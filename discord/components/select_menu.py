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

from __future__ import annotations

from typing import ClassVar, Generic, Literal
from abc import ABC

from discord.enums import ComponentType
from .component import Component
from .types import T


class SelectMenu(Component[T], ABC, Generic[T]):
    """Represents a select menu from the Discord Bot UI Kit.

    This inherits from :class:`Component`.

    This is an abstract class and cannot be instantiated directly.

    .. versionadded:: 3.0

    """

    __slots__: tuple[str, ...] = (  # pyright: ignore[reportIncompatibleUnannotatedOverride]
        "custom_id",
        "placeholder",
        "min_values",
        "max_values",
        "disabled",
    )

    __repr_info__: ClassVar[tuple[str, ...]] = __slots__
    versions: tuple[int, ...] = (1, 2)
    type: Literal[  # pyright: ignore[reportIncompatibleVariableOverride]
        ComponentType.string_select,
        ComponentType.channel_select,
        ComponentType.role_select,
        ComponentType.mentionable_select,
        ComponentType.user_select,
    ]
    width: Literal[5] = 5

    def __init__(
        self,
        custom_id: str,
        *,
        placeholder: str | None = None,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False,
        id: int | None = None,
    ):
        self.custom_id: str = custom_id
        self.placeholder: str | None = placeholder
        self.min_values: int = min_values
        self.max_values: int = max_values
        self.disabled: bool = disabled
        super().__init__(id=id)
