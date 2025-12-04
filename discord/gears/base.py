"""
The MIT License (MIT)

Copyright (c) 2021-present Pycord Development

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Awaitable, Callable, Collection, Sequence
from functools import partial
from typing import (
    TYPE_CHECKING,
    Any,
    Protocol,
    TypeAlias,
    TypeVar,
    cast,
    runtime_checkable,
)

from ..app.event_emitter import Event
from ..utils import MISSING, Undefined
from ..utils.annotations import get_annotations
from ..utils.private import hybridmethod

E = TypeVar("E", bound="Event", covariant=True)

EventCallback: TypeAlias = Callable[[E], Awaitable[None]]


class GearBase(ABC):
    @abstractmethod
    def add_listener(
        self,
        callback: Callable[[E], Awaitable[None]],
        *,
        event: type[E] | Undefined = MISSING,
        is_instance_function: bool = False,
        once: bool = False,
    ) -> None: ...

    @abstractmethod
    def remove_listener(
        self, callback: EventCallback[E], event: type[E] | Undefined = MISSING, is_instance_function: bool = False
    ) -> None: ...

    @abstractmethod
    def listen(self, *args: Any, **kwargs: Any) -> Callable[[Callable[[E], Awaitable[None]]], EventCallback[E]]: ...
