""" PagerMaid module to handle sticker collection. """

import certifi
import ssl
from asyncio import sleep
from os import remove
from urllib import request
from io import BytesIO
from telethon.tl.types import DocumentAttributeFilename, MessageMediaPhoto
from telethon.errors.common import AlreadyInConversationError
from PIL import Image, ImageOps
from math import floor
from pagermaid import bot, redis, redis_status
from pagermaid.listener import listener
from pagermaid.utils import lang
from pagermaid import log


@listener(is_plugin=False, outgoing=True, command="s",
          description=lang('sticker_des'),
          parameters="<emoji>")
async def sticker(context):
    """ Fetches images/stickers and add them to your pack. """
    pic_round = False
    is_batch = False
    package_name = ""
    if redis_status():
        if redis.get("sticker.round"):
            pic_round = True

        if len(context.parameter) >= 1:
            # s merge
            await log(f"{context.parameter}")
            if context.parameter[0] == "merge" or context.parameter[0] == "m":
                is_batch = True
                # s merge png <package_name> <number>
                try:
                    if context.parameter[3].isnumeric():
                        if "png" in context.parameter[1]:
                            pic_round = False
                        else:
                            pic_round = True
                        package_name = context.parameter[2]
                except:
                    # 异常，多半是数组越界，不处理，继续参数校验
                    pass
                try:
                    # s merge <package_name> <number>
                    if context.parameter[2].isnumeric():
                        if "png" in context.parameter[1]:
                            pic_round = False
                            package_name = context.parameter[2]
                        else:
                            package_name = context.parameter[1]
                    # s merge png <package_name>
                    elif "png" in context.parameter[1]:
                        pic_round = False
                        package_name = context.parameter[2]
                    # s merge <package_name> <number>
                    else:
                        package_name = context.parameter[1]

                except:
                    # 异常，多半是数组越界
                    # s merge <package_name>
                    try:
                        if "png" in context.parameter[1]:
                            raise Exception()
                        package_name = context.parameter[1]
                    except:
                        # 命令错误
                        try:
                            await context.edit(lang('merge_command_error'))
                        except:
                            pass
                        return

            # s <png | number> | error
            else:
                if context.parameter[0] == "set_round":
                    if pic_round:
                        redis.delete("sticker.round")
                        try:
                            await context.edit(lang('us_change_rounding_false'))
                        except:
                            pass
                    else:
                        redis.set("sticker.round", "true")
                        try:
                            await context.edit(lang('us_change_rounding_true'))
                        except:
                            pass
                    return
                elif "png" in context.parameter[0]:
                    pic_round = False
                    # s <number>
                elif context.parameter[0].isnumeric():
                    pass
                elif isEmoji(context.parameter[0]) or len(context.parameter[0]) == 1:
                    await log(f"emoji：{context.parameter[0]}")
                    pass
                else:
                    try:
                        await context.edit(lang('merge_command_error'))
                    except:
                        pass
                    return

    user = await bot.get_me()
    if not user.username:
        user.username = user.first_name

    custom_emoji = False
    animated = False
    emoji = ""

    if is_batch:
        # 多张
        """ merge every single sticker after the message you replied to. """
        if not context.reply_to_msg_id:
            await context.edit(lang('not_reply'))
            return
        input_chat = await context.get_input_chat()
        count = 0
        scount = 0
        result = ""
        if context.parameter[0] == "m":
            message = await context.get_reply_message()
            await single_sticker(animated, context, custom_emoji, emoji, message, pic_round, user,
                                 package_name)
        else:
            async for message in context.client.iter_messages(input_chat, min_id=context.reply_to_msg_id):
                count += 1
                if message and message.media:
                    scount += 1
                    try:
                        await log(f"{lang('merge_processing_left')}{count}{lang('merge_processing_right')}")
                        await context.edit(f"{lang('merge_processing_left')}{count}{lang('merge_processing_right')}")
                    except:
                        pass
                    result = await single_sticker(animated, context, custom_emoji, emoji, message, pic_round, user,
                                                  package_name)
                    await sleep(.5)
            try:
                await context.edit(f"{result}\n"
                                   f"{lang('merge_total_processed_left')}{scount}{lang('merge_total_processed_right')}", parse_mode='md')
            except:
                pass
        await sleep(5)
        try:
            await context.delete()
        except:
            pass
    else:
        # 单张收集图片
        message = await context.get_reply_message()
        await single_sticker(animated, context, custom_emoji, emoji, message, pic_round, user, "")


async def single_sticker(animated, context, custom_emoji, emoji, message, pic_round, user, package_name):
    try:
        await context.edit(lang('sticker_processing'))
    except:
        pass
    if message and message.media:
        if isinstance(message.media, MessageMediaPhoto):
            photo = BytesIO()
            photo = await bot.download_media(message.photo, photo)
        elif "image" in message.media.document.mime_type.split('/'):
            photo = BytesIO()
            try:
                await context.edit(lang('sticker_downloading'))
            except:
                pass
            await bot.download_file(message.media.document, photo)
            if (DocumentAttributeFilename(file_name='sticker.webp') in
                    message.media.document.attributes):
                emoji = message.media.document.attributes[1].alt
                custom_emoji = True
        elif (DocumentAttributeFilename(file_name='AnimatedSticker.tgs') in
              message.media.document.attributes):
            photo = BytesIO()
            await bot.download_file(message.media.document, "AnimatedSticker.tgs")
            for index in range(len(message.media.document.attributes)):
                try:
                    emoji = message.media.document.attributes[index].alt
                    break
                except:
                    pass
            custom_emoji = True
            animated = True
            photo = 1
        else:
            try:
                await context.edit(lang('sticker_type_not_support'))
            except:
                pass
            return
    else:
        try:
            await context.edit(lang('sticker_reply_not_sticker'))
        except:
            pass
        return

    if photo:
        split_strings = context.text.split()
        if not custom_emoji:
            emoji = "👀"
        pack = 1
        sticker_already = False
        if package_name:
            # 批量处理贴纸无法指定emoji，只获取第几个pack
            # s merge png <package_name> <number>
            if len(split_strings) == 5:
                pack = split_strings[4]
            # s merge <package_name> <number>
            elif len(split_strings) == 4:
                pack = split_strings[3]
        else:
            if len(split_strings) == 3:
                # s png <number|emoji>
                pack = split_strings[2]
                if split_strings[1].replace("png", "") != "":
                    emoji = split_strings[1].replace("png", "")
            elif len(split_strings) == 2:
                # s <number|emoji>
                if split_strings[1].isnumeric():
                    pack = int(split_strings[1])
                else:
                    if split_strings[1].replace("png", "") != "":
                        emoji = split_strings[1].replace("png", "")

        if not isinstance(pack, int):
            pack = 1

        if package_name:
            # merge指定package_name
            pack_name = f"{user.username}_{package_name}_{pack}"
            pack_title = f"@{user.username} {lang('sticker_pack_title')} ({package_name}) ({pack})"
        else:
            pack_name = f"{user.username}_{pack}"
            pack_title = f"@{user.username} {lang('sticker_pack_title')} ({pack})"
        command = '/newpack'
        file = BytesIO()

        if not animated:
            try:
                await context.edit(lang('sticker_resizing'))
            except:
                pass
            image = await resize_image(photo)
            if pic_round:
                try:
                    await context.edit(lang('us_static_rounding'))
                except:
                    pass
                image = await rounded_image(image)
            file.name = "sticker.png"
            image.save(file, "PNG")
        else:
            pack_name += "_animated"
            pack_title += " (animated)"
            command = '/newanimated'

        try:
            response = request.urlopen(
                request.Request(f'http://t.me/addstickers/{pack_name}'),
                context=ssl.create_default_context(cafile=certifi.where()))
        except UnicodeEncodeError:
            pack_name = 's' + hex(context.sender.id)[2:]
            if animated:
                pack_name = 's' + hex(context.sender.id)[2:] + '_animated'
            response = request.urlopen(
                request.Request(f'http://t.me/addstickers/{pack_name}'),
                context=ssl.create_default_context(cafile=certifi.where()))
        if not response.status == 200:
            try:
                await context.edit(lang('sticker_telegram_server_error'))
            except:
                pass
            return
        http_response = response.read().decode("utf8").split('\n')

        if "  A <strong>Telegram</strong> user has created the <strong>Sticker&nbsp;Set</strong>." not in \
                http_response:
            for _ in range(20):  # 最多重试20次
                try:
                    async with bot.conversation('Stickers') as conversation:
                        await conversation.send_message('/addsticker')
                        await conversation.get_response()
                        await bot.send_read_acknowledge(conversation.chat_id)
                        await conversation.send_message(pack_name)
                        chat_response = await conversation.get_response()
                        while chat_response.text == "Whoa! That's probably enough stickers for one pack, give it a break. \
A pack can't have more than 120 stickers at the moment.":
                            pack += 1

                            if package_name:
                                # merge指定package_name
                                pack_name = f"{user.username}_{package_name}_{pack}"
                                pack_title = f"@{user.username} {lang('sticker_pack_title')} ({package_name}) ({pack})"
                            else:
                                pack_name = f"{user.username}_{pack}"
                                pack_title = f"@{user.username} {lang('sticker_pack_title')} ({pack})"
                            try:
                                if package_name:
                                    await context.edit(
                                        lang('sticker_change_pack_to') + str(package_name) + str(pack) + lang(
                                            'sticker_last_is_full'))
                                else:
                                    await context.edit(
                                        lang('sticker_change_pack_to') + str(pack) + lang('sticker_last_is_full'))
                            except:
                                pass
                            await conversation.send_message(pack_name)
                            chat_response = await conversation.get_response()
                            if chat_response.text == "Invalid pack selected.":
                                await add_sticker(conversation, command, pack_title, pack_name, animated, message,
                                                  context, file, emoji)
                                try:
                                    await context.edit(
                                        f"{lang('sticker_has_been_added')} [{lang('sticker_this')}](t.me/addstickers/{pack_name}) {lang('sticker_pack')}",
                                        parse_mode='md')
                                except:
                                    pass
                                return
                        await upload_sticker(animated, message, context, file, conversation)
                        await conversation.get_response()
                        await conversation.send_message(emoji)
                        await bot.send_read_acknowledge(conversation.chat_id)
                        await conversation.get_response()
                        await conversation.send_message('/done')
                        await conversation.get_response()
                        await bot.send_read_acknowledge(conversation.chat_id)
                        break
                except AlreadyInConversationError:
                    if not sticker_already:
                        try:
                            await context.edit(lang('sticker_another_running'))
                        except:
                            pass
                        sticker_already = True
                    else:
                        pass
                    await sleep(.5)
                except Exception:
                    raise
        else:
            try:
                await context.edit(lang('sticker_no_pack_exist_creating'))
            except:
                pass
            async with bot.conversation('Stickers') as conversation:
                await add_sticker(conversation, command, pack_title, pack_name, animated, message,
                                  context, file, emoji)

        try:
            await context.edit(
                f"{lang('sticker_has_been_added')} [{lang('sticker_this')}](t.me/addstickers/{pack_name}) {lang('sticker_pack')}",
                parse_mode='md')
        except:
            pass
        if package_name:
            return f"{lang('sticker_has_been_added')} [{lang('sticker_this')}](t.me/addstickers/{pack_name}) {lang('sticker_pack')}"
        else:
            await sleep(5)
            try:
                await context.delete()
            except:
                pass


async def add_sticker(conversation, command, pack_title, pack_name, animated, message, context, file, emoji):
    await conversation.send_message(command)
    await conversation.get_response()
    await bot.send_read_acknowledge(conversation.chat_id)
    await conversation.send_message(pack_title)
    await conversation.get_response()
    await bot.send_read_acknowledge(conversation.chat_id)
    await upload_sticker(animated, message, context, file, conversation)
    await conversation.get_response()
    await conversation.send_message(emoji)
    await bot.send_read_acknowledge(conversation.chat_id)
    await conversation.get_response()
    await conversation.send_message("/publish")
    if animated:
        await conversation.get_response()
        await conversation.send_message(f"<{pack_title}>")
    await conversation.get_response()
    await bot.send_read_acknowledge(conversation.chat_id)
    await conversation.send_message("/skip")
    await bot.send_read_acknowledge(conversation.chat_id)
    await conversation.get_response()
    await conversation.send_message(pack_name)
    await bot.send_read_acknowledge(conversation.chat_id)
    await conversation.get_response()
    await bot.send_read_acknowledge(conversation.chat_id)


async def upload_sticker(animated, message, context, file, conversation):
    if animated:
        try:
            await context.edit(lang('us_animated_uploading'))
        except:
            pass
        await conversation.send_file("AnimatedSticker.tgs", force_document=True)
        remove("AnimatedSticker.tgs")
    else:
        file.seek(0)
        try:
            await context.edit(lang('us_static_uploading'))
        except:
            pass
        await conversation.send_file(file, force_document=True)


async def resize_image(photo):
    image = Image.open(photo)
    maxsize = (512, 512)
    if (image.width and image.height) < 512:
        size1 = image.width
        size2 = image.height
        if image.width > image.height:
            scale = 512 / size1
            size1new = 512
            size2new = size2 * scale
        else:
            scale = 512 / size2
            size1new = size1 * scale
            size2new = 512
        size1new = floor(size1new)
        size2new = floor(size2new)
        size_new = (size1new, size2new)
        image = image.resize(size_new)
    else:
        image.thumbnail(maxsize)

    return image


async def rounded_image(image):
    w = image.width
    h = image.height
    resize_size = 0
    # 比较长宽
    if w > h:
        resize_size = h
    else:
        resize_size = w
    half_size = floor(resize_size / 2)

    # 获取圆角模版，切割成4个角
    tl = (0, 0, 256, 256)
    tr = (256, 0, 512, 256)
    bl = (0, 256, 256, 512)
    br = (256, 256, 512, 512)
    border = Image.open('pagermaid/static/images/rounded.png').convert('L')
    tlp = border.crop(tl)
    trp = border.crop(tr)
    blp = border.crop(bl)
    brp = border.crop(br)

    # 缩放四个圆角
    tlp = tlp.resize((half_size, half_size))
    trp = trp.resize((half_size, half_size))
    blp = blp.resize((half_size, half_size))
    brp = brp.resize((half_size, half_size))

    # 扩展四个角大小到目标图大小
    # tlp = ImageOps.expand(tlp, (0, 0, w - tlp.width, h - tlp.height))
    # trp = ImageOps.expand(trp, (w - trp.width, 0, 0, h - trp.height))
    # blp = ImageOps.expand(blp, (0, h - blp.height, w - blp.width, 0))
    # brp = ImageOps.expand(brp, (w - brp.width, h - brp.height, 0, 0))

    # 四个角合并到一张新图上
    ni = Image.new('RGB', (w, h), (0, 0, 0)).convert('L')
    ni.paste(tlp, (0, 0))
    ni.paste(trp, (w - trp.width, 0))
    ni.paste(blp, (0, h - blp.height))
    ni.paste(brp, (w - brp.width, h - brp.height))

    # 合并圆角和原图
    image.putalpha(ImageOps.invert(ni))

    return image


def isEmoji(content):
    if not content:
        return False
    if u"\U0001F600" <= content <= u"\U0001F64F":
        return True
    elif u"\U0001F300" <= content <= u"\U0001F5FF":
        return True
    elif u"\U0001F680" <= content <= u"\U0001F6FF":
        return True
    elif u"\U0001F1E0" <= content <= u"\U0001F1FF":
        return True
    else:
        return False
