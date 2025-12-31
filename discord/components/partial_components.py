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

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Generic, Literal, TypeAlias, cast

from typing_extensions import TypeVar, override

from ..enums import ComponentType, try_enum
from ..types.partial_components import PartialButton as PartialButtonPayload
from ..types.partial_components import PartialChannelSelectMenu as PartialChannelSelectPayload
from ..types.partial_components import PartialComponent as PartialComponentPayload
from ..types.partial_components import PartialFileUpload as PartialFileUploadPayload
from ..types.partial_components import PartialLabel as PartialLabelPayload
from ..types.partial_components import PartialMentionableSelectMenu as PartialMentionableSelectPayload
from ..types.partial_components import PartialRoleSelectMenu as PartialRoleSelectPayload
from ..types.partial_components import PartialStringSelectMenu as PartialStringSelectPayload
from ..types.partial_components import PartialTextDisplay as PartialTextDisplayPayload
from ..types.partial_components import PartialTextInput as PartialTextInputPayload
from ..types.partial_components import PartialUserSelectMenu as PartialUserSelectPayload

if TYPE_CHECKING:
    from typing_extensions import Self

    from .type_aliases import AnyPartialComponent

AllowedPartialLabelComponents: TypeAlias = "PartialStringSelect | PartialUserSelect | PartialChannelSelect | PartialRoleSelect | PartialMentionableSelect | PartialTextInput | PartialFileUpload"

# Below, the usage of field with kw_only=True is used to push the attribute at the end of the __init__ signature and
# avoid issues with optional arguments order during class inheritance.
# Reference: https://stackoverflow.com/questions/51575931/class-inheritance-in-python-3-7-dataclasses


T = TypeVar("T", bound="ComponentType")
P = TypeVar("P", bound="PartialComponentPayload")


@dataclass
class PartialComponent(ABC, Generic[T, P]):
    """Base class for all partial components returned by Discord during an :class:`Interaction` of type :data:`InteractionType.modal_submit`.

    .. versionadded:: 3.0
    """

    id: int
    type: T

    @classmethod
    @abstractmethod
    def from_payload(cls, payload: P) -> Self: ...


C = TypeVar("C", bound="AnyPartialComponent", covariant=True)


class PartialWalkableComponentMixin(ABC, Generic[C]):
    @abstractmethod
    def walk_components(self) -> Iterator[C]: ...

    if TYPE_CHECKING:
        __iter__: Iterator[C]
    else:

        def __iter__(self) -> Iterator[C]:
            yield from self.walk_components()

    def get_by_id(self, component_id: str | int) -> C | None:
        for component in self.walk_components():
            if isinstance(component_id, str) and getattr(component, "custom_id", None) == component_id:
                return component
            elif isinstance(component_id, int) and getattr(component, "id", None) == component_id:
                return component
        return None


V = TypeVar("V", bound="str | int")


@dataclass
class PartialButton(PartialComponent[Literal[ComponentType.button], PartialButtonPayload]):
    """Represents a :class:`Button` component as returned by Discord during a :class:`Interaction` of type :data:`InteractionType.modal_submit`.

    .. versionadded:: 3.0

    Attributes
    ----------
    type: Literal[:data:`ComponentType.button`]
        The type of component.
    id: :class:`int`
        The ID of this button component.
    custom_id: :class:`str` | :class:`None`
        The custom ID of this button component. This can be ``None`` for link buttons.
    """

    id: int
    custom_id: str | None
    type: Literal[ComponentType.button] = field(default=ComponentType.button, kw_only=True)

    @classmethod
    @override
    def from_payload(cls, payload: PartialButtonPayload) -> Self:
        return cls(id=payload["id"], custom_id=payload.get("custom_id"))


@dataclass
class PartialSelect(PartialComponent[T, P], ABC, Generic[T, V, P]):
    """Base class for all select menu interaction components returned by Discord during an :class:`Interaction` of type :data:`InteractionType.modal_submit`.

    .. versionadded:: 3.0
    """

    id: int
    custom_id: str
    values: list[V]
    type: T


@dataclass
class PartialStringSelect(PartialSelect[Literal[ComponentType.string_select], str, PartialStringSelectPayload]):
    """Represents a :class:`StringSelect` component as returned by Discord during a :class:`Interaction` of type :data:`InteractionType.modal_submit`.

    .. versionadded:: 3.0

    Attributes
    ----------
    type: Literal[:data:`ComponentType.string_select`]
        The type of component.
    values: :class:`list` of :class:`str`
        The values selected in the string select menu.
    id: :class:`int`
        The ID of this string select menu component.
    custom_id: :class:`str`
        The custom ID of this string select menu component.
    """

    type: Literal[ComponentType.string_select] = field(default=ComponentType.string_select, kw_only=True)

    @classmethod
    @override
    def from_payload(cls, payload: PartialStringSelectPayload) -> Self:
        return cls(
            id=payload["id"],
            custom_id=payload["custom_id"],
            values=payload["values"],
        )


P_int_select = TypeVar(
    "P_int_select",
    bound=PartialUserSelectPayload
    | PartialRoleSelectPayload
    | PartialChannelSelectPayload
    | PartialMentionableSelectPayload,
)


@dataclass
class PartialSnowflakeSelect(PartialSelect[T, int, P_int_select], ABC, Generic[T, P_int_select]):
    type: T

    @classmethod
    @override
    def from_payload(cls, payload: P_int_select) -> Self:
        return cls(  # pyright: ignore[reportCallIssue]
            id=payload["id"],
            custom_id=payload["custom_id"],
            values=[int(value) for value in payload["values"]],
        )


@dataclass
class PartialUserSelect(PartialSnowflakeSelect[Literal[ComponentType.user_select], PartialUserSelectPayload]):
    """Represents a :class:`UserSelect` component as returned by Discord during a :class:`Interaction` of type :data:`InteractionType.modal_submit`.

    .. versionadded:: 3.0

    Attributes
    ----------
    type: Literal[:data:`ComponentType.user_select`]
        The type of component.
    values: :class:`list` of :class:`int`
        The user IDs selected in the user select menu.
    id: :class:`int`
        The ID of this user select menu component.
    custom_id: :class:`str`
        The custom ID of this user select menu component.
    """

    type: Literal[ComponentType.user_select] = field(default=ComponentType.user_select, kw_only=True)


@dataclass
class PartialRoleSelect(PartialSnowflakeSelect[Literal[ComponentType.role_select], PartialRoleSelectPayload]):
    """Represents a :class:`RoleSelect` component as returned by Discord during a :class:`Interaction` of type :data:`InteractionType.modal_submit`.

    .. versionadded:: 3.0

    Attributes
    ----------
    type: Literal[:data:`ComponentType.role_select`]
        The type of component.
    values: :class:`list` of :class:`int`
        The role IDs selected in the role select menu.
    id: :class:`int`
        The ID of this role select menu component.
    custom_id: :class:`str`
        The custom ID of this role select menu component.
    """

    type: Literal[ComponentType.role_select] = field(default=ComponentType.role_select, kw_only=True)


@dataclass
class PartialChannelSelect(PartialSnowflakeSelect[Literal[ComponentType.channel_select], PartialChannelSelectPayload]):
    """Represents a :class:`ChannelSelect` component as returned by Discord during a :class:`Interaction` of type :data:`InteractionType.modal_submit`.

    .. versionadded:: 3.0

    Attributes
    ----------
    type: Literal[:data:`ComponentType.channel_select`]
        The type of component.
    values: :class:`list` of :class:`int`
        The channel IDs selected in the channel select menu.
    id: :class:`int`
        The ID of this channel select menu component.
    custom_id: :class:`str`
        The custom ID of this channel select menu component.
    """

    type: Literal[ComponentType.channel_select] = field(default=ComponentType.channel_select, kw_only=True)


@dataclass
class PartialMentionableSelect(
    PartialSnowflakeSelect[Literal[ComponentType.mentionable_select], PartialMentionableSelectPayload]
):
    """Represents a :class:`MentionableSelect` component as returned by Discord during a :class:`Interaction` of type :data:`InteractionType.modal_submit`.

    .. versionadded:: 3.0

    Attributes
    ----------
    type: Literal[:data:`ComponentType.mentionable_select`]
        The type of component.
    values: :class:`list` of :class:`int`
        The IDs selected in the mentionable select menu.
    id: :class:`int`
        The ID of this mentionable select menu component.
    custom_id: :class:`str`
        The custom ID of this mentionable select menu component.
    """

    type: Literal[ComponentType.mentionable_select] = field(default=ComponentType.mentionable_select, kw_only=True)


@dataclass
class PartialTextInput(PartialComponent[Literal[ComponentType.text_input], PartialTextInputPayload]):
    """Represents a :class:`TextInput` component as returned by Discord during a :class:`Interaction` of type :data:`InteractionType.modal_submit`.

    .. versionadded:: 3.0

    Attributes
    ----------
    type: Literal[:data:`ComponentType.text_input`]
        The type of component.
    value: :class:`str`
        The value of the text input.
    id: :class:`int`
        The ID of this text input component.
    custom_id: :class:`str`
        The custom ID of this text input component.
    """

    id: int
    custom_id: str
    value: str
    type: Literal[ComponentType.text_input] = field(default=ComponentType.text_input, kw_only=True)

    @classmethod
    @override
    def from_payload(cls, payload: PartialTextInputPayload) -> Self:
        return cls(id=payload["id"], custom_id=payload["custom_id"], value=payload["value"])


L_c = TypeVar("L_c", bound=AllowedPartialLabelComponents, default=AllowedPartialLabelComponents)


@dataclass
class PartialLabel(
    PartialComponent[Literal[ComponentType.label], PartialLabelPayload],
    PartialWalkableComponentMixin[AllowedPartialLabelComponents],
    Generic[L_c],
):
    """Represents a :class:`Label` component as returned by Discord during a :class:`Interaction` of type :data:`InteractionType.modal_submit`.

    This is a component used exclusively within a :class:`Modal` to hold other components.

    .. versionadded:: 3.0

    Attributes
    ----------
    type: Literal[:data:`ComponentType.label`]
        The type of component.
    component: :class:`PartialTextInput` | :class:`PartialStringSelect`
        The component contained in this label.
    id: :class:`int`
        The ID of this label component.
    """

    id: int
    component: L_c
    type: Literal[ComponentType.label] = field(default=ComponentType.label, kw_only=True)

    @classmethod
    @override
    def from_payload(cls, payload: PartialLabelPayload) -> Self:
        return cls(
            id=payload["id"],
            component=cast("AllowedPartialLabelComponents", _partial_component_factory(payload["component"])),
        )

    @override
    def walk_components(self) -> Iterator[AllowedPartialLabelComponents]:
        yield self.component
        if isinstance(self.component, PartialWalkableComponentMixin):
            yield from self.component.walk_components()  # pyright: ignore[reportReturnType]


@dataclass
class PartialTextDisplay(PartialComponent[Literal[ComponentType.text_display], PartialTextDisplayPayload]):
    """Represents a :class:`TextDisplay` component as returned by Discord during a :class:`Interaction` of type :data:`InteractionType.modal_submit`.

    .. versionadded:: 3.0

    Attributes
    ----------
    type: Literal[:data:`ComponentType.text_display`]
        The type of component.
    id: :class:`int`
        The ID of this text display component.
    """

    id: int
    type: Literal[ComponentType.text_display] = field(default=ComponentType.text_display, kw_only=True)

    @classmethod
    @override
    def from_payload(cls, payload: PartialTextDisplayPayload) -> Self:
        return cls(id=payload["id"])


@dataclass
class PartialFileUpload(PartialComponent[Literal[ComponentType.file_upload], PartialFileUploadPayload]):
    """Represents a :class:`TextDisplay` component as returned by Discord during a :class:`Interaction` of type :data:`InteractionType.modal_submit`.

    .. versionadded:: 3.0

    Attributes
    ----------
    type: Literal[:data:`ComponentType.file_upload`]
        The type of component.
    id: :class:`int`
        The ID of this file upload component.
    custom_id: :class:`str`
        The custom ID of this file upload component.
    values: :class:`list` of :class:`int`
        The attachment IDs uploaded in the file upload component.
    """

    id: int
    custom_id: str
    values: list[int]
    type: Literal[ComponentType.file_upload] = field(default=ComponentType.file_upload, kw_only=True)

    @classmethod
    @override
    def from_payload(cls, payload: PartialFileUploadPayload) -> Self:
        return cls(id=payload["id"], custom_id=payload["custom_id"], values=[int(value) for value in payload["values"]])


@dataclass
class UnknownPartialComponent(PartialComponent[ComponentType, PartialComponentPayload]):
    """A class representing an unknown interaction component.

    This class is used when an interaction component with an unrecognized type is encountered.

    Attributes
    ----------
    type: :class:`int`
        The type of the unknown component.
    id: :class:`int`
        The ID of the unknown component.
    payload: dict[str, Any]
        The original raw payload of the unknown component.
    """

    type: ComponentType
    id: int
    payload: dict[str, Any]  # pyright: ignore[reportExplicitAny]

    @classmethod
    @override
    def from_payload(cls, payload: PartialComponentPayload) -> Self:
        return cls(
            id=payload["id"],
            type=try_enum(ComponentType, payload["type"]),
            payload=payload,  # pyright: ignore[reportArgumentType]
        )


COMPONENT_MAPPINGS = {
    2: PartialButton,
    3: PartialStringSelect,
    4: PartialTextInput,
    5: PartialUserSelect,
    6: PartialRoleSelect,
    7: PartialMentionableSelect,
    8: PartialChannelSelect,
    10: PartialTextDisplay,
    18: PartialLabel,
    19: PartialFileUpload,
}


def _partial_component_factory(payload: PartialComponentPayload, key: str = "type") -> AnyPartialComponent:
    component_type: int = cast("int", payload[key])
    component_class = COMPONENT_MAPPINGS.get(component_type, UnknownPartialComponent)
    return component_class.from_payload(payload)  # pyright: ignore[reportArgumentType]
