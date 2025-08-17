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

from typing import (
    TYPE_CHECKING,
    cast,
    ClassVar,
    TypeVar,
    Generic,
    TypeAlias,
    Literal,
    overload,
)
from collections.abc import Iterator, Sequence
from typing_extensions import override
from abc import ABC, abstractmethod


from .asset import AssetMixin
from .colour import Colour
from .enums import (
    ButtonStyle,
    ComponentType,
    InputTextStyle,
    SeparatorSpacingSize,
    try_enum,
)
from .flags import AttachmentFlags
from .partial_emoji import PartialEmoji, _EmojiTag  # pyright: ignore[reportPrivateUsage]
from .utils import MISSING, Undefined
from .types.components import ActionRow as ActionRowPayload
from .types.components import ButtonComponent as ButtonComponentPayload
from .types.components import Component as ComponentPayload
from .types.components import ContainerComponent as ContainerComponentPayload
from .types.components import FileComponent as FileComponentPayload
from .types.components import InputText as InputTextComponentPayload
from .types.components import MediaGalleryComponent as MediaGalleryComponentPayload
from .types.components import MediaGalleryItem as MediaGalleryItemPayload
from .types.components import SectionComponent as SectionComponentPayload
from .types.components import StringSelect as StringSelectPayload
from .types.components import ChannelSelect as ChannelSelectPayload
from .types.components import RoleSelect as RoleSelectPayload
from .types.components import MentionableSelect as MentionableSelectPayload
from .types.components import UserSelect as UserSelectPayload
from .types.components import SelectOption as SelectOptionPayload
from .types.components import SeparatorComponent as SeparatorComponentPayload
from .types.components import TextDisplayComponent as TextDisplayComponentPayload
from .types.components import ThumbnailComponent as ThumbnailComponentPayload
from .types.components import UnfurledMediaItem as UnfurledMediaItemPayload
from .types.components import SelectDefaultValue

if TYPE_CHECKING:
    from .state import ConnectionState
    from typing_extensions import Self
    from .emoji import AppEmoji, GuildEmoji

    AnyEmoji: TypeAlias = GuildEmoji | AppEmoji | PartialEmoji


__all__ = (
    "Component",
    "ActionRow",
    "Button",
    "SelectMenu",
    "SelectOption",
    "InputText",
    "Section",
    "TextDisplay",
    "Thumbnail",
    "MediaGallery",
    "MediaGalleryItem",
    "UnfurledMediaItem",
    "FileComponent",
    "Separator",
    "Container",
)


P = TypeVar("P", bound="ComponentPayload", covariant=True)
C = TypeVar("C", bound="Component[ComponentPayload]", covariant=True)


class Component(ABC, Generic[P]):
    """Represents a Discord Bot UI Kit Component.

    The components supported by Discord in messages are as follows:

    - :class:`ActionRow`
    - :class:`Button`
    - :class:`SelectMenu`
    - :class:`Section`
    - :class:`TextDisplay`
    - :class:`Thumbnail`
    - :class:`MediaGallery`
    - :class:`FileComponent`
    - :class:`Separator`
    - :class:`Container`

    This class is abstract and cannot be instantiated.

    .. versionadded:: 2.0

    Attributes
    ----------
    type: :class:`ComponentType`
        The type of component.
    id: :class:`int`
        The component's ID. If not provided by the user, it is set sequentially by Discord.
        The ID `0` is treated as if no ID was provided.
    """

    __slots__: tuple[str, ...] = ("type", "id")  # pyright: ignore[reportIncompatibleUnannotatedOverride]

    __repr_info__: ClassVar[tuple[str, ...]]
    type: ComponentType
    versions: tuple[int, ...]

    def __init__(self, id: int | None = None) -> None:
        self.id: int | None = id

    @override
    def __repr__(self) -> str:
        attrs = " ".join(f"{key}={getattr(self, key)!r}" for key in self.__repr_info__)
        return f"<{self.__class__.__name__} {attrs}>"

    @abstractmethod
    def to_dict(self) -> P: ...

    @classmethod
    @abstractmethod
    def from_payload(cls, payload: P) -> Self: ...  # pyright: ignore[reportGeneralTypeIssues]

    def is_v2(self) -> bool:
        """Whether this component was introduced in Components V2."""
        return bool(self.versions and 1 not in self.versions)

    def any_is_v2(self) -> bool:
        """Whether this component or any of its children were introduced in Components V2."""
        return self.is_v2()

    def is_dispatchable(self) -> bool:
        """Wether this component can be interacted with and lead to a :class:`Interaction`"""
        return False

    def any_is_dispatchable(self) -> bool:
        """Whether this component or any of its children can be interacted with and lead to a :class:`Interaction`"""
        return self.is_dispatchable()


class StateComponent(Component[P], ABC):
    @classmethod
    @abstractmethod
    @override
    def from_payload(cls, payload: P, state: ConnectionState | None = None) -> Self:  # pyright: ignore[reportGeneralTypeIssues]
        ...


class WalkableComponent(Component[P], ABC, Generic[P, C]):
    """A component that can be walked through.

    This is an abstract class and cannot be instantiated directly.
    It is used to represent components that can be walked through, such as :class:`ActionRow`, :class:`Container` and :class:`Section`.
    """

    __slots__: tuple[str, ...] = ("components",)  # pyright: ignore[reportIncompatibleUnannotatedOverride]
    components: list[C]

    def walk_components(self) -> Iterator[C]:
        """Walks through the components in this component."""
        for component in self.components:
            if isinstance(component, WalkableComponent):
                yield from component.walk_components()
            else:
                yield component

    @override
    def any_is_v2(self) -> bool:
        """Whether this component or any of its children were introduced in Components V2."""
        return self.is_v2() or any(c.any_is_v2() for c in self.walk_components())

    @override
    def any_is_dispatchable(self) -> bool:
        """Whether this component or any of its children can be interacted with and lead to a :class:`Interaction`"""
        return self.is_dispatchable() or any(c.any_is_dispatchable() for c in self.walk_components())


class InputText(Component[InputTextComponentPayload]):
    """Represents an Input Text field from the Discord Bot UI Kit.
    This inherits from :class:`Component`.

    Attributes
    ----------
    style: :class:`.InputTextStyle`
        The style of the input text field.
    custom_id: Optional[:class:`str`]
        The custom ID of the input text field that gets received during an interaction.
    label: :class:`str`
        The label for the input text field.
    placeholder: Optional[:class:`str`]
        The placeholder text that is shown if nothing is selected, if any.
    min_length: Optional[:class:`int`]
        The minimum number of characters that must be entered
        Defaults to 0
    max_length: Optional[:class:`int`]
        The maximum number of characters that can be entered
    required: Optional[:class:`bool`]
        Whether the input text field is required or not. Defaults to `True`.
    value: Optional[:class:`str`]
        The value that has been entered in the input text field.
    id: Optional[:class:`int`]
        The input text's ID.
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


class Button(Component[ButtonComponentPayload]):
    """Represents a button from the Discord Bot UI Kit.

    This inherits from :class:`Component`.

    .. versionadded:: 2.0

    Attributes
    ----------
    style: :class:`.ButtonStyle`
        The style of the button.
    custom_id: Optional[:class:`str`]
        The ID of the button that gets received during an interaction.
        If this button is for a URL, it does not have a custom ID.
    url: Optional[:class:`str`]
        The URL this button sends you to.
    disabled: :class:`bool`
        Whether the button is disabled or not.
    label: Optional[:class:`str`]
        The label of the button, if any.
    emoji: Optional[:class:`PartialEmoji`]
        The emoji of the button, if available.
    sku_id: Optional[:class:`int`]
        The ID of the SKU this button refers to.
    id: Optional[:class:`int`]
        The button's ID. If not provided, it is set sequentially by Discord.
        The ID `0` is treated as if no ID was provided.

    Parameters
    ----------
    style: :class:`.ButtonStyle`
        The style of the button.
    custom_id: Optional[:class:`str`]
        The ID of the button that gets received during an interaction.
        Cannot be used with :class:`ButtonStyle.url` or :class:`ButtonStyle.premium`.
    label: Optional[:class:`str`]
        The label of the button, if any.
        Cannot be used with :class:`ButtonStyle.premium`.
    emoji: Optional[:class:`str` | :class:`PartialEmoji`]
        The emoji of the button, if available.
        Cannot be used with :class:`ButtonStyle.premium`.
    disabled: :class:`bool`
        Whether the button is disabled or not.
    url: Optional[:class:`str`]
        The URL this button sends you to.
        Can only be used with :class:`ButtonStyle.url`.
    id: Optional[:class:`int`]
        The button's ID. If not provided, it is set sequentially by Discord.
        The ID `0` is treated as if no ID was provided.
    sku_id: Optional[:class:`int`]
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


class SelectOption:
    """Represents a :class:`discord.SelectMenu`'s option.

    These can be created by users.

    .. versionadded:: 2.0

    Attributes
    ----------
    label: :class:`str`
        The label of the option. This is displayed to users.
        Can only be up to 100 characters.
    value: :class:`str`
        The value of the option. This is not displayed to users.
        If not provided when constructed then it defaults to the
        label. Can only be up to 100 characters.
    description: Optional[:class:`str`]
        An additional description of the option, if any.
        Can only be up to 100 characters.
    default: :class:`bool`
        Whether this option is selected by default.
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


DT = TypeVar("DT", bound='Literal["user", "role", "channel"]')


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


SelectMenuTypes = (
    StringSelectPayload | ChannelSelectPayload | RoleSelectPayload | MentionableSelectPayload | UserSelectPayload
)

T = TypeVar(
    "T",
    bound=SelectMenuTypes,
)


class SelectMenu(Component[T], ABC, Generic[T]):
    """Represents a select menu from the Discord Bot UI Kit.

    This inherits from :class:`Component`.

    This is an abstract class and cannot be instantiated directly.

    .. versionadded:: 3.0

    """

    __slots__: tuple[str, ...] = (  # pyright: ignore[reportIncompatibleUnannotatedOverride]
        "custom_id",
        "placeholder",
        "min_values",
        "max_values",
        "disabled",
    )

    __repr_info__: ClassVar[tuple[str, ...]] = __slots__
    versions: tuple[int, ...] = (1, 2)
    type: Literal[  # pyright: ignore[reportIncompatibleVariableOverride]
        ComponentType.string_select,
        ComponentType.channel_select,
        ComponentType.role_select,
        ComponentType.mentionable_select,
        ComponentType.user_select,
    ]
    width: Literal[5] = 5

    def __init__(
        self,
        custom_id: str,
        *,
        placeholder: str | None = None,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False,
        id: int | None = None,
    ):
        self.custom_id: str = custom_id
        self.placeholder: str | None = placeholder
        self.min_values: int = min_values
        self.max_values: int = max_values
        self.disabled: bool = disabled
        super().__init__(id=id)


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


class UserSelectMenu(SelectMenu[UserSelectPayload]):
    """Represents a user select menu from the Discord Bot UI Kit.

    This inherits from :class:`SelectMenu`.

    .. versionadded:: 3.0

    Attributes
    ----------
    default_values: List[:class:`DefaultSelectOption[Literal["user"]]`]
        The default selected values of the select menu.
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
    default_values: Sequence[:class:`DefaultSelectOption[Literal["user"]]`]
        The default selected values of the select menu.
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
    def to_dict(self) -> UserSelectPayload:
        payload: UserSelectPayload = {  # pyright: ignore[reportAssignmentType]
            "type": int(self.type),
            "id": self.id,
            "custom_id": self.custom_id,
            "min_values": self.min_values,
            "max_values": self.max_values,
        }
        if self.placeholder:
            payload["placeholder"] = self.placeholder

        if self.disabled:
            payload["disabled"] = self.disabled

        if self.default_values:
            payload["default_values"] = [value.to_dict() for value in self.default_values]

        return payload


class RoleSelectMenu(SelectMenu[RoleSelectPayload]):
    """Represents a role select menu from the Discord Bot UI Kit.

    This inherits from :class:`SelectMenu`.

    .. versionadded:: 3.0

    Attributes
    ----------
    default_values: List[:class:`DefaultSelectOption[Literal["role"]]`]
        The default selected values of the select menu.
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
    default_values: Sequence[:class:`DefaultSelectOption[Literal["role"]]`]
        The default selected values of the select menu.
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
        Whether the select menu is disabled or not. Defaults to ``False``.
    id: Optional[:class:`int`]
        The select menu's ID. If not provided, it is set sequentially by Discord.
        The ID `0` is treated as if no ID was provided.
    """

    __slots__: tuple[str, ...] = ("default_values",)
    type: Literal[ComponentType.role_select] = ComponentType.role_select  # pyright: ignore[reportIncompatibleVariableOverride]

    def __init__(
        self,
        *,
        default_values: Sequence[DefaultSelectOption[Literal["role"]]] | None = None,
        custom_id: str,
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
        self.default_values: list[DefaultSelectOption[Literal["role"]]] = (
            list(default_values) if default_values is not None else []
        )

    @classmethod
    @override
    def from_payload(cls, payload: RoleSelectPayload) -> Self:
        default_values: list[DefaultSelectOption[Literal["role"]]] = [
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
    def to_dict(self) -> RoleSelectPayload:
        payload: RoleSelectPayload = {  # pyright: ignore[reportAssignmentType]
            "type": int(self.type),
            "id": self.id,
            "custom_id": self.custom_id,
            "min_values": self.min_values,
            "max_values": self.max_values,
        }
        if self.placeholder:
            payload["placeholder"] = self.placeholder

        if self.disabled:
            payload["disabled"] = self.disabled

        if self.default_values:
            payload["default_values"] = [value.to_dict() for value in self.default_values]

        return payload


class MentionableSelectMenu(SelectMenu[MentionableSelectPayload]):
    """Represents a mentionable select menu from the Discord Bot UI Kit.

    This inherits from :class:`SelectMenu`.

    .. versionadded:: 3.0

    Attributes
    ----------
    default_values: List[:class:`DefaultSelectOption[Literal["role", "user"]]`]
        The default selected values of the select menu.
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
    default_values: Sequence[:class:`DefaultSelectOption[Literal["role", "user"]]`]
        The default selected values of the select menu.
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
        Whether the select menu is disabled or not. Defaults to ``False``.
    id: Optional[:class:`int`]
        The select menu's ID. If not provided, it is set sequentially by Discord.
        The ID `0` is treated as if no ID was provided.
    """

    __slots__: tuple[str, ...] = ("default_values",)
    type: Literal[ComponentType.mentionable_select] = ComponentType.mentionable_select  # pyright: ignore[reportIncompatibleVariableOverride]

    def __init__(
        self,
        *,
        default_values: Sequence[DefaultSelectOption[Literal["role", "user"]]] | None = None,
        custom_id: str,
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
        self.default_values: list[DefaultSelectOption[Literal["role", "user"]]] = (
            list(default_values) if default_values is not None else []
        )

    @classmethod
    @override
    def from_payload(cls, payload: MentionableSelectPayload) -> Self:
        default_values: list[DefaultSelectOption[Literal["role", "user"]]] = [
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
    def to_dict(self) -> MentionableSelectPayload:
        payload: MentionableSelectPayload = {  # pyright: ignore[reportAssignmentType]
            "type": int(self.type),
            "id": self.id,
            "custom_id": self.custom_id,
            "min_values": self.min_values,
            "max_values": self.max_values,
        }
        if self.placeholder:
            payload["placeholder"] = self.placeholder

        if self.disabled:
            payload["disabled"] = self.disabled

        if self.default_values:
            payload["default_values"] = [value.to_dict() for value in self.default_values]

        return payload


class ChannelSelectMenu(SelectMenu[ChannelSelectPayload]):
    """Represents a channel select menu from the Discord Bot UI Kit.

    This inherits from :class:`SelectMenu`.

    .. versionadded:: 3.0

    Attributes
    ----------
    default_values: List[:class:`DefaultSelectOption[Literal["channel"]]`]
        The default selected values of the select menu.
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
    default_values: Sequence[:class:`DefaultSelectOption[Literal["channel"]]`]
        The default selected values of the select menu.
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
        Whether the select menu is disabled or not. Defaults to ``False``.
    id: Optional[:class:`int`]
        The select menu's ID. If not provided, it is set sequentially by Discord.
        The ID `0` is treated as if no ID was provided.
    """

    __slots__: tuple[str, ...] = ("default_values",)
    type: Literal[ComponentType.channel_select] = ComponentType.channel_select  # pyright: ignore[reportIncompatibleVariableOverride]

    def __init__(
        self,
        *,
        default_values: Sequence[DefaultSelectOption[Literal["channel"]]] | None = None,
        custom_id: str,
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
        self.default_values: list[DefaultSelectOption[Literal["channel"]]] = (
            list(default_values) if default_values is not None else []
        )

    @classmethod
    @override
    def from_payload(cls, payload: ChannelSelectPayload) -> Self:
        default_values: list[DefaultSelectOption[Literal["channel"]]] = [
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
    def to_dict(self) -> ChannelSelectPayload:
        payload: ChannelSelectPayload = {  # pyright: ignore[reportAssignmentType]
            "type": int(self.type),
            "id": self.id,
            "custom_id": self.custom_id,
            "min_values": self.min_values,
            "max_values": self.max_values,
        }
        if self.placeholder:
            payload["placeholder"] = self.placeholder

        if self.disabled:
            payload["disabled"] = self.disabled

        if self.default_values:
            payload["default_values"] = [value.to_dict() for value in self.default_values]

        return payload


class TextDisplay(Component[TextDisplayComponentPayload]):
    """Represents a Text Display from Components V2.

    This is a component that displays text.

    This inherits from :class:`Component`.

    .. versionadded:: 2.7
    .. versionchanged:: 3.0

    Attributes
    ----------
    content: :class:`str`
        The component's text content.
    id: Optional[:class:`int`]
        The component's ID. If not provided, it is set sequentially by Discord.
        The ID `0` is treated as if no ID was provided.

    Parameters
    ----------
    content: :class:`str`
        The text content of the component.
    id: Optional[:class:`int`]
        The component's ID. If not provided, it is set sequentially by Discord.
        The ID `0` is treated as if no ID was provided.
    """

    __slots__: tuple[str, ...] = ("content",)

    __repr_info__: ClassVar[tuple[str, ...]] = __slots__
    versions: tuple[int, ...] = (2,)
    type: Literal[ComponentType.text_display] = ComponentType.text_display  # pyright: ignore[reportIncompatibleVariableOverride]

    def __init__(self, content: str, id: int | None = None):
        self.content: str = content
        super().__init__(id=id)

    @classmethod
    @override
    def from_payload(cls, payload: TextDisplayComponentPayload) -> Self:
        return cls(
            content=payload["content"],
            id=payload.get("id"),
        )

    @override
    def to_dict(self) -> TextDisplayComponentPayload:
        return {"type": int(self.type), "id": self.id, "content": self.content}  # pyright: ignore[reportReturnType]


class UnfurledMediaItem(AssetMixin):
    """Represents an Unfurled Media Item used in Components V2.

    This is used as an underlying component for other media-based components such as :class:`Thumbnail`, :class:`FileComponent`, and :class:`MediaGalleryItem`.

    .. versionadded:: 2.7

    Attributes
    ----------
    url: :class:`str`
        The URL of this media item. This can either be an arbitrary URL or an ``attachment://`` URL to work with local files.
    """

    def __init__(self, url: str):
        self._state: ConnectionState | None = None
        self._url: str = url
        self.proxy_url: str | None = None
        self.height: int | None = None
        self.width: int | None = None
        self.content_type: str | None = None
        self.flags: AttachmentFlags | None = None
        self.attachment_id: int | None = None

    @property
    @override
    def url(self) -> str:  # pyright: ignore[reportIncompatibleVariableOverride]
        """Returns this media item's url."""
        return self._url

    @classmethod
    def from_dict(cls, data: UnfurledMediaItemPayload, state: ConnectionState | None = None) -> UnfurledMediaItem:
        r = cls(data.get("url"))
        r.proxy_url = data.get("proxy_url")
        r.height = data.get("height")
        r.width = data.get("width")
        r.content_type = data.get("content_type")
        r.flags = AttachmentFlags._from_value(data.get("flags", 0))  # pyright: ignore[reportPrivateUsage]
        r.attachment_id = data.get("attachment_id")  # pyright: ignore[reportAttributeAccessIssue]
        r._state = state
        return r

    def to_dict(self) -> UnfurledMediaItemPayload:
        return {"url": self.url}  # pyright: ignore[reportReturnType]


class Thumbnail(StateComponent[ThumbnailComponentPayload]):
    """Represents a Thumbnail from Components V2.

    This is a component that displays media, such as images and videos.

    This inherits from :class:`Component`.

    .. versionadded:: 2.7
    .. versionchanged:: 3.0

    Attributes
    ----------
    media: :class:`UnfurledMediaItem`
        The component's underlying media object.
    description: Optional[:class:`str`]
        The thumbnail's description, up to 1024 characters.
    spoiler: Optional[:class:`bool`]
        Whether the thumbnail has the spoiler overlay.

    Parameters
    ----------
    url: :class:`str` | :class:`UnfurledMediaItem`
        The URL of the thumbnail. This can either be an arbitrary URL or an ``attachment://`` URL to work with local files.
    id: Optional[:class:`int`]
        The thumbnail's ID. If not provided, it is set sequentially by Discord.
        The ID `0` is treated as if no ID was provided.
    description: Optional[:class:`str`]
        The thumbnail's description, up to 1024 characters.
    spoiler: Optional[:class:`bool`]
        Whether the thumbnail has the spoiler overlay. Defaults to ``False``.
    """

    __slots__: tuple[str, ...] = (
        "file",
        "description",
        "spoiler",
    )

    __repr_info__: ClassVar[tuple[str, ...]] = __slots__
    versions: tuple[int, ...] = (2,)
    type: Literal[ComponentType.thumbnail] = ComponentType.thumbnail  # pyright: ignore[reportIncompatibleVariableOverride]

    def __init__(
        self,
        url: str | UnfurledMediaItem,
        *,
        id: int | None = None,
        description: str | None = None,
        spoiler: bool | None = False,
    ):
        self.file: UnfurledMediaItem = url if isinstance(url, UnfurledMediaItem) else UnfurledMediaItem(url)
        self.description: str | None = description
        self.spoiler: bool | None = spoiler
        super().__init__(id=id)

    @property
    def url(self) -> str:
        """Returns the URL of this thumbnail's underlying media item."""
        return self.file.url

    @classmethod
    @override
    def from_payload(cls, payload: ThumbnailComponentPayload, state: ConnectionState | None = None) -> Self:
        file = UnfurledMediaItem.from_dict(payload.get("file", {}), state=state)
        return cls(
            url=file,
            id=payload.get("id"),
            description=payload.get("description"),
            spoiler=payload.get("spoiler", False),
        )

    @override
    def to_dict(self) -> ThumbnailComponentPayload:
        payload: ThumbnailComponentPayload = {"type": self.type, "id": self.id, "media": self.file.to_dict()}  # pyright: ignore[reportAssignmentType]
        if self.description:
            payload["description"] = self.description
        if self.spoiler is not None:
            payload["spoiler"] = self.spoiler
        return payload


AllowedSectionComponents: TypeAlias = TextDisplay
AllowedSectionAccessoryComponents = Button | Thumbnail


class Section(
    WalkableComponent[SectionComponentPayload, AllowedSectionComponents | AllowedSectionAccessoryComponents],
):
    """Represents a Section from Components V2.

    This is a component that groups other components together with an additional component to the right as the accessory.

    This inherits from :class:`Component`.

    .. versionadded:: 2.7

    Attributes
    ----------
    components: List[:class:`Component`]
        The components contained in this section. Currently supports :class:`TextDisplay`.
    accessory: Optional[:class:`Component`]
        The accessory attached to this Section. Currently supports :class:`Button` and :class:`Thumbnail`.

    Parameters
    ----------
    components: Sequence[:class:`AllowedSectionComponents`]
        The components contained in this section. Currently supports :class:`TextDisplay`.
    accessory: Optional[:class:`AllowedSectionAccessoryComponents`]
        The accessory attached to this Section. Currently supports :class:`Button` and :class:`Thumbnail`.
    id: Optional[:class:`int`]
        The section's ID. If not provided, it is set sequentially by Discord.
        The ID `0` is treated as if no ID was provided.
    """

    __slots__: tuple[str, ...] = ("components", "accessory")

    __repr_info__: ClassVar[tuple[str, ...]] = __slots__
    versions: tuple[int, ...] = (2,)
    type: Literal[ComponentType.section] = ComponentType.section  # pyright: ignore[reportIncompatibleVariableOverride]

    def __init__(
        self,
        components: Sequence[AllowedSectionComponents],
        accessory: AllowedSectionAccessoryComponents | None = None,
        id: int | None = None,
    ):
        self.components: list[AllowedSectionComponents] = list(components)  # pyright: ignore[reportIncompatibleVariableOverride]
        self.accessory: AllowedSectionAccessoryComponents | None = accessory
        super().__init__(id=id)

    @classmethod
    @override
    def from_payload(cls, payload: SectionComponentPayload, state: ConnectionState | None = None) -> Self:
        # self.id: int = data.get("id")
        components: list[AllowedSectionComponents] = cast(
            "list[AllowedSectionComponents]",
            [_component_factory(d, state=state) for d in payload.get("components", [])],
        )
        accessory: AllowedSectionAccessoryComponents | None = None
        if _accessory := payload.get("accessory"):
            accessory = cast("AllowedSectionAccessoryComponents", _component_factory(_accessory, state=state))
        return cls(
            components=components,
            accessory=accessory,
            id=payload.get("id"),
        )

    @override
    def to_dict(self) -> SectionComponentPayload:
        payload: SectionComponentPayload = {  # pyright: ignore[reportAssignmentType]
            "type": int(self.type),
            "id": self.id,
            "components": [c.to_dict() for c in self.components],
        }
        if self.accessory:
            payload["accessory"] = self.accessory.to_dict()
        return payload


class MediaGalleryItem:
    """Represents an item used in the :class:`MediaGallery` component.

    This is used as an underlying component for other media-based components such as :class:`Thumbnail`, :class:`FileComponent`, and :class:`MediaGalleryItem`.

    .. versionadded:: 2.7
    .. versionchanged:: 3.0

    Attributes
    ----------
    url: :class:`str`
        The URL of this gallery item. This can either be an arbitrary URL or an ``attachment://`` URL to work with local files.
    description: Optional[:class:`str`]
        The gallery item's description, up to 1024 characters.
    spoiler: Optional[:class:`bool`]
        Whether the gallery item is a spoiler.
    """

    def __init__(self, url: str, *, description: str | None = None, spoiler: bool = False):
        self._state: ConnectionState | None = None
        self.media: UnfurledMediaItem = UnfurledMediaItem(url)
        self.description: str | None = description
        self.spoiler: bool = spoiler

    @property
    def url(self) -> str:
        """Returns the URL of this gallery's underlying media item."""
        return self.media.url

    def is_dispatchable(self) -> bool:
        return False

    @classmethod
    def from_payload(cls, data: MediaGalleryItemPayload, state: ConnectionState | None = None) -> MediaGalleryItem:
        media = (umi := data.get("media")) and UnfurledMediaItem.from_dict(umi, state=state)
        description = data.get("description")
        spoiler = data.get("spoiler", False)

        r = cls(
            url=media.url,
            description=description,
            spoiler=spoiler,
        )
        r._state = state
        r.media = media
        return r

    def to_dict(self) -> MediaGalleryItemPayload:
        payload: MediaGalleryItemPayload = {"media": self.media.to_dict()}
        if self.description:
            payload["description"] = self.description
        payload["spoiler"] = self.spoiler
        return payload


class MediaGallery(StateComponent[MediaGalleryComponentPayload]):
    """Represents a Media Gallery from Components V2.

    This is a component that displays up to 10 different :class:`MediaGalleryItem` objects.

    This inherits from :class:`Component`.

    .. versionadded:: 2.7
    .. versionchanged:: 3.0

    Attributes
    ----------
    items: List[:class:`MediaGalleryItem`]
        The media this gallery contains.
    """

    __slots__: tuple[str, ...] = ("items",)

    __repr_info__: ClassVar[tuple[str, ...]] = __slots__
    versions: tuple[int, ...] = (2,)
    type: Literal[ComponentType.media_gallery] = ComponentType.media_gallery  # pyright: ignore[reportIncompatibleVariableOverride]

    def __init__(self, items: Sequence[MediaGalleryItem], id: int | None = None):
        self.items: list[MediaGalleryItem] = list(items)
        super().__init__(id=id)

    @classmethod
    @override
    def from_payload(cls, payload: MediaGalleryComponentPayload, state: ConnectionState | None = None) -> Self:
        items = [MediaGalleryItem.from_payload(d, state=state) for d in payload.get("items", [])]
        return cls(items, id=payload.get("id"))

    @override
    def to_dict(self) -> MediaGalleryComponentPayload:
        return {  # pyright: ignore[reportReturnType]
            "type": int(self.type),
            "id": self.id,
            "items": [i.to_dict() for i in self.items],
        }


class FileComponent(StateComponent[FileComponentPayload]):
    """Represents a File from Components V2.

    This component displays a downloadable file in a message.

    This inherits from :class:`Component`.

    .. versionadded:: 2.7
    .. versionchanged:: 3.0

    Attributes
    ----------
    file: :class:`UnfurledMediaItem`
        The file's media item.
    name: :class:`str`
        The file's name.
    size: :class:`int`
        The file's size in bytes.
    spoiler: Optional[:class:`bool`]
        Whether the file has the spoiler overlay.
    """

    __slots__: tuple[str, ...] = (
        "file",
        "spoiler",
        "name",
        "size",
    )

    __repr_info__: ClassVar[tuple[str, ...]] = __slots__
    versions: tuple[int, ...] = (2,)
    type: Literal[ComponentType.file] = ComponentType.file  # pyright: ignore[reportIncompatibleVariableOverride]

    def __init__(
        self,
        url: str | UnfurledMediaItem,
        *,
        spoiler: bool | None = False,
        id: int | None = None,
        size: int | None = None,
        name: str | None = None,
    ) -> None:
        self.file: UnfurledMediaItem = url if isinstance(url, UnfurledMediaItem) else UnfurledMediaItem(url)
        self.spoiler: bool | None = bool(spoiler) if spoiler is not None else None
        self.size: int | None = size
        self.name: str | None = name
        super().__init__(id=id)

    @classmethod
    @override
    def from_payload(cls, payload: FileComponentPayload, state: ConnectionState | None = None) -> Self:
        file = UnfurledMediaItem.from_dict(payload.get("file", {}), state=state)
        return cls(
            file, spoiler=payload.get("spoiler"), id=payload.get("id"), size=payload["size"], name=payload["name"]
        )

    @override
    def to_dict(self) -> FileComponentPayload:
        payload = {"type": int(self.type), "id": self.id, "file": self.file.to_dict()}
        if self.spoiler is not None:
            payload["spoiler"] = self.spoiler
        return payload  # type: ignore  # pyright: ignore[reportReturnType]

    @property
    def url(self) -> str:
        return self.file.url

    @url.setter
    def url(self, url: str) -> None:
        self.file = UnfurledMediaItem(url)


class Separator(Component[SeparatorComponentPayload]):
    """Represents a Separator from Components V2.

    This is a component that visually separates components.

    This inherits from :class:`Component`.

    .. versionadded:: 2.7
    .. versionchanged:: 3.0

    Attributes
    ----------
    divider: :class:`bool`
        Whether the separator will show a horizontal line in addition to vertical spacing.
    spacing: Optional[:class:`SeparatorSpacingSize`]
        The separator's spacing size.
    """

    __slots__: tuple[str, ...] = (
        "divider",
        "spacing",
    )

    __repr_info__: ClassVar[tuple[str, ...]] = __slots__
    versions: tuple[int, ...] = (2,)
    type: Literal[ComponentType.separator] = ComponentType.separator  # pyright: ignore[reportIncompatibleVariableOverride]

    def __init__(
        self, divider: bool = True, spacing: SeparatorSpacingSize = SeparatorSpacingSize.small, id: int | None = None
    ) -> None:
        self.divider: bool = divider
        self.spacing: SeparatorSpacingSize = spacing
        super().__init__(id=id)

    @classmethod
    @override
    def from_payload(cls, payload: SeparatorComponentPayload) -> Self:
        self = cls(
            divider=payload.get("divider", False), spacing=try_enum(SeparatorSpacingSize, payload.get("spacing", 1))
        )
        self.id = payload.get("id")
        return self

    @override
    def to_dict(self) -> SeparatorComponentPayload:
        return {  # pyright: ignore[reportReturnType]
            "type": int(self.type),
            "id": self.id,
            "divider": self.divider,
            "spacing": int(self.spacing),
        }  # type: ignore


AllowedActionRowComponents = Button | InputText | SelectMenu[SelectMenuTypes]


class ActionRow(WalkableComponent[ActionRowPayload, AllowedActionRowComponents]):
    """Represents a Discord Bot UI Kit Action Row.

    This is a component that holds up to 5 children components in a row.

    This inherits from :class:`Component`.

    .. versionadded:: 2.0
    .. versionchanged:: 3.0

    Attributes
    ----------
    type: :class:`ComponentType`
        The type of component.
    components: List[:class:`AllowedActionRowComponents`]
        The components that this ActionRow holds, if any.
    id: Optional[:class:`int`]
        The action row's ID. If not provided, it is set sequentially by Discord.
        The ID `0` is treated as if no ID was provided.

    Parameters
    ----------
    components: Sequence[:class:`AllowedActionRowComponents`]

    """

    __slots__: tuple[str, ...] = ("components",)

    __repr_info__: ClassVar[tuple[str, ...]] = __slots__
    versions: tuple[int, ...] = (1, 2)
    type: Literal[ComponentType.action_row] = ComponentType.action_row  # pyright: ignore[reportIncompatibleVariableOverride]

    def __init__(self, components: Sequence[AllowedActionRowComponents], id: int | None = None) -> None:
        self.components: list[AllowedActionRowComponents] = list(components)
        super().__init__(id=id)

    @classmethod
    @override
    def from_payload(cls, payload: ActionRowPayload) -> Self:
        components: list[AllowedActionRowComponents] = cast(
            "list[AllowedActionRowComponents]", [_component_factory(d) for d in payload.get("components", [])]
        )
        return cls(components, id=payload.get("id"))

    @property
    def width(self):
        """Return the sum of the components' widths."""
        return sum(getattr(c, "width", 0) for c in self.components)

    @override
    def to_dict(self) -> ActionRowPayload:
        return {  # pyright: ignore[reportReturnType]
            "type": int(self.type),
            "id": self.id,
            "components": [component.to_dict() for component in self.components],
        }  # type: ignore


AllowedContainerComponents = ActionRow | TextDisplay | Section | MediaGallery | Separator | FileComponent


class Container(WalkableComponent[ContainerComponentPayload, AllowedContainerComponents]):
    """Represents a Container from Components V2.

    This is a component that contains different :class:`Component` objects.
    It may only contain:

    - :class:`ActionRow`
    - :class:`TextDisplay`
    - :class:`Section`
    - :class:`MediaGallery`
    - :class:`Separator`
    - :class:`FileComponent`

    This inherits from :class:`Component`.

    .. versionadded:: 2.7
    .. versionchanged:: 3.0

    Attributes
    ----------
    components: List[:class:`Component`]
        The components contained in this container.
    accent_color: Optional[:class:`Colour`]
        The accent color of the container.
    spoiler: Optional[:class:`bool`]
        Whether the entire container has the spoiler overlay.
    """

    __slots__: tuple[str, ...] = (
        "accent_color",
        "spoiler",
        "components",
    )

    __repr_info__: ClassVar[tuple[str, ...]] = __slots__
    versions: tuple[int, ...] = (2,)
    type: Literal[ComponentType.container] = ComponentType.container  # pyright: ignore[reportIncompatibleVariableOverride]

    def __init__(
        self,
        accent_color: Colour | None = None,
        spoiler: bool | None = False,
        id: int | None = None,
        *,
        components: Sequence[AllowedContainerComponents] = (),
    ) -> None:
        self.accent_color: Colour | None = accent_color
        self.spoiler: bool | None = spoiler
        self.components: list[AllowedContainerComponents] = list(components)
        super().__init__(id=id)

    @override
    def to_dict(self) -> ContainerComponentPayload:
        payload: ContainerComponentPayload = {
            "type": int(self.type),  # pyright: ignore[reportAssignmentType]
            "id": self.id,
            "components": [c.to_dict() for c in self.components],
        }
        if self.accent_color:
            payload["accent_color"] = self.accent_color.value
        if self.spoiler is not None:
            payload["spoiler"] = self.spoiler
        return payload

    @classmethod
    @override
    def from_payload(cls, payload: ContainerComponentPayload, state: ConnectionState | None = None) -> Self:
        components: list[AllowedContainerComponents] = cast(
            "list[AllowedContainerComponents]",
            [_component_factory(d, state=state) for d in payload.get("components", [])],
        )
        accent_color = Colour(c) if (c := payload.get("accent_color") is not None) else None
        return cls(
            accent_color=accent_color,
            spoiler=payload.get("spoiler"),
            id=payload.get("id"),
            components=components,
        )


class UnknownComponent(Component[ComponentPayload]):
    """Represents an unknown component.

    This is used when the component type is not recognized by the library,
    for example if a new component is introduced by Discord.

    .. versionadded:: 3.0

    Attributes
    ----------
    type: :class:`ComponentType`
        The type of the unknown component.

    """

    __slots__: tuple[str, ...] = ("type",)

    def __init__(self, type: ComponentType, id: int | None = None) -> None:
        self.type: ComponentType = type
        super().__init__(id=id)

    @override
    def to_dict(self) -> ComponentPayload:
        return {"type": int(self.type)}  # pyright: ignore[reportReturnType]

    @classmethod
    @override
    def from_payload(cls, payload: ComponentPayload) -> Self:
        type_ = try_enum(ComponentType, payload.pop("type", 0))
        self = cls(type_, id=payload.pop("id", None))
        for key, value in payload.items():
            setattr(self, key, value)
        return self


COMPONENT_MAPPINGS = {
    1: ActionRow,
    2: Button,
    3: StringSelectMenu,
    4: InputText,
    5: UserSelectMenu,
    6: RoleSelectMenu,
    7: MentionableSelectMenu,
    8: ChannelSelectMenu,
    9: Section,
    10: TextDisplay,
    11: Thumbnail,
    12: MediaGallery,
    13: FileComponent,
    14: Separator,
    17: Container,
}

STATE_COMPONENTS = (Section, Container, Thumbnail, MediaGallery, FileComponent)


def _component_factory(data: P, state: ConnectionState | None = None) -> Component[P]:
    component_type = data["type"]
    if cls := COMPONENT_MAPPINGS.get(component_type):
        if issubclass(cls, StateComponent):
            return cls(data, state=state)  # pyright: ignore[reportCallIssue, reportReturnType]
        else:
            return cls(data)  # pyright: ignore[reportArgumentType, reportCallIssue, reportReturnType]
    else:
        return UnknownComponent.from_payload(data)  # pyright: ignore[reportReturnType]


AnyComponent = (
    ActionRow
    | Button
    | StringSelectMenu
    | InputText
    | UserSelectMenu
    | RoleSelectMenu
    | MentionableSelectMenu
    | ChannelSelectMenu
    | Section
    | TextDisplay
    | Thumbnail
    | MediaGallery
    | FileComponent
    | Separator
    | Container
    | UnknownComponent
)
