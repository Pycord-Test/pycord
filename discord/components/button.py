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

from typing import TYPE_CHECKING, ClassVar, Literal, overload
from typing_extensions import override

from ..enums import ButtonStyle, ComponentType, try_enum
from ..partial_emoji import PartialEmoji, _EmojiTag  # pyright: ignore[reportPrivateUsage]
from ..types.components import ButtonComponent as ButtonComponentPayload
from .component import Component
from .types import AnyEmoji

if TYPE_CHECKING:
    from typing_extensions import Self


class Button(Component[ButtonComponentPayload]):
    """Represents a button from the Discord Bot UI Kit.

    This inherits from :class:`Component`.

    .. versionadded:: 2.0

    Attributes
    ----------
    type: Literal[:data:`ComponentType.button`]
        The type of component.
    style: :class:`ButtonStyle`
        The style of the button.
    custom_id: :class:`str` | :data:`None`
        The ID of the button that gets received during an interaction.
        If this button is for a URL, it does not have a custom ID.
    url: :class:`str` | :data:`None`
        The URL this button sends you to.
    disabled: :class:`bool`
        Whether the button is disabled or not.
    label: :class:`str` | :data:`None`
        The label of the button, if any.
    emoji: :class:`PartialEmoji`] | :data:`None`
        The emoji of the button, if available.
    sku_id: :class:`int` | :data:`None`
        The ID of the SKU this button refers to.
    id: :class:`int` | :data:`None`
        The button's ID. If not provided, it is set sequentially by Discord.
        The ID `0` is treated as if no ID was provided.

    Parameters
    ----------
    style:
        The style of the button.
    custom_id:
        The ID of the button that gets received during an interaction.
        Cannot be used with :class:`ButtonStyle.url` or :class:`ButtonStyle.premium`.
    label:
        The label of the button, if any.
        Cannot be used with :class:`ButtonStyle.premium`.
    emoji:
        The emoji of the button, if available.
        Cannot be used with :class:`ButtonStyle.premium`.
    disabled:
        Whether the button is disabled or not.
    url:
        The URL this button sends you to.
        Can only be used with :class:`ButtonStyle.url`.
    id:
        The button's ID. If not provided, it is set sequentially by Discord.
        The ID `0` is treated as if no ID was provided.
    sku_id:
        The ID of the SKU this button refers to.
        Can only be used with :class:`ButtonStyle.premium`.
    """

    __slots__: tuple[str, ...] = (
        "style",
        "custom_id",
        "url",
        "disabled",
        "label",
        "emoji",
        "sku_id",
    )

    __repr_info__: ClassVar[tuple[str, ...]] = __slots__
    versions: tuple[int, ...] = (1, 2)
    type: Literal[ComponentType.button] = ComponentType.button  # pyright: ignore[reportIncompatibleVariableOverride]
    width: Literal[1] = 1

    # Premium button
    @overload
    def __init__(
        self,
        style: Literal[ButtonStyle.premium],
        *,
        sku_id: int,
        disabled: bool = False,
        id: int | None = None,
    ) -> None: ...

    # URL button with label
    @overload
    def __init__(
        self,
        style: Literal[ButtonStyle.url],
        *,
        label: str,
        emoji: str | AnyEmoji | None = None,
        disabled: bool = False,
        url: str,
        id: int | None = None,
    ) -> None: ...

    # URL button with emoji
    @overload
    def __init__(
        self,
        style: Literal[ButtonStyle.url],
        *,
        emoji: str | AnyEmoji,
        label: str | None = None,
        disabled: bool = False,
        url: str,
        id: int | None = None,
    ) -> None: ...

    # Interactive button with label
    @overload
    def __init__(
        self,
        style: Literal[ButtonStyle.primary, ButtonStyle.secondary, ButtonStyle.success, ButtonStyle.danger],
        *,
        custom_id: str,
        label: str,
        emoji: str | AnyEmoji | None = None,
        disabled: bool = False,
        id: int | None = None,
    ) -> None: ...

    # Interactive button with emoji
    @overload
    def __init__(
        self,
        style: Literal[ButtonStyle.primary, ButtonStyle.secondary, ButtonStyle.success, ButtonStyle.danger],
        *,
        custom_id: str,
        emoji: str | AnyEmoji,
        label: str | None = None,
        disabled: bool = False,
        id: int | None = None,
    ) -> None: ...

    def __init__(
        self,
        style: int | ButtonStyle,
        custom_id: str | None = None,
        label: str | None = None,
        emoji: str | AnyEmoji | None = None,
        disabled: bool = False,
        url: str | None = None,
        id: int | None = None,
        sku_id: int | None = None,
    ) -> None:
        self.style: ButtonStyle = try_enum(ButtonStyle, style)
        self.custom_id: str | None = custom_id
        self.url: str | None = url
        self.disabled: bool = disabled
        self.label: str | None = label
        self.emoji: PartialEmoji | None
        if isinstance(emoji, _EmojiTag):
            self.emoji = emoji._to_partial()  # pyright: ignore[reportPrivateUsage]
        elif isinstance(emoji, str):
            self.emoji = PartialEmoji.from_str(emoji)
        else:
            self.emoji = emoji
        self.sku_id: int | None = sku_id
        super().__init__(id=id)

    @classmethod
    @override
    def from_payload(cls, payload: ButtonComponentPayload) -> Self:
        style = try_enum(ButtonStyle, payload["style"])
        custom_id = payload.get("custom_id")
        label = payload.get("label")
        emoji = payload.get("emoji")
        disabled = payload.get("disabled", False)
        url = payload.get("url")
        sku_id = payload.get("sku_id")

        if emoji is not None:
            emoji = PartialEmoji.from_dict(emoji)

        return cls(  # pyright: ignore[reportCallIssue]
            style=style,
            custom_id=custom_id,
            label=label,
            emoji=emoji,
            disabled=disabled,
            url=url,
            id=payload.get("id"),
            sku_id=int(sku_id) if sku_id is not None else None,
        )

    @override
    def to_dict(self) -> ButtonComponentPayload:
        payload: ButtonComponentPayload = {  # pyright: ignore[reportAssignmentType]
            "type": 2,
            "id": self.id,
            "style": int(self.style),
            "label": self.label,
            "disabled": self.disabled,
        }
        if self.custom_id:
            payload["custom_id"] = self.custom_id

        if self.url:
            payload["url"] = self.url

        if self.emoji:
            payload["emoji"] = self.emoji.to_dict()  # pyright: ignore[reportGeneralTypeIssues]

        if self.sku_id:
            payload["sku_id"] = self.sku_id

        return payload  # type: ignore
