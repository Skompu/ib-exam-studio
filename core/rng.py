"""Random draws for one question at a time.

`bind` installs a private stream for the question being composed. New
generators read that stream, so another session cannot consume their draws.
Older generators still use the process-wide `random` module and stay inside
the paper lock.
"""

import random
from contextvars import ContextVar

_current: ContextVar = ContextVar("stem_rng", default=None)


def bind(seed):
    return _current.set(random.Random(str(seed)))


def release(token):
    _current.reset(token)


def _stream():
    stream = _current.get()
    if stream is None:
        return random
    return stream


def choice(options):
    return _stream().choice(tuple(options))


def randint(low: int, high: int) -> int:
    return _stream().randint(low, high)
