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

from typing import Generic, override

from discord.types.components import SelectDefaultValue
from .types import DT


class DefaultSelectOption(Generic[DT]):
    """
    Represents a default select menu option.
    Can only be used :class:`UserSelectMenu`, :class:`RoleSelectMenu`, and :class:`MentionableSelectMenu`.

    .. versionadded:: 3.0

    Attributes
    ----------
    id: :class:`int`
        The ID of the default option.
    type: :class:`str`
        The type of the default option. This can be either "user", "role", or "channel".
        This is used to determine which type of select menu this option belongs to.
    """

    __slots__: tuple[str, ...] = ("id", "type")

    def __init__(
        self,
        id: int,
        type: DT,
    ) -> None:
        self.id: int = id
        self.type: DT = type

    @override
    def __repr__(self) -> str:
        return f"<DefaultSelectOption id={self.id!r} type={self.type!r}>"

    @classmethod
    def from_payload(cls, payload: SelectDefaultValue[DT]) -> DefaultSelectOption[DT]:
        """Creates a DefaultSelectOption from a dictionary."""
        return cls(
            id=payload["id"],
            type=payload["type"],
        )

    def to_dict(self) -> SelectDefaultValue[DT]:
        """Converts the DefaultSelectOption to a dictionary."""
        return {
            "id": self.id,
            "type": self.type,
        }
