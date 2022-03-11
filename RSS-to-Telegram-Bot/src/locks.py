"""
Shared locks.
"""
from __future__ import annotations

import asyncio
from asyncio import BoundedSemaphore, Lock
from collections import defaultdict
from functools import partial
from typing import Union
from urllib.parse import urlparse

_USER_LIKE = Union[int, str]


# ----- user locks -----

class _UserLockBucket:
    def __init__(self):
        self.msg_lock = Lock()
        self.flood_lock = Lock()
        self.media_upload_semaphore = BoundedSemaphore(3)
        self.pending_callbacks = set()


_user_bucket: defaultdict[_USER_LIKE, _UserLockBucket] = defaultdict(_UserLockBucket)


def user_msg_lock(user: _USER_LIKE) -> Lock:
    return _user_bucket[user].msg_lock


def user_flood_lock(user: _USER_LIKE) -> Lock:
    return _user_bucket[user].flood_lock


def user_media_upload_semaphore(user: _USER_LIKE) -> BoundedSemaphore:
    return _user_bucket[user].media_upload_semaphore


def user_msg_locks(user: _USER_LIKE) -> tuple[Lock, Lock]:
    """
    :return: user_msg_lock, user_flood_lock
    """
    return user_msg_lock(user), user_flood_lock(user)


def user_pending_callbacks(user: _USER_LIKE) -> set:
    return _user_bucket[user].pending_callbacks


async def user_flood_wait(user: _USER_LIKE, seconds: int) -> bool:
    flood_lock = user_flood_lock(user)
    if not flood_lock.locked():
        try:
            await asyncio.wait_for(flood_lock.acquire(), timeout=2)  # double insurance to make sure only wait once
            try:
                await asyncio.sleep(seconds + 1)
            finally:
                flood_lock.release()
        except asyncio.TimeoutError:
            return False
        return True
    return False


# ----- web locks -----
_hostname_semaphore_bucket: defaultdict[str, BoundedSemaphore] = defaultdict(partial(BoundedSemaphore, 5))
overall_web_semaphore = BoundedSemaphore(100)


def hostname_semaphore(url: str, parse: bool = True) -> BoundedSemaphore:
    hostname = urlparse(url).hostname if parse else url
    return _hostname_semaphore_bucket[hostname]
