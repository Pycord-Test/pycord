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

from collections.abc import Sequence
from typing import TYPE_CHECKING, Literal

from typing_extensions import override

from ..enums import ComponentType
from ..types.components import UserSelect as UserSelectPayload
from .default_select_option import DefaultSelectOption
from .select_menu import Select

if TYPE_CHECKING:
    from typing_extensions import Self


class UserSelect(Select[UserSelectPayload]):
    """Represents a user select menu from the Discord Bot UI Kit.

    This inherits from :class:`SelectMenu`.

    .. versionadded:: 3.0

    Attributes
    ----------
    type: Literal[:data:`ComponentType.user_select`]
        The type of component.
    default_values: List[:class:`DefaultSelectOption`]
        The default selected values of the select menu.
    custom_id: :class:`str`
        The custom ID of the select menu that gets received during an interaction.
    placeholder: :class:`str` | :data:`None`
        The placeholder text that is shown if nothing is selected, if any.
    min_values: :class:`int`
        The minimum number of values that must be selected.
    max_values: :class:`int`
        The maximum number of values that can be selected.
    disabled: :class:`bool`
        Whether the select menu is disabled or not.
    id: :class:`int` | :data:`None`
        The user select menu's ID.
    required: :class:`bool`
        Whether the user select is required or not.
        Only applicable when used in a :class:`discord.Modal`.

    Parameters
    ----------
    default_values:
        The default selected values of the select menu.
    custom_id:
        The custom ID of the select menu that gets received during an interaction.
    options:
        The options available in this select menu.
    placeholder:
        The placeholder text that is shown if nothing is selected, if any.
    min_values:
        The minimum number of values that must be selected.
        Defaults to 1.
    max_values:
        The maximum number of values that can be selected.
        Defaults to 1.
    disabled:
        Whether the select menu is disabled or not. Defaults to ``False``.
    id:
        The user select menu's ID. If not provided, it is set sequentially by Discord.
        The ID `0` is treated as if no ID was provided.
    required:
        Whether the user select is required or not. Defaults to `True`.
        Only applicable when used in a :class:`discord.Modal`.
    """

    __slots__: tuple[str, ...] = ("default_values",)
    type: Literal[ComponentType.user_select] = ComponentType.user_select  # pyright: ignore[reportIncompatibleVariableOverride]

    def __init__(
        self,
        *,
        default_values: Sequence[DefaultSelectOption[Literal["user"]]] | None = None,
        custom_id: str,
        placeholder: str | None = None,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False,
        id: int | None = None,
        required: bool = True,
    ):
        super().__init__(
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            id=id,
        )
        self.default_values: list[DefaultSelectOption[Literal["user"]]] = (
            list(default_values) if default_values is not None else []
        )

    @classmethod
    @override
    def from_payload(cls, payload: UserSelectPayload) -> Self:
        default_values: list[DefaultSelectOption[Literal["user"]]] = [
            DefaultSelectOption.from_payload(value) for value in payload.get("default_values", [])
        ]
        return cls(
            custom_id=payload["custom_id"],
            placeholder=payload.get("placeholder"),
            min_values=payload.get("min_values", 1),
            max_values=payload.get("max_values", 1),
            disabled=payload.get("disabled", False),
            id=payload.get("id"),
            default_values=default_values,
        )

    @override
    def to_dict(self, modal: bool = False) -> UserSelectPayload:
        payload: UserSelectPayload = {  # pyright: ignore[reportAssignmentType]
            "type": int(self.type),
            "id": self.id,
            "custom_id": self.custom_id,
            "min_values": self.min_values,
            "max_values": self.max_values,
        }
        if self.placeholder:
            payload["placeholder"] = self.placeholder

        if self.disabled and not modal:
            payload["disabled"] = self.disabled

        if self.default_values:
            payload["default_values"] = [value.to_dict() for value in self.default_values]

        return payload
