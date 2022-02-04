from __future__ import annotations
from typing import Union, Optional, AnyStr
from src.compat import nullcontext, ssl_create_default_context

import asyncio
import functools
import aiodns
import aiohttp
import feedparser
from concurrent.futures import ThreadPoolExecutor
from aiohttp_socks import ProxyConnector
from aiohttp_retry import RetryClient, ExponentialRetry
from ssl import SSLError
from ipaddress import ip_network, ip_address
from urllib.parse import urlparse
from socket import AF_INET, AF_INET6
from multidict import CIMultiDictProxy
from attr import define

from src import env, log, locks
from src.i18n import i18n

logger = log.getLogger('RSStT.web')

_feedparser_thread_pool = ThreadPoolExecutor(1, 'feedparser_')
_resolver = aiodns.DNSResolver(timeout=3, loop=env.loop)

PROXY = env.R_PROXY.replace('socks5h', 'socks5').replace('sock4a', 'socks4') if env.R_PROXY else None
PRIVATE_NETWORKS = tuple(ip_network(ip_block) for ip_block in
                         ('127.0.0.0/8', '::1/128',  # loopback is not a private network, list in here for convenience
                          '169.254.0.0/16', 'fe80::/10',  # link-local address
                          '10.0.0.0/8',  # class A private network
                          '172.16.0.0/12',  # class B private networks
                          '192.168.0.0/16',  # class C private networks
                          'fc00::/7',  # ULA
                          ))

HEADER_TEMPLATE = {
    'User-Agent': env.USER_AGENT,
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br',
}
FEED_ACCEPT = 'application/rss+xml, application/rdf+xml, application/atom+xml, ' \
              'application/xml;q=0.9, text/xml;q=0.8, text/*;q=0.7, application/*;q=0.6'

EXCEPTIONS_SHOULD_RETRY = (asyncio.TimeoutError,
                           # aiohttp.ClientPayloadError,
                           # aiohttp.ClientResponseError,
                           # aiohttp.ClientConnectionError,
                           aiohttp.ServerConnectionError,
                           TimeoutError)

RETRY_OPTION = ExponentialRetry(attempts=2, start_timeout=1, exceptions=set(EXCEPTIONS_SHOULD_RETRY))


@define
class WebResponse:
    url: str  # redirected url
    content: Optional[AnyStr]
    headers: CIMultiDictProxy[str]
    status: int
    reason: Optional[str]


@define
class WebFeed:
    url: str  # redirected url
    headers: Optional[CIMultiDictProxy[str]] = None
    status: int = -1
    reason: Optional[str] = None
    rss_d: Optional[feedparser.FeedParserDict] = None
    msg: Optional[str] = None


def proxy_filter(url: str, parse: bool = True) -> bool:
    if not (env.PROXY_BYPASS_PRIVATE or env.PROXY_BYPASS_DOMAINS):
        return True

    hostname = urlparse(url).hostname if parse else url
    if env.PROXY_BYPASS_PRIVATE:
        try:
            ip_a = ip_address(hostname)
            is_private = any(ip_a in network for network in PRIVATE_NETWORKS)
            if is_private:
                return False
        except ValueError:
            pass  # not an IP, continue
    if env.PROXY_BYPASS_DOMAINS:
        is_bypassed = any(hostname.endswith(domain) and (hostname == domain or hostname[-len(domain) - 1] == '.')
                          for domain in env.PROXY_BYPASS_DOMAINS)
        if is_bypassed:
            return False
    return True


async def get(url: str, timeout: Optional[float] = None, semaphore: Union[bool, asyncio.Semaphore] = None,
              headers: Optional[dict] = None, decode: bool = False, no_body: bool = False) -> WebResponse:
    """
    :param url: URL to fetch
    :param timeout: timeout in seconds
    :param semaphore: semaphore to use for limiting concurrent connections
    :param headers: headers to use
    :param decode: whether to decode the response body
    :param no_body: whether to return the response headers only
    :return: {url, content, headers, status}
    """
    if not timeout:
        timeout = 12
    wait_for_timeout = (timeout * 2 + 5) * (2 if env.IPV6_PRIOR else 1)
    return await asyncio.wait_for(_get(url, timeout, semaphore, headers, decode, no_body), wait_for_timeout)


async def _get(url: str, timeout: Optional[float] = None, semaphore: Union[bool, asyncio.Semaphore] = None,
               headers: Optional[dict] = None, decode: bool = False, no_body: bool = False) -> WebResponse:
    host = urlparse(url).hostname
    semaphore_to_use = locks.hostname_semaphore(host, parse=False) if semaphore in (None, True) \
        else (semaphore or nullcontext())
    v6_address = None
    try:
        v6_address = await _resolver.query(host, 'AAAA') if env.IPV6_PRIOR else None
    except aiodns.error.DNSError:
        pass
    except Exception as e:
        logger.debug(f'Error occurred when querying {url} AAAA:', exc_info=e)
    socket_family = AF_INET6 if v6_address else 0

    _headers = HEADER_TEMPLATE.copy()
    if headers:
        _headers.update(headers)

    tries = 0
    retry_in_v4_flag = False
    while True:
        tries += 1
        assert tries <= 2, 'Too many tries'

        if retry_in_v4_flag:
            socket_family = AF_INET
        ssl_context = ssl_create_default_context()
        proxy_connector = (
            ProxyConnector.from_url(PROXY, family=socket_family, ssl=ssl_context)
            if (PROXY and proxy_filter(host, parse=False))
            else aiohttp.TCPConnector(family=socket_family, ssl=ssl_context)
        )

        try:
            async with locks.overall_web_semaphore:
                async with semaphore_to_use:
                    async with RetryClient(retry_options=RETRY_OPTION, connector=proxy_connector,
                                           timeout=aiohttp.ClientTimeout(total=timeout), headers=_headers) as session:
                        async with session.get(url) as response:
                            status = response.status
                            content = (await (response.text() if decode else response.read())
                                       if status == 200 and not no_body
                                       else None)
                            if status in (403, 429, 451) and socket_family == AF_INET6 and tries == 1:
                                retry_in_v4_flag = True
                                continue
                            return WebResponse(url=url,
                                               content=content,
                                               headers=response.headers,
                                               status=status,
                                               reason=response.reason)
        except EXCEPTIONS_SHOULD_RETRY as e:
            if socket_family != AF_INET6 or tries > 1:
                raise e
            err_msg = str(e).strip()
            logger.debug(f'Fetch failed ({e.__class__.__name__}' + (f': {err_msg}' if err_msg else '')
                         + f') using IPv6, retrying using IPv4: {url}')
            retry_in_v4_flag = True
            continue


async def get_session(timeout: Optional[float] = None):
    if not timeout:
        timeout = 12

    proxy_connector = ProxyConnector.from_url(PROXY) if PROXY else None

    session = RetryClient(retry_options=RETRY_OPTION, connector=proxy_connector,
                          timeout=aiohttp.ClientTimeout(total=timeout), headers={'User-Agent': env.USER_AGENT})

    return session


async def feed_get(url: str, timeout: Optional[float] = None, web_semaphore: Union[bool, asyncio.Semaphore] = None,
                   headers: Optional[dict] = None, lang: Optional[str] = None, verbose: bool = True) -> WebFeed:
    ret = WebFeed(url=url)

    auto_warning = logger.warning if verbose else logger.debug
    _headers = {}
    if headers:
        _headers.update(headers)
    if 'Accept' not in _headers:
        _headers['Accept'] = FEED_ACCEPT

    try:
        resp = await get(url, timeout, web_semaphore, headers=_headers)
        rss_content = resp.content
        ret.url = resp.url
        ret.headers = resp.headers
        ret.status = resp.status

        # some rss feed implement http caching improperly :(
        if resp.status == 200 and int(resp.headers.get('Content-Length', '1')) == 0:
            ret.status = 304
            ret.msg = f'"Content-Length" is 0'
            return ret

        if resp.status == 304:
            ret.msg = f'304 Not Modified'
            return ret  # 304 Not Modified, feed not updated

        if rss_content is None:
            status_caption = f'{resp.status}' + f' {resp.reason}' if resp.reason else ''
            auto_warning(f'Fetch failed (status code error, {status_caption}): {url}')
            ret.msg = f'ERROR: {i18n[lang]["status_code_error"]} ({status_caption})'
            return ret

        if len(rss_content) <= 524288:
            rss_d = feedparser.parse(rss_content, sanitize_html=False)
        else:  # feed too large, run in another thread to avoid blocking the bot
            rss_d = await asyncio.get_event_loop().run_in_executor(_feedparser_thread_pool,
                                                                   functools.partial(feedparser.parse,
                                                                                     rss_content,
                                                                                     sanitize_html=False))

        if 'title' not in rss_d.feed:
            auto_warning(f'Fetch failed (feed invalid): {url}')
            ret.msg = 'ERROR: ' + i18n[lang]['feed_invalid']
            return ret

        ret.rss_d = rss_d
    except aiohttp.InvalidURL:
        auto_warning(f'Fetch failed (URL invalid): {url}')
        ret.msg = 'ERROR: ' + i18n[lang]['url_invalid']
    except (asyncio.TimeoutError,
            aiohttp.ClientError,
            SSLError,
            OSError,
            ConnectionError,
            TimeoutError) as e:
        err_name = e.__class__.__name__
        auto_warning(f'Fetch failed (network error, {err_name}): {url}')
        ret.msg = f'ERROR: {i18n[lang]["network_error"]} ({err_name})'
    except Exception as e:
        auto_warning(f'Fetch failed: {url}', exc_info=e)
        ret.msg = 'ERROR: ' + i18n[lang]['internal_error']

    return ret
