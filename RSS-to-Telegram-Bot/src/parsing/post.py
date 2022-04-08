from __future__ import annotations
from typing import Optional

from .. import db, env
from ..errors_collection import MediaSendFailErrors
from .utils import parse_entry, logger, Enclosure
from .post_formatter import PostFormatter
from .message import MessageDispatcher


def get_post_from_entry(entry, feed_title: str, feed_link: str = None) -> 'Post':
    entry_parsed = parse_entry(entry)
    return Post(entry_parsed.content, entry_parsed.title, feed_title, entry_parsed.link, entry_parsed.author,
                feed_link=feed_link, enclosures=entry_parsed.enclosures)


class Post:
    def __init__(self,
                 html: str,
                 title: Optional[str] = None,
                 feed_title: Optional[str] = None,
                 link: Optional[str] = None,
                 author: Optional[str] = None,
                 feed_link: Optional[str] = None,
                 enclosures: list[Enclosure] = None):
        """
        :param html: HTML content
        :param title: post title
        :param feed_title: feed title
        :param link: post link
        :param author: post author
        :param feed_link: the url of the feed where the post from
        """
        self.html = html
        self.title = title
        self.feed_title = feed_title
        self.link = link
        self.author = author
        self.feed_link = feed_link
        self.enclosures = enclosures

        self.post_formatter = PostFormatter(html=self.html,
                                            title=self.title,
                                            feed_title=self.feed_title,
                                            link=self.link,
                                            author=self.author,
                                            feed_link=self.feed_link,
                                            enclosures=self.enclosures)

    async def send_formatted_post_according_to_sub(self, sub: db.Sub):
        if not isinstance(sub.feed, db.User):
            await sub.fetch_related('user')
        user: db.User = sub.user
        await self.send_formatted_post(
            user_id=sub.user_id,
            sub_title=sub.title,
            tags=sub.tags.split(' ') if sub.tags else [],
            send_mode=sub.send_mode if sub.send_mode != -100 else user.send_mode,
            length_limit=sub.length_limit if sub.length_limit != -100 else user.length_limit,
            link_preview=sub.link_preview if sub.link_preview != -100 else user.link_preview,
            display_author=sub.display_author if sub.display_author != -100 else user.display_author,
            display_via=sub.display_via if sub.display_via != -100 else user.display_via,
            display_title=sub.display_title if sub.display_title != -100 else user.display_title,
            style=sub.style if sub.style != -100 else user.style,
            display_media=sub.display_media if sub.display_media != -100 else user.display_media,
            silent=not (sub.notify if sub.notify != -100 else user.notify)
        )

    async def send_formatted_post(self,
                                  user_id: int,
                                  sub_title: Optional[str] = None,
                                  tags: Optional[list[str]] = None,
                                  send_mode: int = 0,
                                  length_limit: int = 0,
                                  link_preview: int = 0,
                                  display_author: int = 0,
                                  display_via: int = 0,
                                  display_title: int = 0,
                                  style: int = 0,
                                  display_media: int = 0,
                                  silent: bool = False):
        """
        Send formatted post.

        :param user_id: user id
        :param sub_title: Sub title, overriding feed title if set
        :param tags: Tags of the sub
        :param send_mode: -1=force link, 0=auto, 1=force Telegraph, 2=force message
        :param length_limit: Telegraph length limit, valid when send_mode==0. If exceeded, send via Telegraph; If is 0,
            send via Telegraph when a post cannot be sent in a single message
        :param link_preview: 0=auto, 1=force enable
        :param display_author: -1=disable, 0=auto, 1=force display
        :param display_via: -2=completely disable, -1=disable but display link, 0=auto, 1=force display
        :param display_title: -1=disable, 0=auto, 1=force display
        :param style: 0=RSStT, 1=flowerss
        :param display_media: -1=disable, 0=enable
        :param silent: whether to send with notification sound
        """
        for tries in range(3):
            if not self.post_formatter.parsed:
                await self.post_formatter.parse_html()

            formatted_post, need_media, need_link_preview = \
                await self.post_formatter.get_formatted_post(sub_title=sub_title,
                                                             tags=tags,
                                                             send_mode=send_mode,
                                                             length_limit=length_limit,
                                                             link_preview=link_preview,
                                                             display_author=display_author,
                                                             display_via=display_via,
                                                             display_title=display_title,
                                                             style=style,
                                                             display_media=display_media)

            message_dispatcher = MessageDispatcher(user_id=user_id,
                                                   html=formatted_post,
                                                   media=self.post_formatter.media if need_media else None,
                                                   link_preview=need_link_preview,
                                                   silent=silent)
            try:
                return await message_dispatcher.send_messages()
            except MediaSendFailErrors as e:
                media = self.post_formatter.media
                log_header = f'Failed to send post to user {user_id} (feed: {self.feed_link}, post: {self.link}) ' \
                             f'due to {type(e).__name__}'
                msg_count_prev = await media.estimate_message_counts()
                if media.allow_mixing_images_and_videos:
                    media.allow_mixing_images_and_videos = False
                    msg_count_new = await media.estimate_message_counts()
                    if msg_count_new != msg_count_prev:
                        # the videos may not be able to mixed with images split them and try again
                        logger.debug(log_header + ', disallowed mixing images and videos and retrying')
                        continue
                if not media.consider_videos_as_gifs:
                    media.consider_videos_as_gifs = True
                    msg_count_new = await media.estimate_message_counts()
                    if msg_count_new != msg_count_prev:
                        logger.debug(log_header + ', let each video occupy a single message and retrying')
                        continue
                if media.allow_files_sent_as_album:
                    media.allow_files_sent_as_album = False
                    msg_count_new = await media.estimate_message_counts()
                    if msg_count_new != msg_count_prev:
                        logger.debug(log_header + ', disallowed files sent as album and retrying')
                        continue
                logger.error(log_header + f', dropped all media and retrying...')
                self.post_formatter.media.invalidate_all()
                continue

    async def test_format(self, user_id: int):
        if user_id != env.MANAGER:
            return
        sub = await db.Sub.filter(feed__link=self.feed_link, user_id=user_id).get_or_none()
        if sub is None:
            user = await db.User.get_or_none(id=user_id)
            if user is None:
                return await self.send_formatted_post(user_id=user_id)
            return await self.send_formatted_post(
                user_id=user_id,
                send_mode=user.send_mode,
                length_limit=user.length_limit,
                link_preview=user.link_preview,
                display_author=user.display_author,
                display_via=user.display_via,
                display_title=user.display_title,
                style=user.style,
                display_media=user.display_media,
                silent=not user.notify
            )
        return await self.send_formatted_post_according_to_sub(sub=sub)
