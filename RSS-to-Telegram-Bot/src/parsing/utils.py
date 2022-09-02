from __future__ import annotations
from typing import Optional, Sequence, Union

import re
import json
from contextlib import suppress
from bs4 import BeautifulSoup
from bs4.element import Tag
from minify_html import minify as _minify
from html import unescape
from emoji import emojize
from telethon.tl.types import TypeMessageEntity
from telethon.helpers import add_surrogate
from functools import partial
from urllib.parse import urljoin
from os import path
from itertools import chain

from .. import log
from ..aio_helper import run_async_on_demand
from ..compat import parsing_utils_html_validator_preprocess

logger = log.getLogger('RSStT.parsing')

# noinspection SpellCheckingInspection
SPACES = (
    # all characters here, except for \u200c, \u200d and \u2060, are converted to space on TDesktop, but Telegram
    # Android preserves all
    ' '  # '\x20', SPACE
    '\xa0'  # NO-BREAK SPACE
    '\u2002'  # EN SPACE
    '\u2003'  # EM SPACE
    '\u2004'  # THREE-PER-EM SPACE
    '\u2005'  # FOUR-PER-EM SPACE
    '\u2006'  # SIX-PER-EM SPACE
    '\u2007'  # FIGURE SPACE
    '\u2008'  # PUNCTUATION SPACE
    '\u2009'  # THIN SPACE
    '\u200a'  # HAIR SPACE
    '\u200b'  # ZERO WIDTH SPACE, ZWSP
    # '\u200c'  # ZERO WIDTH NON-JOINER, ZWNJ, important for emoji or some languages
    # '\u200d'  # ZERO WIDTH JOINER, ZWJ, important for emoji or some languages
    '\u202f'  # NARROW NO-BREAK SPACE
    '\u205f'  # MEDIUM MATHEMATICAL SPACE, MMSP
    # '\u2060'  # WORD JOINER
    '\u3000'  # IDEOGRAPHIC SPACE
)
INVALID_CHARACTERS = (
    # all characters here are converted to space server-side
    '\x00'  # NULL
    '\x01'  # START OF HEADING
    '\x02'  # START OF TEXT
    '\x03'  # END OF TEXT
    '\x04'  # END OF TRANSMISSION
    '\x05'  # ENQUIRY
    '\x06'  # ACKNOWLEDGE
    '\x07'  # BELL
    '\x08'  # BACKSPACE
    '\t'    # '\x09', # HORIZONTAL TAB
    '\x0b'  # LINE TABULATION
    '\x0c'  # FORM FEED
    '\x0e'  # SHIFT OUT
    '\x0f'  # SHIFT IN
    '\x10'  # DATA LINK ESCAPE
    '\x11'  # DEVICE CONTROL ONE
    '\x12'  # DEVICE CONTROL TWO
    '\x13'  # DEVICE CONTROL THREE
    '\x14'  # DEVICE CONTROL FOUR
    '\x15'  # NEGATIVE ACKNOWLEDGE
    '\x16'  # SYNCHRONOUS IDLE
    '\x17'  # END OF TRANSMISSION BLOCK
    '\x18'  # CANCEL
    '\x19'  # END OF MEDIUM
    '\x1a'  # SUBSTITUTE
    '\x1b'  # ESCAPE
    '\x1c'  # FILE SEPARATOR
    '\x1d'  # GROUP SEPARATOR
    '\x1e'  # RECORD SEPARATOR
    '\x1f'  # UNIT SEPARATOR
    '\u2028'  # LINE SEPARATOR
    '\u2029'  # PARAGRAPH SEPARATOR
)

replaceInvalidCharacter = partial(re.compile(rf'[{INVALID_CHARACTERS}]').sub, ' ')  # use initially
replaceSpecialSpace = partial(re.compile(rf'[{SPACES[1:]}]').sub, ' ')  # use carefully
stripBr = partial(re.compile(r'\s*<br\s*/?\s*>\s*').sub, '<br>')
stripLineEnd = partial(re.compile(rf'[{SPACES}]+\n').sub, '\n')  # use firstly
stripNewline = partial(re.compile(r'\n{3,}').sub, '\n\n')  # use secondly
stripAnySpace = partial(re.compile(r'\s+').sub, ' ')
isAbsoluteHttpLink = re.compile(r'^https?://').match
isSmallIcon = re.compile(r'(width|height): ?(([012]?\d|30)(\.\d)?px|([01](\.\d)?|2)r?em)').search

minify = partial(_minify,
                 # https://docs.rs/minify-html/latest/minify_html/struct.Cfg.html
                 do_not_minify_doctype=True,
                 ensure_spec_compliant_unquoted_attribute_values=True,
                 keep_closing_tags=True,
                 keep_spaces_between_attributes=True)


class Enclosure:
    def __init__(self, url: str, length: Union[int, str], _type: str, duration: str = None):
        self.url = url
        self.length = (
            int(length)
            if isinstance(length, str) and length.isdigit()
            else length
            if isinstance(length, int)
            else None
        )
        self.type = _type
        self.duration = duration


# load emoji dict
with open(path.join(path.dirname(__file__), 'emojify.json'), 'r', encoding='utf-8') as emojify_json:
    emoji_dict = json.load(emojify_json)


def resolve_relative_link(base: Optional[str], url: Optional[str]) -> str:
    if not base or not url or isAbsoluteHttpLink(url) or not isAbsoluteHttpLink(base):
        return url or ''
    return urljoin(base, url)


def emojify(xml):
    xml = emojize(xml, language='alias', variant='emoji_type')
    for emoticon, emoji in emoji_dict.items():
        # emojify weibo emoticons, get all here: https://api.weibo.com/2/emotions.json?source=1362404091
        xml = xml.replace(f'[{emoticon}]', emoji)
    return xml


def is_emoticon(tag: Tag) -> bool:
    if tag.name != 'img':
        return False
    src = tag.get('src', '')
    alt, _class = tag.get('alt', ''), tag.get('class', '')
    style, width, height = tag.get('style', ''), tag.get('width', ''), tag.get('height', '')
    width = int(width) if width and width.isdigit() else float('inf')
    height = int(height) if height and height.isdigit() else float('inf')
    return (width <= 30 or height <= 30 or isSmallIcon(style)
            or 'emoji' in _class or 'emoticon' in _class or (alt.startswith(':') and alt.endswith(':'))
            or src.startswith('data:'))


def _html_validator(html: str) -> str:
    html = parsing_utils_html_validator_preprocess(html)
    html = minify(html)
    html = stripBr(html)
    html = replaceInvalidCharacter(html)
    return html


async def html_validator(html: str) -> str:
    return await run_async_on_demand(_html_validator, html, condition=len(html) > 64 * 1024)


def html_space_stripper(s: str, enable_emojify: bool = False) -> str:
    if not s:
        return s
    s = stripAnySpace(replaceSpecialSpace(replaceInvalidCharacter(unescape(s)))).strip()
    return emojify(s) if enable_emojify else s


async def parse_entry(entry, feed_link: Optional[str] = None):
    class EntryParsed:
        content: str = ''
        link: Optional[str] = None
        author: Optional[str] = None
        title: Optional[str] = None
        enclosures: list[Enclosure] = None

    # entry.summary returns summary(Atom) or description(RSS)
    content = entry.get('content') or entry.get('summary', '')

    if isinstance(content, list):  # Atom
        if len(content) == 1:
            content = content[0]
        else:
            for _content in content:
                content_type = _content.get('type', '')
                if 'html' in content_type or 'xml' in content_type:
                    content = _content
                    break
            else:
                content = content[0]
        content = content.get('value', '')

    EntryParsed.content = await html_validator(content)
    EntryParsed.link = entry.get('link') or entry.get('guid')
    author = entry['author'] if ('author' in entry and type(entry['author']) is str) else None
    author = html_space_stripper(author) if author else None
    EntryParsed.author = author or None  # reject empty string
    # hmm, some entries do have no title, should we really set up a feed hospital?
    title = entry.get('title')
    title = html_space_stripper(title, enable_emojify=True) if title else None
    EntryParsed.title = title or None  # reject empty string
    if isinstance(entry.get('links'), list):
        EntryParsed.enclosures = []
        for link in entry['links']:
            if link.get('rel') == 'enclosure':
                enclosure_url = link.get('href')
                if not enclosure_url:
                    continue
                enclosure_url = resolve_relative_link(feed_link, enclosure_url)
                EntryParsed.enclosures.append(Enclosure(url=enclosure_url,
                                                        length=link.get('length'),
                                                        _type=link.get('type')))
        if EntryParsed.enclosures and entry.get('itunes_duration'):
            EntryParsed.enclosures[0].duration = entry['itunes_duration']

    return EntryParsed


def surrogate_len(s: str) -> int:
    return len(add_surrogate(s))


def sort_entities(entities: Sequence[TypeMessageEntity]) -> list[TypeMessageEntity]:
    entities = list(entities)
    _entities = []
    while entities:
        e = entities.pop(0)
        is_duplicated = any(compare_entity(e, _e) for _e in entities)
        if not is_duplicated:
            _entities.append(e)
    return sorted(_entities, key=lambda entity: entity.offset)


def is_position_within_entity(pos: int, entity: TypeMessageEntity) -> bool:
    return entity.offset <= pos < entity.offset + entity.length


def filter_entities_by_position(pos: int, entities: Sequence[TypeMessageEntity]) -> list[TypeMessageEntity]:
    return [entity for entity in entities if is_position_within_entity(pos, entity)]


def filter_entities_by_range(start: int, end: int, entities: Sequence[TypeMessageEntity]) -> list[TypeMessageEntity]:
    return [entity for entity in entities if start <= entity.offset < end]


def copy_entity(entity: TypeMessageEntity) -> TypeMessageEntity:
    entity_dict = entity.to_dict()
    del entity_dict['_']
    return type(entity)(**entity_dict)


def copy_entities(entities: Sequence[TypeMessageEntity]) -> list[TypeMessageEntity]:
    return [copy_entity(entity) for entity in entities]


def compare_entity(a: TypeMessageEntity, b: TypeMessageEntity, ignore_position: bool = False) -> bool:
    if type(a) != type(b):
        return False

    a_dict = a.to_dict()
    b_dict = b.to_dict()
    if ignore_position:
        for d in (a_dict, b_dict):
            for key in ('offset', 'length'):
                with suppress(KeyError):
                    del d[key]

    return a_dict == b_dict


def merge_contiguous_entities(entities: Sequence[TypeMessageEntity]) -> list[TypeMessageEntity]:
    if len(entities) < 2:
        return list(entities)

    merged_entities = []
    entities = sort_entities(entities)
    while entities:
        entity = entities.pop(0)
        start_pos = entity.offset
        end_pos = entity.offset + entity.length
        for contiguous_entity in (_entity
                                  for _entity in entities
                                  if (
                                          (start_pos <= _entity.offset <= end_pos
                                           or _entity.offset <= start_pos <= _entity.offset + _entity.length)
                                          and compare_entity(entity, _entity, ignore_position=True)
                                  )):
            new_start_pos = min(start_pos, contiguous_entity.offset)
            new_end_pos = max(end_pos, contiguous_entity.offset + contiguous_entity.length)
            entity = copy_entity(entity)
            entity.offset = new_start_pos
            entity.length = new_end_pos - new_start_pos
        merged_entities.append(entity)
    return merged_entities
