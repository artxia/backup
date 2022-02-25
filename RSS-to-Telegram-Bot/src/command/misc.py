from typing import Optional, Union
from telethon import events, types, Button
from telethon.tl.patched import Message
from telethon.errors import RPCError

from src import env, db
from .utils import command_gatekeeper, get_group_migration_help_msg, get_commands_list, set_bot_commands, logger
from src.i18n import i18n, ALL_LANGUAGES
from . import inner


@command_gatekeeper(only_manager=False, ignore_tg_lang=True)
async def cmd_start(event: Union[events.NewMessage.Event, Message], *_, lang=None, **__):
    if lang is None:
        await cmd_lang.__wrapped__(event)
        return
    await cmd_or_callback_help.__wrapped__(event, lang=lang)


@command_gatekeeper(only_manager=False)
async def cmd_lang(event: Union[events.NewMessage.Event, Message], *_, **__):
    msg = '\n'.join(f"{i18n[lang]['select_lang_prompt']}"
                    for lang in ALL_LANGUAGES)
    buttons = inner.utils.arrange_grid((Button.inline(i18n[lang]['lang_native_name'], data=f'set_lang_{lang}')
                                        for lang in ALL_LANGUAGES),
                                       columns=3)
    await event.respond(msg, buttons=buttons)


@command_gatekeeper(only_manager=False)
async def callback_set_lang(event: events.CallbackQuery.Event, *_, **__):  # callback data: set_lang_{lang_code}
    lang = event.data.decode().strip().split('set_lang_')[-1]
    welcome_msg = i18n[lang]['welcome_prompt']
    await db.User.update_or_create(defaults={'lang': lang}, id=event.chat_id)
    await set_bot_commands(scope=types.BotCommandScopePeer(await event.get_input_chat()),
                           lang_code='',
                           commands=get_commands_list(lang=lang, manager=event.chat_id == env.MANAGER))
    logger.info(f'Changed language to {lang} for {event.chat_id}')
    help_button = Button.inline(text=i18n[lang]['cmd_description_help'], data='help')
    await event.edit(welcome_msg, buttons=help_button)


@command_gatekeeper(only_manager=False)
async def cmd_or_callback_help(event: Union[events.NewMessage.Event, Message, events.CallbackQuery.Event],
                               *_,
                               lang: Optional[str] = None,
                               **__):  # callback data: help; command: /help
    msg = i18n[lang]['help_msg_html']
    await event.respond(msg, parse_mode='html') \
        if isinstance(event, events.NewMessage.Event) or not hasattr(event, 'edit') \
        else await event.edit(msg, parse_mode='html')


@command_gatekeeper(only_manager=False)
async def cmd_version(event: Union[events.NewMessage.Event, Message], *_, **__):
    await event.respond(env.VERSION)


# bypassing command gatekeeper
async def callback_null(event: events.CallbackQuery.Event):  # callback data = null
    await event.answer(cache_time=3600)
    raise events.StopPropagation


@command_gatekeeper(only_manager=False)
async def callback_cancel(event: events.CallbackQuery.Event,
                          *_,
                          lang: Optional[str] = None,
                          **__):  # callback data = cancel
    await event.edit(i18n[lang]['canceled_by_user'])


@command_gatekeeper(only_manager=False, allow_in_old_fashioned_groups=True)
async def callback_get_group_migration_help(event: events.CallbackQuery.Event,
                                            *_,
                                            **__):  # callback data: get_group_migration_help_{lang_code}
    lang = event.data.decode().strip().split('get_group_migration_help_')[-1]
    chat = await event.get_chat()
    if not isinstance(chat, types.Chat) or chat.migrated_to:  # already a supergroup
        try:
            await event.delete()
        except RPCError:
            pass
        return
    msg, buttons = get_group_migration_help_msg(lang)
    await event.edit(msg, buttons=buttons, parse_mode='html')
