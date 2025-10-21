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

from collections.abc import Iterator
from typing import TYPE_CHECKING, ClassVar, Literal, TypeAlias, cast

from typing_extensions import override

from ..enums import ComponentType
from ..types.component_types import LabelComponent as LabelComponentPayload
from .component import Component, ModalComponentMixin, WalkableComponentMixin

if TYPE_CHECKING:
    from typing_extensions import Self

    from discord.state import ConnectionState

    from .channel_select_menu import ChannelSelect
    from .file_upload import FileUpload
    from .mentionable_select_menu import MentionableSelect
    from .string_select_menu import StringSelect
    from .text_input import TextInput
    from .user_select_menu import UserSelect

    AllowedLabelComponents: TypeAlias = (
        StringSelect | UserSelect | TextInput | FileUpload | MentionableSelect | ChannelSelect
    )


class Label(
    Component["LabelComponentPayload"],
    WalkableComponentMixin["AllowedLabelComponents"],
    ModalComponentMixin["LabelComponentPayload"],
):
    """Represents a Label component.

    This is a component used exclusively within a :class:`Modal` to hold :class:`InputText` components.

    This inherits from :class:`Component`.

    .. versionadded:: 3.0

    Attributes
    ----------
    type: Literal[:data:`ComponentType.label`]
        The type of component.
    component: :class:`list` of :class:`Component`
        The components contained in this label.
    label: :class:`str`
        The text of the label.
    description: :class:`str` | :data:`None`
        The description of the label.
    id: :class:`int` | :data:`None`
        The label's ID.

    Parameters
    ----------
    component:
        The component held by this label. Currently supports :class:`TextDisplay` and :class:`StringSelect`.
    label:
        The text of the label.
    description:
        The description of the label. This is optional.
    id:
        The label's ID. If not provided, it is set sequentially by Discord.
        The ID `0` is treated as if no ID was provided.
    """

    __slots__: tuple[str, ...] = ("label", "description", "component")  # pyright: ignore[reportIncompatibleUnannotatedOverride]

    __repr_info__: ClassVar[tuple[str, ...]] = __slots__
    versions: tuple[int, ...] = (2,)
    type: Literal[ComponentType.label] = ComponentType.label  # pyright: ignore[reportIncompatibleVariableOverride]

    def __init__(
        self,
        component: AllowedLabelComponents,
        label: str,
        description: str | None = None,
        id: int | None = None,
    ):
        self.label: str = label
        self.description: str | None = description
        self.component: AllowedLabelComponents = component
        super().__init__(id=id)

    @classmethod
    @override
    def from_payload(cls, payload: LabelComponentPayload, state: ConnectionState | None = None) -> Self:
        from ._component_factory import _component_factory  # noqa: PLC0415  # pyright: ignore[reportPrivateUsage]

        # self.id: int = data.get("id")
        component: AllowedLabelComponents = cast(
            "AllowedLabelComponents", _component_factory(payload["component"], state=state)
        )
        return cls(
            component=component,
            label=payload["label"],
            description=payload.get("description"),
            id=payload.get("id"),
        )

    @override
    def to_dict(self, modal: bool = True) -> LabelComponentPayload:
        payload: LabelComponentPayload = {  # pyright: ignore[reportAssignmentType]
            "type": int(self.type),
            "id": self.id,
            "component": self.component.to_dict(modal=modal),
            "label": self.label,
        }
        if self.description:
            payload["description"] = self.description
        return payload

    @override
    def walk_components(self) -> Iterator[AllowedLabelComponents]:
        yield self.component
