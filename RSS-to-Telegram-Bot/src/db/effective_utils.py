from __future__ import annotations
from typing import Optional, Any, NoReturn, Union
from typing_extensions import Final
from collections.abc import Callable

from math import ceil
from random import shuffle

from . import models


class __EffectiveOptions:
    """
    EffectiveOptions singleton class.

    Implement a write-through cache that caches all options to reduce db load.
    """
    __singleton: Optional["__EffectiveOptions"] = None
    __initialized: bool = False

    def __new__(cls, *args, **kwargs):
        if not cls.__singleton:
            cls.__singleton = super().__new__(cls)
        return cls.__singleton

    def __init__(self):
        if self.__initialized:
            return
        self.__initialized = True

        self.__options: dict[str, Union[str, int]] = {}
        self.__cached = False
        self.__default_options: dict[str, Union[str, int]] = {
            "default_interval": 10,
            "minimal_interval": 5,
        }

    @property
    def options(self) -> dict[str, Union[str, int]]:
        return self.__options.copy()

    @property
    def default_options(self) -> dict[str, Union[str, int]]:
        return self.__default_options.copy()

    @property
    def default_interval(self) -> int:
        return self.get('default_interval')

    @property
    def minimal_interval(self) -> int:
        return self.get("minimal_interval")

    def validate(self, key: str, value: Union[int, str], ignore_type_error: bool = False) -> Union[int, str]:
        if len(key) > 255:
            raise KeyError("Option key must be 255 characters or less")

        value_type = type(self.__default_options[key])
        if value_type is str:
            return str(value)

        if value_type is int and type(value) is str:
            if value.lstrip('-').isdecimal():
                return int(value)

            if ignore_type_error:
                return self.__default_options[key]
            raise ValueError("Option value must be an integer")

        return value

    def get(self, key: str) -> Union[str, int]:
        """
        Get the value of an Option.

        :param key: option key
        :return: option value
        """
        if not self.__cached:
            raise RuntimeError("Options cache not initialized")
        return self.__options[key]

    async def set(self, key: str, value: Union[int, str]) -> NoReturn:
        """
        Set the value of an Option. (write-through to the DB)

        :param key: option key
        :param value: option value
        """
        value = self.validate(key, value)
        await models.Option.update_or_create(defaults={'value': str(value)}, key=key)
        self.__options[key] = value

    async def cache(self) -> NoReturn:
        """
        Cache all options from the DB.
        """
        options = await models.Option.all()
        for option in options:
            if option.key not in self.__default_options:  # invalid option
                continue
            self.__options[option.key] = self.validate(option.key, option.value, ignore_type_error=True)

        for key, value in self.__default_options.items():
            if key in self.__options:
                continue
            self.__options[key] = value
            # await models.Option.create(key=key, value=value)  # init option

        self.__cached = True


EffectiveOptions = __EffectiveOptions()


class EffectiveTasks:
    """
    EffectiveTasks class.

    A task dispatcher.
    """
    __task_buckets: dict[int, "EffectiveTasks"] = {}  # key: interval, value: EffectiveTasks
    __all_tasks: dict[int, int] = {}  # key: id, value: interval

    def __init__(self, interval: int) -> NoReturn:
        self.interval: Final[int] = interval
        self.__all_feeds: set[int] = set()
        self.__pending_feeds: list[int] = []  # use a list here to make randomization easier
        # self.__checked_feeds: set[int] = set()
        self.__run_count: int = 0

    @staticmethod
    def __ignore_key_or_value_error(func: Callable, *args, **kwargs) -> Optional[Any]:
        try:
            return func(*args, **kwargs)
        except (KeyError, ValueError):
            return None

    @classmethod
    async def init(cls, flush: bool = False) -> NoReturn:
        """
        Load a feeds from the DB and initialize tasks.

        :param flush: if already initialized, re-initialize?
        """
        if not cls.__task_buckets or flush:
            cls.__all_tasks = {}
            cls.__task_buckets = {}
            feeds = await models.Feed.filter(state=1).values('id', 'interval')
            default_interval = EffectiveOptions.default_interval
            for feed in feeds:
                cls.update(feed_id=feed['id'], interval=feed['interval'] or default_interval)

    def __update(self, feed_id: int):
        self.__all_feeds.add(feed_id)
        # no need to add it to the pending list, since it will be processed in the next cycle
        #
        # if feed_id not in self.__pending_feeds:
        #     self.__pending_feeds.append(feed_id)

    @classmethod
    def update(cls, feed_id: int, interval: int = None) -> NoReturn:
        """
        Update or add a task.

        :param feed_id: the id of the feed in the task
        :param interval: the interval of the task
        """
        interval = interval or EffectiveOptions.default_interval
        if feed_id in cls.__all_tasks:  # if already have a task
            if cls.__all_tasks[feed_id] == interval:  # no need to update
                return
            cls.delete(feed_id, _preserve_in_all_tasks=True)  # delete the old one

        if interval not in cls.__task_buckets:  # if lack of bucket
            cls.__task_buckets[interval] = cls(interval)  # create one

        cls.__all_tasks[feed_id] = interval  # log the new task
        cls.__task_buckets[interval].__update(feed_id)  # update task

    def __delete(self, feed_id: int) -> NoReturn:
        self.__ignore_key_or_value_error(self.__all_feeds.remove, feed_id)
        self.__ignore_key_or_value_error(self.__pending_feeds.remove, feed_id)

    @classmethod
    def delete(cls, feed_id: int, _preserve_in_all_tasks: bool = False) -> NoReturn:
        """
        Delete a task.

        :param feed_id: the id of the feed in the task
        :param _preserve_in_all_tasks: for internal use
        """
        try:
            old_interval = cls.__all_tasks[feed_id]
            cls.__task_buckets[old_interval].__delete(feed_id)

            if not _preserve_in_all_tasks:
                del cls.__all_tasks[feed_id]
        except KeyError:
            pass

    @classmethod
    def exist(cls, feed_id: int) -> bool:
        """
        Check if a task exists.

        :param feed_id: the id of the feed in the task
        :return `bool`: if the task exists
        """
        return feed_id in cls.__all_tasks

    @classmethod
    def get_interval(cls, feed_id: int) -> Optional[int]:
        """
        Get the interval of a task.

        :param feed_id: the id of the feed in the task
        :return `int`: the interval of the task, or `None` if task do not exist
        """
        return cls.__all_tasks[feed_id] if cls.exist(feed_id) else None

    def __get_tasks(self) -> set[int]:
        if len(self.__all_feeds) == 0:
            return set()  # nothing to run
        if self.__run_count == 0:
            self.__pending_feeds = list(self.__all_feeds)
            shuffle(self.__pending_feeds)  # randomize

        pop_count = ceil(len(self.__pending_feeds) / (self.interval - self.__run_count))
        # tasks_to_run = set(self.__pending_feeds.pop() for _ in range(pop_count) if self.__pending_feeds)
        tasks_to_run = set(self.__pending_feeds[:pop_count])
        del self.__pending_feeds[:pop_count]
        self.__run_count = self.__run_count + 1 if self.__run_count + 1 < self.interval else 0
        return tasks_to_run

    @classmethod
    def get_tasks(cls) -> set[int]:
        """
        Get tasks to be run.

        :return: a `set` contains the ids of feeds in tasks to be run
        """
        tasks_to_run = set()
        for effective_tasks in cls.__task_buckets.values():
            tasks = effective_tasks.__get_tasks()
            if tasks:
                tasks_to_run.update(tasks)

        return tasks_to_run


async def init():
    await EffectiveOptions.cache()
    await EffectiveTasks.init()
