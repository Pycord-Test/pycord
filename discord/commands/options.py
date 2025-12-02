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

import inspect
import logging
import sys
import types
from collections.abc import Awaitable, Callable, Iterable
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Literal,
    Optional,
    Sequence,
    Type,
    Union,
    get_args,
    overload,
)

from typing_extensions import TypeAlias, TypeVar, override

from discord.interactions import AutocompleteInteraction, Interaction

from ..utils.private import maybe_awaitable

if sys.version_info >= (3, 12):
    from typing import TypeAliasType
else:
    from typing_extensions import TypeAliasType

from ..abc import Mentionable
from ..channel import (
    BaseChannel,
    CategoryChannel,
    DMChannel,
    ForumChannel,
    GuildChannel,
    MediaChannel,
    StageChannel,
    TextChannel,
    Thread,
    VoiceChannel,
)
from ..commands import ApplicationContext, AutocompleteContext
from ..enums import ChannelType, SlashCommandOptionType
from ..enums import Enum as DiscordEnum
from ..utils import MISSING, Undefined, basic_autocomplete

if TYPE_CHECKING:
    from ..cog import Cog
    from ..ext.commands import Converter
    from ..member import Member
    from ..message import Attachment
    from ..role import Role
    from ..user import User

    InputType = (
        type[
            str | bool | int | float | GuildChannel | Thread | Member | User | Attachment | Role | Mentionable
            #            | Converter
        ]
        | SlashCommandOptionType
        #        | Converter
    )

    AutocompleteReturnType = Iterable["OptionChoice"] | Iterable[str] | Iterable[int] | Iterable[float]
    AR_T = TypeVar("AR_T", bound=AutocompleteReturnType)
    MaybeAwaitable = AR_T | Awaitable[AR_T]
    AutocompleteFunction: TypeAlias = (
        Callable[[AutocompleteInteraction], MaybeAwaitable[AutocompleteReturnType]]
        | Callable[[Any, AutocompleteInteraction], MaybeAwaitable[AutocompleteReturnType]]
        | Callable[
            [AutocompleteInteraction, Any],
            MaybeAwaitable[AutocompleteReturnType],
        ]
        | Callable[
            [Any, AutocompleteInteraction, Any],
            MaybeAwaitable[AutocompleteReturnType],
        ]
    )


__all__ = (
    "ThreadOption",
    "Option",
    "OptionChoice",
)

CHANNEL_TYPE_MAP = {
    TextChannel: ChannelType.text,
    VoiceChannel: ChannelType.voice,
    StageChannel: ChannelType.stage_voice,
    CategoryChannel: ChannelType.category,
    Thread: ChannelType.public_thread,
    ForumChannel: ChannelType.forum,
    MediaChannel: ChannelType.media,
    DMChannel: ChannelType.private,
}

_log = logging.getLogger(__name__)


class ThreadOption:
    """Represents a class that can be passed as the ``input_type`` for an :class:`Option` class.

    .. versionadded:: 2.0

    Parameters
    ----------
    thread_type: Literal["public", "private", "news"]
        The thread type to expect for this options input.
    """

    def __init__(self, thread_type: Literal["public", "private", "news"]):
        type_map = {
            "public": ChannelType.public_thread,
            "private": ChannelType.private_thread,
            "news": ChannelType.news_thread,
        }
        self._type = type_map[thread_type]


T = TypeVar("T", bound="str | int | float", default="str")


class ApplicationCommandOptionAutocomplete:
    def __init__(self, autocomplete_function: AutocompleteFunction) -> None:
        self.autocomplete_function: AutocompleteFunction = autocomplete_function
        self.self: Any | None = None

    async def __call__(self, interaction: AutocompleteInteraction) -> AutocompleteReturnType:
        if self.self is not None:
            return await maybe_awaitable(self.autocomplete_function(self.self, interaction))
        return await maybe_awaitable(self.autocomplete_function(interaction))


class Option(Generic[T]):  # TODO: Update docstring @Paillat-dev
    """Represents a selectable option for a slash command.

    Attributes
    ----------
    input_type: Union[Type[:class:`str`], Type[:class:`bool`], Type[:class:`int`], Type[:class:`float`], Type[:class:`.abc.GuildChannel`], Type[:class:`Thread`], Type[:class:`Member`], Type[:class:`User`], Type[:class:`Attachment`], Type[:class:`Role`], Type[:class:`.abc.Mentionable`], :class:`SlashCommandOptionType`, Type[:class:`.ext.commands.Converter`], Type[:class:`enums.Enum`], Type[:class:`Enum`]]
        The type of input that is expected for this option. This can be a :class:`SlashCommandOptionType`,
        an associated class, a channel type, a :class:`Converter`, a converter class or an :class:`enum.Enum`.
        If a :class:`enum.Enum` is used and it has up to 25 values, :attr:`choices` will be automatically filled. If the :class:`enum.Enum` has more than 25 values, :attr:`autocomplete` will be implemented with :func:`discord.utils.basic_autocomplete` instead.
    name: :class:`str`
        The name of this option visible in the UI.
        Inherits from the variable name if not provided as a parameter.
    description: Optional[:class:`str`]
        The description of this option.
        Must be 100 characters or fewer. If :attr:`input_type` is a :class:`enum.Enum` and :attr:`description` is not specified, :attr:`input_type`'s docstring will be used.
    choices: Optional[List[Union[:class:`Any`, :class:`OptionChoice`]]]
        The list of available choices for this option.
        Can be a list of values or :class:`OptionChoice` objects (which represent a name:value pair).
        If provided, the input from the user must match one of the choices in the list.
    required: Optional[:class:`bool`]
        Whether this option is required.
    default: Optional[:class:`Any`]
        The default value for this option. If provided, ``required`` will be considered ``False``.
    min_value: Optional[:class:`int`]
        The minimum value that can be entered.
        Only applies to Options with an :attr:`.input_type` of :class:`int` or :class:`float`.
    max_value: Optional[:class:`int`]
        The maximum value that can be entered.
        Only applies to Options with an :attr:`.input_type` of :class:`int` or :class:`float`.
    min_length: Optional[:class:`int`]
        The minimum length of the string that can be entered. Must be between 0 and 6000 (inclusive).
        Only applies to Options with an :attr:`input_type` of :class:`str`.
    max_length: Optional[:class:`int`]
        The maximum length of the string that can be entered. Must be between 1 and 6000 (inclusive).
        Only applies to Options with an :attr:`input_type` of :class:`str`.
    channel_types: list[:class:`discord.ChannelType`] | None
        A list of channel types that can be selected in this option.
        Only applies to Options with an :attr:`input_type` of :class:`discord.SlashCommandOptionType.channel`.
        If this argument is used, :attr:`input_type` will be ignored.
    name_localizations: Dict[:class:`str`, :class:`str`]
        The name localizations for this option. The values of this should be ``"locale": "name"``.
        See `here <https://discord.com/developers/docs/reference#locales>`_ for a list of valid locales.
    description_localizations: Dict[:class:`str`, :class:`str`]
        The description localizations for this option. The values of this should be ``"locale": "description"``.
        See `here <https://discord.com/developers/docs/reference#locales>`_ for a list of valid locales.

    Examples
    --------
    Basic usage: ::

        @bot.slash_command(guild_ids=[...])
        async def hello(
            ctx: discord.ApplicationContext,
            name: Option(str, "Enter your name"),
            age: Option(int, "Enter your age", min_value=1, max_value=99, default=18),
            # passing the default value makes an argument optional
            # you also can create optional argument using:
            # age: Option(int, "Enter your age") = 18
        ):
            await ctx.respond(f"Hello! Your name is {name} and you are {age} years old.")

    .. versionadded:: 2.0
    """

    # Overload for options with choices (str, int, or float types)
    @overload
    def __init__(
        self,
        name: str,
        input_type: type[T] = str,
        *,
        choices: Sequence[OptionChoice[T]],
        description: str | None = None,
        channel_types: None = None,
        required: bool = ...,
        default: Any | Undefined = ...,
        min_value: None = None,
        max_value: None = None,
        min_length: None = None,
        max_length: None = None,
        name_localizations: dict[str, str] | None = None,
        description_localizations: dict[str, str] | None = None,
        autocomplete: None = None,
    ) -> None: ...

    # Overload for channel options with optional channel_types filter
    @overload
    def __init__(
        self,
        name: str,
        input_type: type[GuildChannel | Thread]
        | Literal[SlashCommandOptionType.channel] = SlashCommandOptionType.channel,
        *,
        choices: None = None,
        description: str | None = None,
        channel_types: Sequence[ChannelType] | None = None,
        required: bool = ...,
        default: Any | Undefined = ...,
        min_value: None = None,
        max_value: None = None,
        min_length: None = None,
        max_length: None = None,
        name_localizations: dict[str, str] | None = None,
        description_localizations: dict[str, str] | None = None,
        autocomplete: None = None,
    ) -> None: ...

    # Overload for required string options with min_length/max_length constraints
    @overload
    def __init__(
        self,
        name: str,
        input_type: type[str] | Literal[SlashCommandOptionType.string] = str,
        *,
        description: str | None = None,
        choices: None = None,
        channel_types: None = None,
        required: Literal[True],
        default: Undefined = MISSING,
        min_length: int | None = None,
        max_length: int | None = None,
        min_value: None = None,
        max_value: None = None,
        name_localizations: dict[str, str] | None = None,
        description_localizations: dict[str, str] | None = None,
        autocomplete: None = None,
    ) -> None: ...

    # Overload for optional string options with default value and min_length/max_length constraints
    @overload
    def __init__(
        self,
        name: str,
        input_type: type[str] | Literal[SlashCommandOptionType.string] = str,
        *,
        description: str | None = None,
        choices: None = None,
        channel_types: None = None,
        required: bool = False,
        default: Any,
        min_length: int | None = None,
        max_length: int | None = None,
        min_value: None = None,
        max_value: None = None,
        name_localizations: dict[str, str] | None = None,
        description_localizations: dict[str, str] | None = None,
        autocomplete: None = None,
    ) -> None: ...

    # Overload for required integer options with min_value/max_value constraints (integers only)
    @overload
    def __init__(
        self,
        name: str,
        input_type: type[int] | Literal[SlashCommandOptionType.integer],
        *,
        description: str | None = None,
        choices: None = None,
        channel_types: None = None,
        required: Literal[True],
        default: Undefined = MISSING,
        min_value: int | None = None,
        max_value: int | None = None,
        min_length: None = None,
        max_length: None = None,
        name_localizations: dict[str, str] | None = None,
        description_localizations: dict[str, str] | None = None,
        autocomplete: None = None,
    ) -> None: ...

    # Overload for optional integer options with default value and min_value/max_value constraints (integers only)
    @overload
    def __init__(
        self,
        name: str,
        input_type: type[int] | Literal[SlashCommandOptionType.integer],
        *,
        description: str | None = None,
        choices: None = None,
        channel_types: None = None,
        required: bool = False,
        default: Any,
        min_value: int | None = None,
        max_value: int | None = None,
        min_length: None = None,
        max_length: None = None,
        name_localizations: dict[str, str] | None = None,
        description_localizations: dict[str, str] | None = None,
        autocomplete: None = None,
    ) -> None: ...

    # Overload for required float options with min_value/max_value constraints (integers or floats)
    @overload
    def __init__(
        self,
        name: str,
        input_type: type[float] | Literal[SlashCommandOptionType.number],
        *,
        description: str | None = None,
        choices: None = None,
        channel_types: None = None,
        required: Literal[True],
        default: Undefined = MISSING,
        min_value: int | float | None = None,
        max_value: int | float | None = None,
        min_length: None = None,
        max_length: None = None,
        name_localizations: dict[str, str] | None = None,
        description_localizations: dict[str, str] | None = None,
        autocomplete: None = None,
    ) -> None: ...

    # Overload for optional float options with default value and min_value/max_value constraints (integers or floats)
    @overload
    def __init__(
        self,
        name: str,
        input_type: type[float] | Literal[SlashCommandOptionType.number],
        *,
        description: str | None = None,
        choices: None = None,
        channel_types: None = None,
        required: bool = False,
        default: Any,
        min_value: int | float | None = None,
        max_value: int | float | None = None,
        min_length: None = None,
        max_length: None = None,
        name_localizations: dict[str, str] | None = None,
        description_localizations: dict[str, str] | None = None,
        autocomplete: None = None,
    ) -> None: ...

    # Overload for required options with autocomplete (no choices or min/max constraints allowed)
    @overload
    def __init__(
        self,
        name: str,
        input_type: type[str | int | float] = str,
        *,
        description: str | None = None,
        choices: None = None,
        channel_types: None = None,
        required: Literal[True],
        default: Undefined = MISSING,
        min_value: None = None,
        max_value: None = None,
        min_length: None = None,
        max_length: None = None,
        autocomplete: ApplicationCommandOptionAutocomplete,
        name_localizations: dict[str, str] | None = None,
        description_localizations: dict[str, str] | None = None,
    ) -> None: ...

    # Overload for optional options with autocomplete and default value (no choices or min/max constraints allowed)
    @overload
    def __init__(
        self,
        name: str,
        input_type: type[str | int | float] = str,
        *,
        description: str | None = None,
        choices: None = None,
        channel_types: None = None,
        required: bool = False,
        default: Any,
        min_value: None = None,
        max_value: None = None,
        min_length: None = None,
        max_length: None = None,
        autocomplete: ApplicationCommandOptionAutocomplete,
        name_localizations: dict[str, str] | None = None,
        description_localizations: dict[str, str] | None = None,
    ) -> None: ...

    # Overload for required options of other types (bool, User, Member, Role, Attachment, Mentionable, etc.)
    @overload
    def __init__(
        self,
        name: str,
        input_type: type[T] = str,
        *,
        description: str | None = None,
        choices: None = None,
        channel_types: None = None,
        required: Literal[True],
        default: Undefined = MISSING,
        min_value: None = None,
        max_value: None = None,
        min_length: None = None,
        max_length: None = None,
        name_localizations: dict[str, str] | None = None,
        description_localizations: dict[str, str] | None = None,
        autocomplete: None = None,
    ) -> None: ...

    # Overload for optional options of other types with default value (bool, User, Member, Role, Attachment, Mentionable, etc.)
    @overload
    def __init__(
        self,
        name: str,
        input_type: type[T] = str,
        *,
        description: str | None = None,
        choices: None = None,
        channel_types: None = None,
        required: bool = False,
        default: Any,
        min_value: None = None,
        max_value: None = None,
        min_length: None = None,
        max_length: None = None,
        name_localizations: dict[str, str] | None = None,
        description_localizations: dict[str, str] | None = None,
        autocomplete: None = None,
    ) -> None: ...

    def __init__(
        self,
        name: str,
        input_type: InputType | type[T] = str,
        *,
        description: str | None = None,
        choices: Sequence[OptionChoice[T]] | None = None,
        channel_types: Sequence[ChannelType] | None = None,
        required: bool = True,
        default: Any | Undefined = MISSING,
        min_value: int | float | None = None,
        max_value: int | float | None = None,
        min_length: int | None = None,
        max_length: int | None = None,
        name_localizations: dict[str, str] | None = None,
        description_localizations: dict[str, str] | None = None,
        autocomplete: ApplicationCommandOptionAutocomplete | None = None,
    ) -> None:
        self.name: str = name

        self.description: str | None = description

        self.choices: list[OptionChoice[T]] | None = list(choices) if choices is not None else None
        if self.choices is not None:
            if len(self.choices) > 25:
                raise ValueError("Option choices cannot exceed 25 items.")
            if not issubclass(input_type, str | int | float):
                raise TypeError("Option choices can only be used with str, int, or float input types.")

        self.channel_types: list[ChannelType] | None = list(channel_types) if channel_types is not None else None

        self.input_type: SlashCommandOptionType

        if isinstance(input_type, SlashCommandOptionType):
            self.input_type = input_type
        elif issubclass(input_type, str):
            self.input_type = SlashCommandOptionType.string
        elif issubclass(input_type, bool):
            self.input_type = SlashCommandOptionType.boolean
        elif issubclass(input_type, int):
            self.input_type = SlashCommandOptionType.integer
        elif issubclass(input_type, float):
            self.input_type = SlashCommandOptionType.number
        elif issubclass(input_type, Attachment):
            self.input_type = SlashCommandOptionType.attachment
        elif issubclass(input_type, User | Member):
            self.input_type = SlashCommandOptionType.user
        elif issubclass(input_type, Role):
            self.input_type = SlashCommandOptionType.role
        elif issubclass(input_type, GuildChannel | Thread):
            self.input_type = SlashCommandOptionType.channel
        elif issubclass(input_type, Mentionable):
            self.input_type = SlashCommandOptionType.mentionable

        self.required: bool = required if default is MISSING else False
        self.default: Any | Undefined = default

        self.autocomplete: ApplicationCommandOptionAutocomplete | None = autocomplete

        self.min_value: int | float | None = min_value
        self.max_value: int | float | None = max_value
        if self.input_type not in (SlashCommandOptionType.integer, SlashCommandOptionType.number) and (
            self.min_value is not None or self.max_value is not None
        ):
            raise TypeError(
                f"min_value and max_value can only be used with int or float input types, not {self.input_type.name}"
            )
        if self.input_type is not SlashCommandOptionType.integer and (
            isinstance(self.min_value, float) or isinstance(self.max_value, float)
        ):
            raise TypeError("min_value and max_value must be integers when input_type is integer")

        self.min_length: int | None = min_length
        self.max_length: int | None = max_length
        if self.input_type is not SlashCommandOptionType.string and (
            self.min_length is not None or self.max_length is not None
        ):
            raise TypeError(
                f"min_length and max_length can only be used with str input type, not {self.input_type.name}"
            )

        self.name_localizations: dict[str, str] | None = name_localizations
        self.description_localizations: dict[str, str] | None = description_localizations

    def to_dict(self) -> dict[str, Any]:
        as_dict: dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "type": self.input_type.value,
            "required": self.required,
            "autocomplete": bool(self.autocomplete),
        }
        if self.choices:
            as_dict["choices"] = [choice.to_dict() for choice in self.choices]
        if self.name_localizations:
            as_dict["name_localizations"] = self.name_localizations
        if self.description_localizations:
            as_dict["description_localizations"] = self.description_localizations
        if self.channel_types:
            as_dict["channel_types"] = [t.value for t in self.channel_types]
        if self.min_value is not None:
            as_dict["min_value"] = self.min_value
        if self.max_value is not None:
            as_dict["max_value"] = self.max_value
        if self.min_length is not None:
            as_dict["min_length"] = self.min_length
        if self.max_length is not None:
            as_dict["max_length"] = self.max_length

        return as_dict

    @override
    def __repr__(self):
        return f"<Option name={self.name!r} input_type={self.input_type} required={self.required}>"


class OptionChoice(Generic[T]):
    """
    Represents a name:value pairing for a selected :class:`.Option`.

    .. versionadded:: 2.0

    Attributes
    ----------
    name: :class:`str`
        The name of the choice. Shown in the UI when selecting an option.
    value: :class:`str` | :class:`int` | :class:`float`
        The value of the choice. If not provided, will use the value of ``name``.
    name_localizations: dict[:class:`str`, :class:`str`]
        The name localizations for this choice. The values of this should be ``"locale": "name"``.
        See `here <https://discord.com/developers/docs/reference#locales>`_ for a list of valid locales.
    """

    def __init__(
        self,
        name: str,
        value: T | None = None,
        name_localizations: dict[str, str] | None = None,
    ):
        self.name: str = str(name)
        self.value: T = value if value is not None else name  # pyright: ignore [reportAttributeAccessIssue]
        self.name_localizations: dict[str, str] | None = name_localizations

    def to_dict(self) -> dict[str, Any]:
        as_dict: dict[str, Any] = {"name": self.name, "value": self.value}
        if self.name_localizations is not None:
            as_dict["name_localizations"] = self.name_localizations

        return as_dict
