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

from typing import TYPE_CHECKING, Literal, override
from collections.abc import Sequence

from discord.enums import ComponentType
from discord.types.components import StringSelect as StringSelectPayload
from .select_menu import SelectMenu
from .select_option import SelectOption

if TYPE_CHECKING:
    from typing_extensions import Self


class StringSelectMenu(SelectMenu[StringSelectPayload]):
    """Represents a string select menu from the Discord Bot UI Kit.

    This inherits from :class:`SelectMenu`.

    .. versionadded:: 3.0

    Attributes
    ----------
    options: List[:class:`SelectOption`]
        The options available in this select menu.
    custom_id: :class:`str`
        The custom ID of the select menu that gets received during an interaction.
    placeholder: Optional[:class:`str`]
        The placeholder text that is shown if nothing is selected, if any.
    min_values: :class:`int`
        The minimum number of values that must be selected.
        Defaults to 1.
    max_values: :class:`int`
        The maximum number of values that can be selected.
        Defaults to 1.
    disabled: :class:`bool`
        Whether the select menu is disabled or not.
        Defaults to ``False``.
    id: Optional[:class:`int`]
        The select menu's ID. If not provided, it is set sequentially by Discord.
        The ID `0` is treated as if no ID was provided.

    Parameters
    ----------
    custom_id: :class:`str`
        The custom ID of the select menu that gets received during an interaction.
    options: Sequence[:class:`SelectOption`]
        The options available in this select menu.
    placeholder: Optional[:class:`str`]
        The placeholder text that is shown if nothing is selected, if any.
    min_values: :class:`int`
        The minimum number of values that must be selected.
        Defaults to 1.
    max_values: :class:`int`
        The maximum number of values that can be selected.
        Defaults to 1.
    disabled: :class:`bool`
        Whether the select menu is disabled or not. Defaults to ``False``.
    id: Optional[:class:`int`]
        The select menu's ID. If not provided, it is set sequentially by Discord.
        The ID `0` is treated as if no ID was provided.
    """

    __slots__: tuple[str, ...] = ("options",)
    type: Literal[ComponentType.string_select] = ComponentType.string_select  # pyright: ignore[reportIncompatibleVariableOverride]

    def __init__(
        self,
        custom_id: str,
        options: Sequence[SelectOption],
        *,
        placeholder: str | None = None,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False,
        id: int | None = None,
    ):
        super().__init__(
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            id=id,
        )
        self.options: list[SelectOption] = list(options)

    @classmethod
    @override
    def from_payload(cls, payload: StringSelectPayload) -> Self:
        options = [SelectOption.from_dict(option) for option in payload["options"]]
        return cls(
            custom_id=payload["custom_id"],
            options=options,
            placeholder=payload.get("placeholder"),
            min_values=payload.get("min_values", 1),
            max_values=payload.get("max_values", 1),
            disabled=payload.get("disabled", False),
            id=payload.get("id"),
        )

    @override
    def to_dict(self) -> StringSelectPayload:
        payload: StringSelectPayload = {  # pyright: ignore[reportAssignmentType]
            "type": int(self.type),
            "id": self.id,
            "custom_id": self.custom_id,
            "options": [option.to_dict() for option in self.options],
            "min_values": self.min_values,
            "max_values": self.max_values,
        }
        if self.placeholder:
            payload["placeholder"] = self.placeholder

        if self.disabled:
            payload["disabled"] = self.disabled

        return payload
