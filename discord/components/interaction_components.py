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
from ..types.interaction_components import InteractionButton as InteractionButtonPayload
from ..types.interaction_components import InteractionChannelSelectMenu as InteractionChannelSelectMenuPayload
from ..types.interaction_components import InteractionComponent as InteractionComponentPayload
from ..types.interaction_components import InteractionLabel as InteractionLabelPayload
from ..types.interaction_components import InteractionMentionableSelectMenu as InteractionMentionableSelectMenuPayload
from ..types.interaction_components import InteractionRoleSelectMenu as InteractionRoleSelectMenuPayload
from ..types.interaction_components import InteractionStringSelectMenu as InteractionStringSelectMenuPayload
from ..types.interaction_components import InteractionTextDisplay as InteractionTextDisplayPayload
from ..types.interaction_components import InteractionTextInput as InteractionTextInputPayload
from ..types.interaction_components import InteractionUserSelectMenu as InteractionUserSelectMenuPayload

if TYPE_CHECKING:
    from typing_extensions import Self

    from .type_aliases import AnyInteractionComponent


# Below, the usage of field with kw_only=True is used to push the attribute at the end of the __init__ signature and
# avoid issues with optional arguments order during class inheritance.
# Reference: https://stackoverflow.com/questions/51575931/class-inheritance-in-python-3-7-dataclasses


T = TypeVar("T", bound="ComponentType")
P = TypeVar("P", bound="InteractionComponentPayload")


@dataclass
class InteractionComponent(ABC, Generic[T, P]):
    """Base class for all interaction components returned by Discord during an :class:`Interaction` of type :data:`InteractionType.modal_submit`.

    .. versionadded:: 3.0
    """

    id: int
    type: T

    @classmethod
    @abstractmethod
    def from_payload(cls, payload: P) -> Self: ...


C = TypeVar("C", bound="AnyInteractionComponent", covariant=True)


class InteractionWalkableComponent(InteractionComponent[T, P], ABC, Generic[T, P, C]):
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
class InteractionButton(InteractionComponent[Literal[ComponentType.button], InteractionButtonPayload]):
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
    def from_payload(cls, payload: InteractionButtonPayload) -> Self:
        return cls(id=payload["id"], custom_id=payload.get("custom_id"))


@dataclass
class InteractionSelect(InteractionComponent[T, P], ABC, Generic[T, V, P]):
    """Base class for all select menu interaction components returned by Discord during an :class:`Interaction` of type :data:`InteractionType.modal_submit`.

    .. versionadded:: 3.0
    """

    id: int
    custom_id: str
    values: list[V]
    type: T


@dataclass
class InteractionStringSelect(
    InteractionSelect[Literal[ComponentType.string_select], str, InteractionStringSelectMenuPayload]
):
    """Represents a :class:`StringSelectMenu` component as returned by Discord during a :class:`Interaction` of type :data:`InteractionType.modal_submit`.

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
    def from_payload(cls, payload: InteractionStringSelectMenuPayload) -> Self:
        return cls(
            id=payload["id"],
            custom_id=payload["custom_id"],
            values=payload["values"],
        )


P_int_select = TypeVar(
    "P_int_select",
    bound=InteractionUserSelectMenuPayload
    | InteractionRoleSelectMenuPayload
    | InteractionChannelSelectMenuPayload
    | InteractionMentionableSelectMenuPayload,
)


@dataclass
class InteractionSnowflakeSelect(InteractionSelect[T, int, P_int_select], ABC, Generic[T, P_int_select]):
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
class InteractionUserSelect(
    InteractionSnowflakeSelect[Literal[ComponentType.user_select], InteractionUserSelectMenuPayload]
):
    """Represents a :class:`UserSelectMenu` component as returned by Discord during a :class:`Interaction` of type :data:`InteractionType.modal_submit`.

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
class InteractionRoleSelect(
    InteractionSnowflakeSelect[Literal[ComponentType.role_select], InteractionRoleSelectMenuPayload]
):
    """Represents a :class:`RoleSelectMenu` component as returned by Discord during a :class:`Interaction` of type :data:`InteractionType.modal_submit`.

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
class InteractionChannelSelect(
    InteractionSnowflakeSelect[Literal[ComponentType.channel_select], InteractionChannelSelectMenuPayload]
):
    """Represents a :class:`ChannelSelectMenu` component as returned by Discord during a :class:`Interaction` of type :data:`InteractionType.modal_submit`.

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
class InteractionMentionableSelect(
    InteractionSnowflakeSelect[Literal[ComponentType.mentionable_select], InteractionMentionableSelectMenuPayload]
):
    """Represents a :class:`MentionableSelectMenu` component as returned by Discord during a :class:`Interaction` of type :data:`InteractionType.modal_submit`.

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
class InteractionTextInput(InteractionComponent[Literal[ComponentType.text_input], InteractionTextInputPayload]):
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
    def from_payload(cls, payload: InteractionTextInputPayload) -> Self:
        return cls(id=payload["id"], custom_id=payload["custom_id"], value=payload["value"])


AllowedInteractionLabelComponents: TypeAlias = "InteractionStringSelect | InteractionUserSelect | InteractionChannelSelect | InteractionRoleSelect | InteractionMentionableSelect | InteractionTextInput"

L_c = TypeVar("L_c", bound=AllowedInteractionLabelComponents, default=AllowedInteractionLabelComponents)


@dataclass
class InteractionLabel(
    InteractionWalkableComponent[
        Literal[ComponentType.label], InteractionLabelPayload, AllowedInteractionLabelComponents
    ],
    Generic[L_c],
):
    """Represents a :class:`Label` component as returned by Discord during a :class:`Interaction` of type :data:`InteractionType.modal_submit`.

    This is a component used exclusively within a :class:`Modal` to hold other components.

    .. versionadded:: 3.0

    Attributes
    ----------
    type: Literal[:data:`ComponentType.label`]
        The type of component.
    component: :class:`InteractionTextInput` | :class:`InteractionStringSelect`
        The component contained in this label.
    id: :class:`int`
        The ID of this label component.
    """

    id: int
    component: L_c
    type: Literal[ComponentType.label] = field(default=ComponentType.label, kw_only=True)

    @classmethod
    @override
    def from_payload(cls, payload: InteractionLabelPayload) -> Self:
        return cls(
            id=payload["id"],
            component=cast("AllowedInteractionLabelComponents", _interaction_component_factory(payload["component"])),
        )

    @override
    def walk_components(self) -> Iterator[AllowedInteractionLabelComponents]:
        yield self.component
        if isinstance(self.component, InteractionWalkableComponent):
            yield from self.component.walk_components()  # pyright: ignore[reportReturnType]


@dataclass
class InteractionTextDisplay(InteractionComponent[Literal[ComponentType.text_display], InteractionTextDisplayPayload]):
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
    def from_payload(cls, payload: InteractionTextDisplayPayload) -> Self:
        return cls(id=payload["id"])


@dataclass
class UnknownInteractionComponent(InteractionComponent[ComponentType, InteractionComponentPayload]):
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
    def from_payload(cls, payload: InteractionComponentPayload) -> Self:
        return cls(
            id=payload["id"],
            type=try_enum(ComponentType, payload["type"]),
            payload=payload,  # pyright: ignore[reportArgumentType]
        )


COMPONENT_MAPPINGS = {
    2: InteractionButton,
    3: InteractionStringSelect,
    4: InteractionTextInput,
    5: InteractionUserSelect,
    6: InteractionRoleSelect,
    7: InteractionMentionableSelect,
    8: InteractionChannelSelect,
    10: InteractionTextDisplay,
    18: InteractionLabel,
}


def _interaction_component_factory(payload: InteractionComponentPayload, key: str = "type") -> AnyInteractionComponent:
    component_type: int = cast("int", payload[key])
    component_class = COMPONENT_MAPPINGS.get(component_type, UnknownInteractionComponent)
    return component_class.from_payload(payload)  # pyright: ignore[reportArgumentType]
