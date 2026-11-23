"""Random draws for one question at a time.

`bind` installs a private stream for the question being composed. New
generators read that stream, so another session cannot consume their draws.
Older generators still use the process-wide `random` module and stay inside
the paper lock.
"""

import random
from contextvars import ContextVar

_current: ContextVar = ContextVar("stem_rng", default=None)
_story_seed: ContextVar = ContextVar("stem_story_seed", default=None)


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


def bind_story(seed):
    """Pin story choice for one strict-parallel class set. None keeps it random."""
    return _story_seed.set(seed)


def release_story(token):
    _story_seed.reset(token)


def story_choice(options):
    """Pick a cover from the class seed when a strict-parallel set is being built.

    Cognitive Twin and a single redraw leave the seed unset, so the story can change.
    """
    items = tuple(options)
    seed = _story_seed.get()
    if seed is None:
        return choice(items)
    return items[int(seed) % len(items)]


def randint(low: int, high: int) -> int:
    return _stream().randint(low, high)
