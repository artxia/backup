""" PagerMaid features that uses external HTTP APIs other than Telegram. """

from pygoogletranslation import Translator
from os import remove
from magic_google import MagicGoogle
from gtts import gTTS
from gtts.tts import gTTSError
from re import compile as regex_compile
from pagermaid import log
from pagermaid.listener import listener, config
from pagermaid.utils import clear_emojis, attach_log, fetch_youtube_audio, lang, alias_command


@listener(is_plugin=False, outgoing=True, command=alias_command('translate'),
          description=lang('translate_des'),
          parameters=lang('translate_parameters'))
async def translate(context):
    """ PagerMaid universal translator. """
    translator = Translator()
    reply = await context.get_reply_message()
    message = context.arguments
    ap_lang = config['application_language']
    if message:
        pass
    elif reply:
        message = reply.text
    else:
        await context.edit(lang('arg_error'))
        return

    try:
        await context.edit(lang('translate_processing'))
        try:
            result = translator.translate(clear_emojis(message), dest=ap_lang)
        except:
            from translate import Translator as trans
            result = trans(to_lang=ap_lang.replace('zh-cn', 'zh')).translate(clear_emojis(message))
    except ValueError:
        await context.edit(lang('translate_ValueError'))
        return
    try:
        source_lang = result.src
        source_text = result.origin
        trans_lang = result.dest
    except AttributeError:
        await context.edit(lang('google_connection_error'))
        return
    result = f"**{lang('translate_hits')}**\n{lang('translate_original_lang')}: {source_lang}\n{source_text} -> {result.text}"

    if len(result) > 4096:
        await context.edit(lang('translate_tg_limit_uploading_file'))
        await attach_log(result, context.chat_id, "translation.txt", context.id)
        return
    await context.edit(result)
    if len(result) <= 4096:
        await log(f"{lang('translate_get')}: `{source_text}` \n{lang('translate_from')} {source_lang} {lang('translate_to')} {trans_lang}")
    else:
        await log(f"{lang('translate_get')}{translate('translate_from')} {source_lang} {lang('translate_to')} {trans_lang}.")


@listener(is_plugin=False, outgoing=True, command=alias_command('tts'),
          description=lang('tts_des'),
          parameters="<string>")
async def tts(context):
    """ Send TTS stuff as voice message. """
    reply = await context.get_reply_message()
    message = context.arguments
    ap_lang = config['application_tts']
    if message:
        pass
    elif reply:
        message = reply.text
    else:
        await context.edit(lang('arg_error'))
        return

    try:
        await context.edit(lang('tts_processing'))
        gTTS(message, lang=ap_lang)
    except AssertionError:
        await context.edit(lang('tts_AssertionError'))
        return
    except ValueError:
        await context.edit(lang('tts_ValueError'))
        return
    except RuntimeError:
        await context.edit(lang('tts_RuntimeError'))
        return
    google_tts = gTTS(message, lang=ap_lang)
    try:
        google_tts.save("vocals.mp3")
    except AssertionError:
        await context.edit(lang('tts_AssertionError'))
        return
    except ConnectionError:
        await context.edit(lang('tts_RuntimeError'))
        return
    except gTTSError:
        await context.edit(lang('tts_RuntimeError'))
        return
    with open("vocals.mp3", "rb") as audio:
        line_list = list(audio)
        line_count = len(line_list)
    if line_count == 1:
        google_tts = gTTS(message, lang=ap_lang)
        google_tts.save("vocals.mp3")
    with open("vocals.mp3", "r"):
        try:
            await context.client.send_file(context.chat_id, "vocals.mp3", voice_note=True)
            remove("vocals.mp3")
        except:
            pass
        if len(message) <= 4096:
            await log(f"{lang('tts_success')}: `{message}`.")
        else:
            await log(lang('tts_success'))
        await context.delete()


@listener(is_plugin=False, outgoing=True, command=alias_command('google'),
          description=lang('google_des'),
          parameters="<query>")
async def googletest(context):
    """ Searches Google for a string. """
    mg = MagicGoogle()
    reply = await context.get_reply_message()
    query = context.arguments
    if query:
        pass
    elif reply:
        query = reply.text
    else:
        await context.edit(lang('arg_error'))
        return

    query = query.replace(' ', '+')
    await context.edit(lang('google_processing'))
    results = ""
    for i in mg.search(query=query, num=int(config['result_length'])):
        try:
            title = i['text'][0:30] + '...'
            link = i['url']
            results += f"\n[{title}]({link}) \n"
        except:
            await context.edit(lang('google_connection_error'))
            return
    await context.edit(f"**Google** |`{query}`| 🎙 🔍 \n"
                       f"{results}",
                       link_preview=False)
    await log(f"{lang('google_success')} `{query}`")


@listener(is_plugin=False, outgoing=True, command=alias_command('fetchaudio'),
          description=lang('fetchaudio_des'),
          parameters="<url>,<string>")
async def fetchaudio(context):
    if context.arguments:
        if ',' in context.arguments:
            url, string_2 = context.arguments.split(',', 1)
        else:
            url = context.arguments
            string_2 = "#audio "
    else:
        await context.edit(lang('fetchaudio_error_grammer'))
        return
    """ Fetches audio from provided URL. """
    reply = await context.get_reply_message()
    reply_id = None
    await context.edit(lang('fetchaudio_processing'))
    if reply:
        reply_id = reply.id
    if url is None:
        await context.edit(lang('arg_error'))
        return
    youtube_pattern = regex_compile(r"^(http(s)?://)?((w){3}.)?youtu(be|.be)?(\.com)?/.+")
    if youtube_pattern.match(url):
        if not await fetch_youtube_audio(url, context.chat_id, reply_id, string_2):
            await context.edit(lang('fetchaudio_error_downloading'))
        await log(f"{lang('fetchaudio_success')}, {lang('fetchaudio_link')}: {url}.")
        await context.delete()
