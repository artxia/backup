"""
Asyncio helper functions.
"""
from __future__ import annotations
from typing import Callable, Union
from typing_extensions import Literal

import os
from functools import partial
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from time import sleep
from signal import signal, SIGINT, SIGTERM
from collections import deque

from . import env

CPU_COUNT = os.cpu_count()
AVAIL_CPU_COUNT = len(os.sched_getaffinity(0))
PROCESS_COUNT = min(AVAIL_CPU_COUNT, 3) if env.MULTIPROCESSING else 1

THREAD_POOL_WEIGHT = 1
PROCESS_POOL_WEIGHT = PROCESS_COUNT - 1

POOL_TYPE = Literal['thread', 'process']

assert min(CPU_COUNT, AVAIL_CPU_COUNT, PROCESS_COUNT) > 0
assert min(THREAD_POOL_WEIGHT, PROCESS_POOL_WEIGHT) >= 0

# asyncio executors
aioThreadExecutor = ThreadPoolExecutor(
    max_workers=THREAD_POOL_WEIGHT,
    thread_name_prefix="rsstt_aio_thread_"
) if THREAD_POOL_WEIGHT else None
aioProcessExecutor = ProcessPoolExecutor(
    max_workers=PROCESS_POOL_WEIGHT,
    initializer=lambda: (
            signal(SIGINT, lambda *_, **__: exit(1))
            and
            signal(SIGTERM, lambda *_, **__: exit(1))
    )
) if PROCESS_POOL_WEIGHT else None

__aioExecutorsDeque = deque(
    (
        *((aioThreadExecutor,) * THREAD_POOL_WEIGHT),
        *((aioProcessExecutor,) * PROCESS_COUNT),
    )
) if aioThreadExecutor and aioProcessExecutor else None


def _get_executor():
    if not __aioExecutorsDeque:
        return aioThreadExecutor or aioProcessExecutor
    chosen_executor = __aioExecutorsDeque[0]
    __aioExecutorsDeque.rotate(1)
    return chosen_executor


async def run_async_on_demand(func: Callable,
                              *args,
                              condition: Union[Callable, bool] = None,
                              prefer_pool: POOL_TYPE = None,
                              **kwargs):
    return (
        await run_async(func, *args, prefer_pool=prefer_pool, **kwargs)
        if condition and (condition is True or condition(*args, **kwargs)) else
        func(*args, **kwargs)
    )


async def run_async(func: Callable, *args, prefer_pool: POOL_TYPE = None, **kwargs):
    """
    Run a CPU-consuming function asynchronously.
    """
    rotate_deque_flag = False
    if prefer_pool == 'thread':
        executor = aioThreadExecutor or aioProcessExecutor
        rotate_deque_flag = True
    elif prefer_pool == 'process':
        executor = aioProcessExecutor or aioThreadExecutor
        rotate_deque_flag = True
    else:
        executor = _get_executor()

    if rotate_deque_flag and __aioExecutorsDeque and executor is __aioExecutorsDeque[0]:
        __aioExecutorsDeque.rotate(1)

    return (
        await env.loop.run_in_executor(executor, partial(func, *args, **kwargs))
        if kwargs else
        await env.loop.run_in_executor(executor, func, *args)
    )


def init():
    if aioProcessExecutor:
        [aioProcessExecutor.submit(sleep, 0.01 * (i + 1)) for i in range(PROCESS_COUNT - 1)]


def shutdown():
    if aioProcessExecutor:
        aioProcessExecutor.shutdown(wait=True)
    aioThreadExecutor.shutdown(wait=False)
