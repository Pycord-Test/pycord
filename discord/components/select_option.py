"""
The MIT License (MIT)

Copyright (c) 2015-2021 Rapptz
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

from typing import TYPE_CHECKING, TypeAlias

from typing_extensions import override

from ..partial_emoji import PartialEmoji, _EmojiTag  # pyright: ignore[reportPrivateUsage]
from ..types.component_types import SelectOption as SelectOptionPayload
from ..utils import MISSING, Undefined

if TYPE_CHECKING:
    from ..emoji import AppEmoji, GuildEmoji
    from ..partial_emoji import PartialEmoji

AnyEmoji: TypeAlias = "GuildEmoji | AppEmoji | PartialEmoji"


class SelectOption:
    """Represents a :class:`discord.SelectMenu`'s option.

    These can be created by users.

    .. versionadded:: 2.0

    Attributes
    ----------
    label: :class:`str`
        The label of the option. This is displayed to users.
    value: :class:`str`
        The value of the option. This is not displayed to users.
    description: Optional[:class:`str`]
        An additional description of the option, if any.
        Can only be up to 100 characters.
    default: :class:`bool`
        Whether this option is selected by default.
    emoji: :class:`str` | :class:`PartialEmoji` | :class:`GuildEmoji` | :class:`AppEmoji` | :data:`None`
        The emoji of the option, if any.

    Parameters
    ----------
    label:
        The label of the option. This is displayed to users.
        Can only be up to 100 characters.
    value:
        The value of the option. This is not displayed to users.
        Can only be up to 100 characters. If not provided when constructed then it defaults to the
        label.
    description:
        An additional description of the option, if any.
        Can only be up to 100 characters.
    emoji:
        The emoji of the option, if any.
    """

    __slots__: tuple[str, ...] = (
        "label",
        "value",
        "description",
        "_emoji",
        "default",
    )

    def __init__(
        self,
        *,
        label: str,
        value: str | Undefined = MISSING,
        description: str | None = None,
        emoji: str | AnyEmoji | None = None,
        default: bool = False,
    ) -> None:
        if len(label) > 100:
            raise ValueError("label must be 100 characters or fewer")

        if value is not MISSING and len(value) > 100:
            raise ValueError("value must be 100 characters or fewer")

        if description is not None and len(description) > 100:
            raise ValueError("description must be 100 characters or fewer")

        self.label: str = label
        self.value: str = label if value is MISSING else value
        self.description: str | None = description
        self.emoji = emoji
        self.default: bool = default

    @override
    def __repr__(self) -> str:
        return (
            "<SelectOption"
            f" label={self.label!r} value={self.value!r} description={self.description!r} "
            f"emoji={self.emoji!r} default={self.default!r}>"
        )

    @override
    def __str__(self) -> str:
        base = f"{self.emoji} {self.label}" if self.emoji else self.label
        if self.description:
            return f"{base}\n{self.description}"
        return base

    @property
    def emoji(self) -> PartialEmoji | None:
        """The emoji of the option, if available."""
        return self._emoji

    @emoji.setter
    def emoji(self, value: str | AnyEmoji | None) -> None:  # pyright: ignore[reportPropertyTypeMismatch]
        if value is not None:
            if isinstance(value, str):
                value = PartialEmoji.from_str(value)
            elif isinstance(value, _EmojiTag):  # pyright: ignore[reportUnnecessaryIsInstance]
                value = value._to_partial()  # pyright: ignore[reportPrivateUsage]
            else:
                raise TypeError(  # pyright: ignore[reportUnreachable]
                    f"expected emoji to be None, str, GuildEmoji, AppEmoji, or PartialEmoji, not {value.__class__}"
                )

        self._emoji: PartialEmoji | None = value

    @classmethod
    def from_dict(cls, data: SelectOptionPayload) -> SelectOption:
        if e := data.get("emoji"):
            emoji = PartialEmoji.from_dict(e)
        else:
            emoji = None

        return cls(
            label=data["label"],
            value=data["value"],
            description=data.get("description"),
            emoji=emoji,
            default=data.get("default", False),
        )

    def to_dict(self) -> SelectOptionPayload:
        payload: SelectOptionPayload = {
            "label": self.label,
            "value": self.value,
            "default": self.default,
        }

        if self.emoji:
            payload["emoji"] = self.emoji.to_dict()  # type: ignore  # pyright: ignore[reportGeneralTypeIssues]

        if self.description:
            payload["description"] = self.description

        return payload
