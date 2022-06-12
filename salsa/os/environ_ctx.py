# coding: utf-8
"""From https://github.com/laurent-laporte-pro/stackoverflow-q2059482 - MIT LICENSE"""

import contextlib
import os
from typing import Iterator


@contextlib.contextmanager
def modified_environ(*remove: str, **update: str) -> Iterator:
    """
    Temporarily updates the ``os.environ`` dictionary in-place.
    The ``os.environ`` dictionary is updated in-place so that the modification
    is sure to work in all situations.
    :param remove: Environment variables to remove.
    :param update: Dictionary of environment variables and values to add/update.
    """
    env = os.environ
    update = update or {}
    remove = remove or ()

    # List of environment variables being updated or removed.
    stomped = (set(update.keys()) | set(remove)) & set(env.keys())
    # Environment variables and values to restore on exit.
    update_after = {k: env[k] for k in stomped}
    # Environment variables and values to remove on exit.
    remove_after = frozenset(k for k in update if k not in env)

    try:
        env.update(update)
        for k in remove:
            env.pop(k, None)
        yield
    finally:
        env.update(update_after)
        for k in remove_after:
            env.pop(k)
