from __future__ import annotations
from typing import Optional, Union
from typing_extensions import Final
from abc import ABC, abstractmethod
from collections.abc import Callable, Awaitable

import asyncio
import re
from io import BytesIO
from collections import defaultdict
from telethon.tl.functions.messages import UploadMediaRequest
from telethon.tl.types import InputMediaPhotoExternal, InputMediaDocumentExternal, \
    MessageMediaPhoto, MessageMediaDocument, InputFile, InputFileBig, InputMediaUploadedPhoto
from telethon.errors import FloodWaitError, SlowModeWaitError, ServerError, BadRequestError
from urllib.parse import urlencode

from .. import env, log, web, locks
from .html_node import Code, Link, Br, Text, HtmlTree
from .utils import isAbsoluteHttpLink
from ..errors_collection import InvalidMediaErrors, ExternalMediaFetchFailedErrors, UserBlockedErrors

logger = log.getLogger('RSStT.medium')

sinaimg_sizes: Final = ('large', 'mw2048', 'mw1024', 'mw720', 'middle')
sinaimg_size_parser: Final = re.compile(r'(?P<domain>^https?://wx\d\.sinaimg\.\w+/)'
                                        r'(?P<size>\w+)'
                                        r'(?P<filename>/\w+\.\w+$)').match
pixiv_sizes: Final = ('original', 'master')
pixiv_size_parser: Final = re.compile(r'(?P<url_prefix>^https?://i\.pixiv\.(cat|re)/img-)'
                                      r'(?P<size>\w+)'
                                      r'(?P<url_infix>/img/\d{4}/(\d{2}/){5})'
                                      r'(?P<filename>\d+_p\d+)'
                                      r'(?P<file_ext>\.\w+$)').match
sinaimg_server_parser: Final = re.compile(r'(?P<url_prefix>^https?://wx)'
                                          r'(?P<server_id>\d)'
                                          r'(?P<url_suffix>\.sinaimg\.\S+$)').match
# lizhi_sizes: Final = ('ud.mp3', 'hd.mp3', 'sd.m4a')  # ud.mp3 is rare
lizhi_sizes: Final = ('hd.mp3', 'sd.m4a')
lizhi_server_id: Final = ('1', '2', '5', '')
lizhi_parser: Final = re.compile(r'(?P<url_prefix>^https?://cdn)'
                                 r'(?P<server_id>[125]?)'
                                 r'(?P<url_infix>\.lizhi\.fm/[\w/]+)'
                                 r'(?P<size_suffix>([uh]d\.mp3|sd\.m4a)$)').match
isTelegramCannotFetch: Final = re.compile(r'^https?://(\w+\.)?telesco\.pe').match

IMAGE: Final = 'image'
VIDEO: Final = 'video'
ANIMATION: Final = 'animation'
AUDIO: Final = 'audio'
FILE: Final = 'file'
MEDIUM_BASE_CLASS: Final = 'medium'
TypeMedium = Union[IMAGE, VIDEO, AUDIO, ANIMATION, FILE]

MEDIA_GROUP: Final = 'media_group'
TypeMessage = Union[MEDIA_GROUP, TypeMedium]

TypeMessageMedia = Union[MessageMediaPhoto, MessageMediaDocument, InputMediaUploadedPhoto]
TypeInputFile = Union[InputFile, InputFileBig]
TypeTelegramMedia = Union[TypeMessageMedia, TypeInputFile]

IMAGE_MAX_SIZE: Final = 5242880
MEDIA_MAX_SIZE: Final = 20971520


# Note:
# One message can have 10 media at most, but there are some exceptions.
# 1. A GIF (Animation) and webp (although as a file) must occupy a SINGLE message.
# 2. Videos and Images can be mixed in a media group, but any other type of media cannot be in the same message.
# 3. Images uploaded as MessageMediaPhoto will be considered as an image. While MessageMediaDocument not, it's a file.
# 4. Any other type of media except Image must be uploaded as MessageMediaDocument.
# 5. Telegram will not take notice of attributes provided if it already decoded the necessary metadata of a media.
# 6. Because of (5), we can't force send GIFs and videos as ordinary files.
# 7. Audios can be sent in a media group, but can not be mixed with other types of media.
# 8. Other files (including images sent as files) should be able to be mixed in a media group.
#
# Type fallback notes:
# 1. A video can fall back to an image if its poster is available.
# 2. An image can fall back to a file if it is: 5MB < size <= 20MB, width + height >= 10000.
# 3. A GIF need not any fallback, because of (5) above.
# 4. The only possible fallback chain is: video -> image(poster) -> file.
# 5. If an image fall back to a file, rest images must fall back to file too!

class AbstractMedium(ABC):
    type: str = ''

    def __init__(self):
        self.valid: Optional[bool] = None
        self.drop_silently: bool = False  # if True, will not be included in invalid media
        self.original_urls: tuple[str, ...] = tuple()
        self.type_fallback_medium: Optional[AbstractMedium] = None
        self.need_type_fallback: bool = False
        self.uploaded_bucket: defaultdict[int, Optional[tuple[TypeMessageMedia, TypeMedium]]] \
            = defaultdict(lambda: None)
        self.uploading_lock = asyncio.Lock()
        self.validating_lock = asyncio.Lock()

    @abstractmethod
    def telegramize(self) -> Optional[TypeMessageMedia]:
        pass

    @abstractmethod
    async def validate(self, flush: bool = False) -> bool:
        pass

    @abstractmethod
    async def fallback(self) -> bool:
        pass

    @abstractmethod
    def type_fallback_chain(self) -> Optional[AbstractMedium]:
        pass

    @abstractmethod
    def get_link_html_node(self) -> Optional[Text]:
        pass

    @property
    @abstractmethod
    def hash(self) -> str:
        pass

    @abstractmethod
    async def change_server(self) -> bool:
        pass

    async def upload(self, chat_id: int, force_upload: bool = False) \
            -> tuple[Optional[TypeMessageMedia], Optional[TypeMedium]]:
        if self.valid is None:
            await self.validate()
        medium_to_upload = self.type_fallback_chain()
        if medium_to_upload is None:
            return None, None
        if self.uploaded_bucket[chat_id]:
            cached = self.uploaded_bucket[chat_id]
            if not force_upload and cached[1] == medium_to_upload.type:
                return cached

        tries = 0
        error_tries = 0
        max_tries = 10
        server_change_count = 0
        media_fallback_count = 0
        err_list = []
        flood_lock = locks.user_flood_lock(chat_id)
        while True:
            peer = await env.bot.get_input_entity(chat_id)
            try:
                async with flood_lock:
                    pass  # wait for flood wait

                async with locks.user_media_upload_semaphore(chat_id):
                    async with self.uploading_lock:
                        medium_to_upload = self.type_fallback_chain()
                        if medium_to_upload is None:
                            return None, None
                        if self.uploaded_bucket[chat_id]:
                            cached = self.uploaded_bucket[chat_id]
                            if not force_upload and cached[1] == medium_to_upload.type:
                                return cached
                        while True:
                            medium_to_upload = self.type_fallback_chain()
                            if medium_to_upload is None:
                                return None, None
                            tries += 1
                            if tries > max_tries:
                                self.valid = False
                                return None, None
                            try:
                                async with flood_lock:
                                    pass  # wait for flood wait

                                uploaded_media = await env.bot(
                                    UploadMediaRequest(peer, medium_to_upload.telegramize())
                                )
                                self.uploaded_bucket[chat_id] = uploaded_media, medium_to_upload.type
                                return uploaded_media, medium_to_upload.type

                            # errors caused by invalid img/video(s)
                            except InvalidMediaErrors as e:
                                err_list.append(e)
                                if await self.fallback():
                                    media_fallback_count += 1
                                else:
                                    self.valid = False
                                    return None, None
                                continue

                            # errors caused by server or network instability between img server and telegram server
                            except ExternalMediaFetchFailedErrors as e:
                                err_list.append(e)
                                if await self.change_server():
                                    server_change_count += 1
                                elif await self.fallback():
                                    media_fallback_count += 1
                                else:
                                    self.valid = False
                                    return None, None
                                continue

            except (FloodWaitError, SlowModeWaitError) as e:
                # telethon has retried for us, but we release locks and retry again here to see if it will be better
                if error_tries >= 1:
                    logger.error(f'Medium dropped due to too many flood control retries ({chat_id}): '
                                 f'{self.original_urls[0]}')
                    return None, None

                error_tries += 1
                await locks.user_flood_wait(chat_id, seconds=e.seconds)  # acquire a flood wait
            except ServerError as e:
                # telethon has retried for us, so we just retry once more
                if error_tries >= 1:
                    logger.error(f'Medium dropped due to Telegram internal server error '
                                 f'({chat_id}, {type(e).__name__}): '
                                 f'{self.original_urls[0]}')

                error_tries += 1


class Medium(AbstractMedium):
    type = MEDIUM_BASE_CLASS
    maxSize = MEDIA_MAX_SIZE
    # noinspection PyTypeChecker
    typeFallbackTo: Optional[type[Medium]] = None
    typeFallbackAllowSelfUrls: bool = False
    # noinspection PyTypeChecker
    inputMediaExternalType: Optional[Union[type[InputMediaPhotoExternal], type[InputMediaDocumentExternal]]] = None

    def __init__(self, urls: Union[str, list[str]], type_fallback_urls: Optional[Union[str, list[str]]] = None):
        super().__init__()
        urls = urls if isinstance(urls, list) else [urls]
        self.urls: list[str] = []
        for url in urls:  # dedup, should not use a set because sequence is important
            if url not in self.urls:
                self.urls.append(url)
        self.original_urls: tuple[str, ...] = tuple(self.urls)
        self.chosen_url: Optional[str] = self.urls[0]
        self._server_change_count: int = 0
        self.size = self.width = self.height = None
        self.max_width = self.max_height = -1  # use for long pic judgment
        self.type_fallback_urls: list[str] = type_fallback_urls if isinstance(type_fallback_urls, list) \
            else [type_fallback_urls] if type_fallback_urls and isinstance(type_fallback_urls, str) \
            else []  # use for fallback if not type_fallback_allow_self_urls
        self.content_type: Optional[str] = None

    def telegramize(self) -> Optional[Union[InputMediaPhotoExternal, InputMediaDocumentExternal]]:
        if self.inputMediaExternalType is None:
            raise NotImplementedError
        return self.inputMediaExternalType(self.chosen_url)

    def type_fallback_chain(self) -> Optional[Medium]:
        return (
            self
            if self.valid
            else
            (self.type_fallback_medium.type_fallback_chain()
             if self.need_type_fallback and self.type_fallback_medium is not None
             else None)
        ) if not self.drop_silently else None

    def get_link_html_node(self) -> Text:
        url = self.original_urls[0]
        if isAbsoluteHttpLink(url):
            return Link(self.type, param=self.original_urls[0])
        return Text([Text(f'{self.type} ('), Code(url), Text(')')])

    async def validate(self, flush: bool = False) -> bool:
        if self.valid is not None and not flush:  # already validated
            return self.valid

        if self.drop_silently:
            return False

        async with self.validating_lock:
            while self.urls:
                url = self.urls.pop(0)
                if not isAbsoluteHttpLink(url):  # bypass non-http links
                    continue
                medium_info = await web.get_medium_info(url)
                if medium_info is None:
                    continue
                self.size, self.width, self.height, self.content_type = medium_info
                if self.type == IMAGE and self.size <= self.maxSize and min(self.width, self.height) == -1 \
                        and self.content_type and self.content_type.startswith('image') \
                        and self.content_type.find('webp') == -1 and self.content_type.find('svg') == -1 \
                        and not url.startswith(env.IMAGES_WESERV_NL):
                    # enforcing dimension detection for images
                    self.width, self.height = await detect_image_dimension_via_images_weserv_nl(url)
                self.max_width = max(self.max_width, self.width)
                self.max_height = max(self.max_height, self.height)

                if self.type == IMAGE:
                    # drop icons and emoticons
                    if 0 < self.width <= 30 or 0 < self.height < 30:
                        self.valid = False
                        self.drop_silently = True
                        return False
                    # force convert WEBP/SVG to PNG
                    if (
                            self.content_type
                            and (self.content_type.find('webp') != -1
                                 or self.content_type.startswith('application')
                                 or self.content_type.find('svg') != -1)
                    ):
                        # immediately fall back to 'images.weserv.nl'
                        self.urls = [url for url in self.urls if url.startswith(env.IMAGES_WESERV_NL)]
                        continue
                    # always invalid
                    if self.width + self.height > 10000 or self.size > self.maxSize:
                        self.valid = False
                    # Telegram accepts 0.05 < w/h < 20. But after downsized, it will be ugly. Narrow the range down
                    elif 0.4 <= self.width / self.height <= 2.5:
                        self.valid = True
                    elif (
                            # ensure the image is valid
                            0.05 < self.width / self.height < 20
                            and
                            # Telegram downsizes images to fit 1280x1280. If not downsized a lot, passing
                            0 < max(self.max_width, self.max_height) <= 1280 * 1.5
                    ):
                        self.valid = True
                    # let long images fall back to file
                    else:
                        self.valid = False
                        self.urls = []  # clear the urls, force fall back to file
                elif self.size <= self.maxSize:  # valid
                    self.valid = True
                else:
                    self.valid = False

                # some images cannot be sent as file directly, if so, images.weserv.nl may help
                if self.type == FILE and self.content_type and self.content_type.startswith('image') \
                        and not url.startswith(env.IMAGES_WESERV_NL):
                    self.urls.append(construct_images_weserv_nl_url_convert_to_jpg(url))

                if self.valid:
                    self.chosen_url = url
                    self._server_change_count = 0
                    if isTelegramCannotFetch(self.chosen_url):
                        await self.change_server()
                    return True

            self.valid = False
            return await self.type_fallback()

    async def type_fallback(self) -> bool:
        fallback_urls = self.type_fallback_urls + (list(self.original_urls) if self.typeFallbackAllowSelfUrls else [])
        self.valid = False
        if self.type_fallback_medium is None and fallback_urls and self.typeFallbackTo:
            # create type fallback medium
            self.type_fallback_medium = self.typeFallbackTo(fallback_urls)
            if await self.type_fallback_medium.validate():
                logger.debug(f"Medium {self.original_urls[0]}"
                             + (f' ({self.info})' if self.info else '')
                             + f" type fallback to '{self.type_fallback_medium.type}'"
                             + (f'({self.type_fallback_medium.original_urls[0]})'
                                if not self.typeFallbackAllowSelfUrls
                                else ''))
                self.need_type_fallback = True
                # self.type_fallback_medium.type = self.type
                # self.type_fallback_medium.original_urls = self.original_urls
                return True
        elif self.need_type_fallback and self.type_fallback_medium is not None:
            return await self.type_fallback_medium.fallback()
        logger.debug(f'Dropped medium {self.original_urls[0]}'
                     + (f' ({self.info})' if self.info else '')
                     + ': invalid or fetch failed')
        return False

    async def fallback(self) -> bool:
        if self.need_type_fallback:
            if not await self.type_fallback_medium.fallback():
                self.need_type_fallback = False
                self.valid = False
            return True
        urls_len = len(self.urls)
        formerly_valid = self.valid
        if formerly_valid:
            await self.validate(flush=True)
        return (self.valid != formerly_valid
                or (self.valid and urls_len != len(self.urls))
                or self.need_type_fallback)

    async def change_server(self) -> bool:
        if self._server_change_count >= 1:
            return False
        self._server_change_count += 1
        self.chosen_url = env.IMG_RELAY_SERVER + self.chosen_url
        # noinspection PyBroadException
        try:
            await web.get(url=self.chosen_url, semaphore=False, max_size=0)  # let the img relay sever cache the img
        except Exception:
            pass
        return True

    def __bool__(self):
        if self.valid is None:
            raise RuntimeError('You must validate a medium before judging its validation')
        return self.valid

    def __eq__(self, other):
        return type(self) == type(other) and self.original_urls == other.original_urls

    @property
    def hash(self) -> str:
        if self.drop_silently:
            return ''
        return '|'.join(
            str(s) for s in (self.valid,
                             self.chosen_url,
                             self.need_type_fallback,
                             self.type_fallback_medium.hash if self.need_type_fallback else None)
        )

    @property
    def info(self):
        return (
                (f'{self.size / 1024 / 1024:.2f}MB'
                 if self.size not in {-1, None}
                 else '')
                + (', '
                   if (self.size not in {-1, None} and (self.width not in {-1, None} or self.height not in {-1, None}))
                   else '')
                + (f'{self.width}x{self.height}'
                   if self.width not in {-1, None} and self.height not in {-1, None}
                   else '')
        )


class File(Medium):
    type = FILE
    maxSize = MEDIA_MAX_SIZE
    typeFallbackTo = None
    typeFallbackAllowSelfUrls = False
    inputMediaExternalType = InputMediaDocumentExternal


class Image(Medium):
    type = IMAGE
    maxSize = IMAGE_MAX_SIZE
    typeFallbackTo = File
    typeFallbackAllowSelfUrls = True
    inputMediaExternalType = InputMediaPhotoExternal

    def __init__(self, urls: Union[str, list[str]]):
        super().__init__(urls)
        new_urls = []
        for url in self.urls:
            sinaimg_match = sinaimg_size_parser(url)
            pixiv_match = pixiv_size_parser(url)
            if not any([sinaimg_match, pixiv_match]):
                new_urls.append(url)
                continue
            if sinaimg_match:
                parsed_sinaimg = sinaimg_match.groupdict()  # is a sinaimg img
                for size_name in sinaimg_sizes:
                    new_url = parsed_sinaimg['domain'] + size_name + parsed_sinaimg['filename']
                    if new_url not in new_urls:
                        new_urls.append(new_url)
            elif pixiv_match:
                parsed_pixiv = pixiv_match.groupdict()  # is a pixiv img
                for size_name in pixiv_sizes:
                    new_url = parsed_pixiv['url_prefix'] + size_name + parsed_pixiv['url_infix'] \
                              + parsed_pixiv['filename'] \
                              + ('_master1200.jpg' if size_name == 'master' else parsed_pixiv['file_ext'])
                    if new_url not in new_urls:
                        new_urls.append(new_url)
            if url not in new_urls:
                new_urls.append(url)
        self.urls = new_urls
        urls_not_images_weserv_nl = [url for url in self.urls if not url.startswith(env.IMAGES_WESERV_NL)]
        self.urls.extend(construct_images_weserv_nl_url(urls_not_images_weserv_nl[i])
                         for i in range(min(len(urls_not_images_weserv_nl), 3)))  # use for final fallback

    async def change_server(self) -> bool:
        sinaimg_server_match = sinaimg_server_parser(self.chosen_url)
        if not sinaimg_server_match:  # is not a sinaimg img
            return await super().change_server()

        if self._server_change_count >= 1:
            return False
        self._server_change_count += 1
        parsed = sinaimg_server_match.groupdict()
        new_server_id = int(parsed['server_id']) + 1
        if new_server_id > 4:
            new_server_id = 1
        self.chosen_url = f"{parsed['url_prefix']}{new_server_id}{parsed['url_suffix']}"
        return True


class Video(Medium):
    type = VIDEO
    maxSize = MEDIA_MAX_SIZE
    typeFallbackTo = Image
    typeFallbackAllowSelfUrls = False
    inputMediaExternalType = InputMediaDocumentExternal


class Audio(Medium):
    type = AUDIO
    maxSize = MEDIA_MAX_SIZE
    typeFallbackTo = None
    typeFallbackAllowSelfUrls = False
    inputMediaExternalType = InputMediaDocumentExternal

    def __init__(self, urls: Union[str, list[str]]):
        super().__init__(urls)
        new_urls = []
        for url in self.urls:
            lizhi_match = lizhi_parser(url)
            if not lizhi_match:
                new_urls.append(url)
                continue
            parsed_lizhi = lizhi_match.groupdict()  # is a pixiv img
            for size_suffix in lizhi_sizes:
                new_url = parsed_lizhi['url_prefix'] + parsed_lizhi['server_id'] + parsed_lizhi['url_infix'] \
                          + size_suffix
                if new_url not in new_urls:
                    new_urls.append(new_url)
            if url not in new_urls:
                new_urls.append(url)
        self.urls = new_urls

    async def change_server(self) -> bool:
        lizhi_match = lizhi_parser(self.chosen_url)
        if not lizhi_match:  # is not a lizhi audio
            return await super().change_server()

        if self._server_change_count >= 1:
            return False
        self._server_change_count += 1
        parsed = lizhi_match.groupdict()
        server_id = parsed['server_id']
        new_server_id = lizhi_server_id[lizhi_server_id.index(server_id) - 1] \
            if server_id in lizhi_server_id else lizhi_server_id[0]
        self.chosen_url = f"{parsed['url_prefix']}{new_server_id}{parsed['url_infix']}{parsed['size_suffix']}"
        return True


class Animation(Image):
    type = ANIMATION
    maxSize = MEDIA_MAX_SIZE
    # typeFallbackTo = Image
    # typeFallbackAllowSelfUrls = True
    typeFallbackTo = None
    typeFallbackAllowSelfUrls = False
    inputMediaExternalType = InputMediaDocumentExternal


class UploadedImage(AbstractMedium):
    type: str = IMAGE
    original_urls = ['']

    def __init__(self, file: Union[bytes, BytesIO, Callable, Awaitable]):
        super().__init__()
        self.file = file
        self.uploaded_file: Union[InputFile, InputFileBig, None] = None

    def telegramize(self) -> Optional[InputMediaUploadedPhoto]:
        if self.valid is None:
            raise RuntimeError('Validate() must be called before telegramize()')
        if self.uploaded_file:
            return InputMediaUploadedPhoto(self.uploaded_file)
        return None

    @property
    def hash(self) -> str:
        return str(hash(self.file))

    @property
    def drop_silently(self):
        if self.valid is None:
            return False
        return not self.valid

    @drop_silently.setter
    def drop_silently(self, value):
        if not value and self.valid is None:
            return
        self.valid = not value

    def type_fallback_chain(self) -> Optional[UploadedImage]:
        return self if not self.drop_silently and self.valid else None

    def get_link_html_node(self) -> None:
        return None

    async def fallback(self) -> bool:
        if self.valid:
            self.valid = False
            return True
        return False

    change_server = fallback

    async def validate(self, flush: bool = False):
        if flush and self.valid:
            self.valid = False
            return False
        if not flush and self.valid is not None:
            return self.valid
        async with self.validating_lock:
            if not flush and self.valid is not None:
                return self.valid
            try:
                try:
                    callable_file = self.file
                    if isinstance(self.file, Awaitable):
                        self.file = await callable_file
                    elif isinstance(self.file, Callable):
                        self.file = callable_file()
                except Exception as e:
                    self.valid = False
                    logger.error(f'Failed to generate file for {callable_file.__name__}', exc_info=e)
                if not isinstance(self.file, (bytes, BytesIO)):
                    raise ValueError(f'File must be bytes or BytesIO, got {type(self.file)}')
                if isinstance(self.file, BytesIO):
                    self.file.seek(0)
                self.uploaded_file = await env.bot.upload_file(self.file)
                self.valid = True
            except (BadRequestError, ValueError) as e:
                logger.debug(f'Failed to upload file', exc_info=e)
                self.valid = False
        return self.valid


class Media:
    def __init__(self):
        self._media: list[AbstractMedium] = []
        self.modify_lock = asyncio.Lock()
        self.allow_mixing_images_and_videos: bool = True
        self.consider_videos_as_gifs: bool = False
        self.allow_files_sent_as_album: bool = True

    def add(self, medium: AbstractMedium):
        if medium in self._media:
            return
        self._media.append(medium)

    def url_exists(self, url: str) -> bool:
        return any(url in medium.original_urls for medium in self._media)

    async def fallback_all(self) -> bool:
        if not self._media:
            return False
        fallback_flag = False
        for medium in self._media:
            if not medium.drop_silently and await medium.fallback():
                fallback_flag = True
        return fallback_flag

    def invalidate_all(self) -> bool:
        invalidated_some_flag = False
        for medium in self._media:
            if not medium.drop_silently and medium.valid or medium.need_type_fallback:
                medium.valid = False
                medium.need_type_fallback = False
                invalidated_some_flag = True
        return invalidated_some_flag

    async def validate(self, flush: bool = False):
        if not self._media:
            return
        await asyncio.gather(*(medium.validate(flush=flush) for medium in self._media if not medium.drop_silently))

    async def upload_all(self, chat_id: Optional[int]) \
            -> tuple[
                list[
                    tuple[
                        Union[
                            tuple[
                                Union[
                                    TypeMessageMedia,  # uploaded media
                                    Medium  # origin media (if chat_id is None)
                                ], ...
                            ],  # uploaded media list of the media group
                            Union[
                                TypeMessageMedia,  # uploaded media
                                Medium  # origin media (if chat_id is None)
                            ]
                        ],
                        TypeMessage,  # message type
                    ]
                ],
                Optional[HtmlTree]
            ]:
        """
        Upload all media to telegram.
        :param chat_id: chat_id to upload to. If None, the origin media will be returned.
        :return: ((uploaded/original medium, medium type), invalid media html node)
        """
        await self.validate()

        media_and_types: tuple[
            Union[tuple[Union[TypeMessageMedia, Medium, None], Optional[TypeMedium]], BaseException],
            ...]
        if chat_id:
            # tuple[Union[tuple[Optional[TypeMessageMedia], Optional[TypeMedium]], BaseException], ...]
            media_and_types = await asyncio.gather(
                *(medium.upload(chat_id) for medium in self._media if not medium.drop_silently),
                return_exceptions=True
            )
        else:
            # tuple[tuple[Optional[Medium], Optional[TypeMedium]], ...]
            media_and_types = tuple((medium.type_fallback_chain(), medium.type_fallback_chain().type)
                                    if medium.type_fallback_chain() is not None
                                    else (None, None)
                                    for medium in self._media if not medium.drop_silently)

        media: list[tuple[Union[TypeMessageMedia, Image, Video], Union[IMAGE, VIDEO]]] = []
        images: list[tuple[Union[MessageMediaPhoto, Image], Union[IMAGE]]] = []
        videos: list[tuple[Union[MessageMediaDocument, Video], Union[VIDEO]]] = []
        gifs: list[tuple[Union[MessageMediaDocument, Animation], ANIMATION]] = []
        audios: list[tuple[Union[MessageMediaDocument, Audio], AUDIO]] = []
        files: list[tuple[Union[MessageMediaDocument, File], FILE]] = []

        link_nodes: list[Text] = []
        for medium, medium_and_type in zip(self._media, media_and_types):
            if isinstance(medium_and_type, Exception):
                if type(medium_and_type) in UserBlockedErrors:  # user blocked, let it go
                    raise medium_and_type
                logger.debug('Upload media failed:', exc_info=medium_and_type)
                link_nodes.append(medium.get_link_html_node())
                continue
            file, file_type = medium_and_type
            if file_type == IMAGE:
                media.append(medium_and_type)
                images.append(medium_and_type)
            elif file_type == VIDEO:
                media.append(medium_and_type)
                videos.append(medium_and_type)
            elif file_type == ANIMATION:
                gifs.append(medium_and_type)
            elif file_type == AUDIO:
                audios.append(medium_and_type)
            elif file_type == FILE:
                files.append(medium_and_type)
            else:
                link_nodes.append(medium.get_link_html_node())
            if file_type in {IMAGE, FILE} and isinstance(medium, Video) and file_type != medium.type:
                link_nodes.append(medium.get_link_html_node())

        ret = []
        allow_in_group = (
                ((media,) if self.allow_mixing_images_and_videos and not self.consider_videos_as_gifs else (images,))
                + (tuple() if self.consider_videos_as_gifs or self.allow_mixing_images_and_videos else (videos,))
                + (audios,)
                + ((files,) if self.allow_files_sent_as_album else tuple())
        )
        disallow_in_group = (
                (tuple() if not self.consider_videos_as_gifs else (videos,))
                + (gifs,)
                + (tuple() if self.allow_files_sent_as_album else (files,))
        )
        for list_to_process in allow_in_group:
            while list_to_process:
                _ = list_to_process[:10]
                list_to_process = list_to_process[10:]
                if len(_) == 1:
                    ret.append(_[0])
                else:
                    # media group
                    media_group = tuple(medium_and_type[0] for medium_and_type in _)
                    ret.append((media_group, MEDIA_GROUP))
        for list_to_process in disallow_in_group:
            ret.extend(list_to_process)

        html_nodes = []
        invalid_html_node: Optional[HtmlTree] = None
        for link in link_nodes:
            if not link:
                continue
            html_nodes.append(link)
            html_nodes.append(Br())
        if html_nodes:
            html_nodes.pop()
            html_nodes.insert(0, Text('Invalid media:\n'))
            invalid_html_node = HtmlTree(html_nodes)

        return ret, invalid_html_node

    async def estimate_message_counts(self):
        media = await self.upload_all(chat_id=None)
        return sum(1 for _ in media[0])

    def __len__(self) -> int:
        return sum(1 for medium in self._media if not medium.drop_silently)

    def __bool__(self) -> bool:
        return any(not medium.drop_silently for medium in self._media)

    @property
    def valid_count(self):
        return sum(1 for medium in self._media if medium.valid and not medium.drop_silently)

    @property
    def invalid_count(self):
        return sum(1 for medium in self._media if medium.valid is False and not medium.drop_silently)

    @property
    def pending_count(self):
        return sum(1 for medium in self._media if medium.valid is None and not medium.drop_silently)

    @property
    def need_type_fallback_count(self):
        return sum(1 for medium in self._media if medium.need_type_fallback and medium.type_fallback_medium is not None
                   and not medium.drop_silently)

    def stat(self):
        class MediaStat:
            valid = self.valid_count
            invalid = self.invalid_count
            pending = self.pending_count
            need_type_fallback = self.need_type_fallback_count

            def __eq__(self, other):
                return isinstance(self, other) and self.valid == other.valid and self.invalid == other.invalid \
                       and self.pending == other.pending and self.need_type_fallback == other.need_type_fallback

        return MediaStat()

    @property
    def hash(self):
        return '|'.join(medium.hash for medium in self._media)


def construct_images_weserv_nl_url(url: str,
                                   width: Optional[int] = 2560,
                                   height: Optional[int] = 2560,
                                   fit: Optional[str] = 'inside',
                                   output_format: Optional[str] = 'png',
                                   without_enlargement: Optional[bool] = True,
                                   default_image: Optional[str] = None) -> str:
    params = {
        'url': url,
        'w': width,
        'h': height,
        'fit': fit,
        'output': output_format,
        'we': '1' if without_enlargement else None,
        'default': default_image,
    }
    filtered_params = {k: v for k, v in params.items() if v is not None}
    query_string = urlencode(filtered_params)
    return env.IMAGES_WESERV_NL + '?' + query_string


def construct_images_weserv_nl_url_convert_to_jpg(url: str) -> str:
    return construct_images_weserv_nl_url(url, width=None, height=None, fit=None, without_enlargement=None,
                                          output_format='jpg')


async def detect_image_dimension_via_images_weserv_nl(url: str) -> tuple[int, int]:
    url = construct_images_weserv_nl_url_convert_to_jpg(url)
    res = await web.get_medium_info(url)
    if not res:
        return -1, -1
    _, width, height, _ = res
    return width, height
