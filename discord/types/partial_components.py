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

from typing import Literal, TypeAlias

from typing_extensions import TypedDict

from .snowflake import Snowflake

ComponentType = Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17]
ButtonStyle = Literal[1, 2, 3, 4, 5, 6]
TextInputStyle = Literal[1, 2]
SeparatorSpacingSize = Literal[1, 2]


class BasePartialComponent(TypedDict):
    type: ComponentType
    id: int


class PartialButton(BasePartialComponent):
    type: Literal[2]  # pyright: ignore[reportIncompatibleVariableOverride]
    custom_id: str | None


class PartialStringSelectMenu(BasePartialComponent):
    type: Literal[3]  # pyright: ignore[reportIncompatibleVariableOverride]
    values: list[str]
    custom_id: str


class PartialUserSelectMenu(BasePartialComponent):
    type: Literal[5]  # pyright: ignore[reportIncompatibleVariableOverride]
    values: list[Snowflake]
    custom_id: str


class PartialRoleSelectMenu(BasePartialComponent):
    type: Literal[6]  # pyright: ignore[reportIncompatibleVariableOverride]
    values: list[Snowflake]
    custom_id: str


class PartialMentionableSelectMenu(BasePartialComponent):
    type: Literal[7]  # pyright: ignore[reportIncompatibleVariableOverride]
    values: list[Snowflake]
    custom_id: str


class PartialChannelSelectMenu(BasePartialComponent):
    type: Literal[8]  # pyright: ignore[reportIncompatibleVariableOverride]
    values: list[Snowflake]
    custom_id: str


class PartialTextInput(BasePartialComponent):
    type: Literal[4]  # pyright: ignore[reportIncompatibleVariableOverride]
    value: str
    custom_id: str


class PartialTextDisplay(BasePartialComponent):
    type: Literal[10]  # pyright: ignore[reportIncompatibleVariableOverride]
    value: str


class PartialFileUpload(BasePartialComponent):
    type: Literal[19]  # pyright: ignore[reportIncompatibleVariableOverride]
    values: list[Snowflake]
    custom_id: str


AllowedPartialLabelComponents: TypeAlias = "PartialStringSelectMenu | PartialTextInput | PartialFileUpload"


class PartialLabel(BasePartialComponent):
    type: Literal[18]  # pyright: ignore[reportIncompatibleVariableOverride]
    component: AllowedPartialLabelComponents


PartialComponent: TypeAlias = (
    PartialStringSelectMenu
    | PartialUserSelectMenu
    | PartialButton
    | PartialRoleSelectMenu
    | PartialMentionableSelectMenu
    | PartialChannelSelectMenu
    | PartialTextInput
    | PartialLabel
    | PartialTextDisplay
    | PartialFileUpload
)
