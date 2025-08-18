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

from typing import TYPE_CHECKING, ClassVar, Literal
from typing_extensions import override

from discord.enums import ComponentType, InputTextStyle, try_enum
from discord.types.components import InputText as InputTextComponentPayload
from .component import Component

if TYPE_CHECKING:
    from typing_extensions import Self


class InputText(Component[InputTextComponentPayload]):
    """Represents an Input Text field from the Discord Bot UI Kit.

    This inherits from :class:`Component`.

    .. versionchanged:: 3.0

    Attributes
    ----------
    type: Literal[:data:`ComponentType.input_text`]
        The type of component.
    style: :class:`InputTextStyle`
        The style of the input text field.
    custom_id: :class:`str` | :data:`None`
        The custom ID of the input text field that gets received during an interaction.
    label: :class:`str`
        The label for the input text field.
    placeholder: class:`str` | :data:`None`
        The placeholder text that is shown if nothing is selected, if any.
    min_length: :class:`int` | :data:`None`
        The minimum number of characters that must be entered
        Defaults to 0
    max_length: :class:`int` | :data:`None`
        The maximum number of characters that can be entered
    required: :class:`bool` | :data:`None`
        Whether the input text field is required or not. Defaults to `True`.
    value: :class:`str` | :data:`None`
        The value that has been entered in the input text field.
    id: :class:`int` | :data:`None`
        The input text's ID.

    Parameters
    ----------
    style: :class:`InputTextStyle`
        The style of the input text field.
    custom_id:
        The custom ID of the input text field that gets received during an interaction.
    label:
        The label for the input text field.
    min_length:
        The minimum number of characters that must be entered.
        Defaults to 0.
    max_length:
        The maximum number of characters that can be entered.
    placeholder:
        The placeholder text that is shown if nothing is selected, if any.
    required:
        Whether the input text field is required or not. Defaults to `True`.
    value:
        The value that has been entered in the input text field.
    id:
        The input text's ID. If not provided, it is set sequentially by Discord.
        The ID `0` is treated as if no ID was provided.
    """

    __slots__: tuple[str, ...] = (
        "style",
        "custom_id",
        "label",
        "placeholder",
        "min_length",
        "max_length",
        "required",
        "value",
    )

    __repr_info__: ClassVar[tuple[str, ...]] = __slots__
    versions: tuple[int, ...] = (1, 2)
    type: Literal[ComponentType.input_text] = ComponentType.input_text  # pyright: ignore[reportIncompatibleVariableOverride]

    def __init__(
        self,
        style: int | InputTextStyle,
        custom_id: str,
        label: str,
        min_lenght: int | None = None,
        max_length: int | None = None,
        placeholder: str | None = None,
        required: bool = True,
        value: str | None = None,
        id: int | None = None,
    ) -> None:
        self.style: InputTextStyle = style  # pyright: ignore[reportAttributeAccessIssue]
        self.custom_id: str = custom_id
        self.label: str = label
        self.min_length: int | None = min_lenght
        self.max_length: int | None = max_length
        self.placeholder: str | None = placeholder
        self.required: bool = required
        self.value: str | None = value
        super().__init__(id=id)

    @classmethod
    @override
    def from_payload(cls, payload: InputTextComponentPayload) -> Self:
        style = try_enum(InputTextStyle, payload["style"])
        custom_id = payload["custom_id"]
        label = payload["label"]
        min_length = payload.get("min_length")
        max_length = payload.get("max_length")
        placeholder = payload.get("placeholder")
        required = payload.get("required", True)
        value = payload.get("value")

        return cls(
            style=style,
            custom_id=custom_id,
            label=label,
            min_lenght=min_length,
            max_length=max_length,
            placeholder=placeholder,
            required=required,
            value=value,
            id=payload.get("id"),
        )

    @override
    def to_dict(self) -> InputTextComponentPayload:
        payload: InputTextComponentPayload = {  # pyright: ignore[reportAssignmentType]
            "type": int(self.type),
            "id": self.id,
            "style": self.style.value,
            "label": self.label,
        }
        if self.custom_id:
            payload["custom_id"] = self.custom_id

        if self.placeholder:
            payload["placeholder"] = self.placeholder

        if self.min_length:
            payload["min_length"] = self.min_length

        if self.max_length:
            payload["max_length"] = self.max_length

        if not self.required:
            payload["required"] = self.required

        if self.value:
            payload["value"] = self.value

        return payload  # type: ignore
