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

from typing_extensions import TypeVar

from discord.channel.base import BaseChannel, GuildChannel

if sys.version_info >= (3, 12):
    from typing import TypeAliasType
else:
    from typing_extensions import TypeAliasType

from ..abc import Mentionable
from ..channel import (
    CategoryChannel,
    DMChannel,
    ForumChannel,
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
    AR_T = TypeVar("AR_T =", bound=AutocompleteReturnType)
    MaybeAwaitable = AR_T | Awaitable[AR_T]
    AutocompleteFunction = (
        Callable[[AutocompleteContext], MaybeAwaitable[AutocompleteReturnType]]
        | Callable[[Cog, AutocompleteContext], MaybeAwaitable[AutocompleteReturnType]]
        | Callable[
            [AutocompleteContext, Any],
            MaybeAwaitable[AutocompleteReturnType],
        ]
        | Callable[
            [Cog, AutocompleteContext, Any],
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


class Option(Generic[T]):
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

    @overload
    def __init__(
        self,
        name: str,
        input_type: type[T] = str,
        *,
        choices: OptionChoice[T],
        description: str | None = None,
        channel_types: None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        name: str,
        input_type: Literal[SlashCommandOptionType.channel] = SlashCommandOptionType.channel,
        *,
        choices: None = None,
        description: str | None = None,
        channel_types: Sequence[ChannelType] | None = None,
    ) -> None: ...

    def __init__(
        self,
        name: str,
        input_type: InputType | type[T] = str,
        *,
        description: str | None = None,
        choices: Sequence[OptionChoice[T]] | None = None,
        channel_types: Sequence[ChannelType] | None = None,
    ) -> None:
        self.name: str = name

        self.description: str | None = description

        self.choices: list[OptionChoice[T]] | None = choices
        if self.choices is not None:
            if len(self.choices) > 25:
                raise InvalidArgument("Option choices cannot exceed 25 items.")
            if not issubclass(input_type, (str, int, float)):
                raise InvalidArgument("Option choices can only be used with str, int, or float input types.")

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
        elif issubclass(input_type, User):
            self.input_type = SlashCommandOptionType.user
        elif issubclass(input_type, Mentionable):
            self.input_type = SlashCommandOptionType.mentionable
        elif issubclass(input_type, Role):
            self.input_type = SlashCommandOptionType.role
        elif issubclass(input_type, BaseChannel):
            self.input_type = SlashCommandOptionType.channel

        if self.channel_types is not None:
            self.input_type = SlashCommandOptionType.channel
            if len(self.channel_types) == 0:
                raise InvalidArgument("channel_types must contain at least one ChannelType.")

        self.required: bool = kwargs.pop("required", True) if "default" not in kwargs else False
        self.default = kwargs.pop("default", None)

        self._autocomplete: AutocompleteFunction | None = None
        self.autocomplete = kwargs.pop("autocomplete", None)
        if len(enum_choices) > 25:
            self.choices: list[OptionChoice] = []
            for e in enum_choices:
                e.value = str(e.value)
            self.autocomplete = basic_autocomplete(enum_choices)
            self.input_type = SlashCommandOptionType.string
        else:
            self.choices: list[OptionChoice] = enum_choices or [
                o if isinstance(o, OptionChoice) else OptionChoice(o) for o in kwargs.pop("choices", [])
            ]

        if self.input_type == SlashCommandOptionType.integer:
            minmax_types = (int, type(None))
            minmax_typehint = Optional[int]  # noqa: UP045
        elif self.input_type == SlashCommandOptionType.number:
            minmax_types = (int, float, type(None))
            minmax_typehint = Optional[int | float]  # noqa: UP045
        else:
            minmax_types = (type(None),)
            minmax_typehint = type(None)

        if self.input_type == SlashCommandOptionType.string:
            minmax_length_types = (int, type(None))
            minmax_length_typehint = Optional[int]  # noqa: UP045
        else:
            minmax_length_types = (type(None),)
            minmax_length_typehint = type(None)

        self.min_value: int | float | None = kwargs.pop("min_value", None)
        self.max_value: int | float | None = kwargs.pop("max_value", None)
        self.min_length: int | None = kwargs.pop("min_length", None)
        self.max_length: int | None = kwargs.pop("max_length", None)

        if (
            self.input_type != SlashCommandOptionType.integer
            and self.input_type != SlashCommandOptionType.number
            and (self.min_value or self.max_value)
        ):
            raise AttributeError(
                "Option does not take min_value or max_value if not of type "
                "SlashCommandOptionType.integer or SlashCommandOptionType.number"
            )
        if self.input_type != SlashCommandOptionType.string and (self.min_length or self.max_length):
            raise AttributeError("Option does not take min_length or max_length if not of type str")

        if self.min_value is not None and not isinstance(self.min_value, minmax_types):
            raise TypeError(f'Expected {minmax_typehint} for min_value, got "{type(self.min_value).__name__}"')
        if self.max_value is not None and not isinstance(self.max_value, minmax_types):
            raise TypeError(f'Expected {minmax_typehint} for max_value, got "{type(self.max_value).__name__}"')

        if self.min_length is not None:
            if not isinstance(self.min_length, minmax_length_types):
                raise TypeError(
                    f'Expected {minmax_length_typehint} for min_length, got "{type(self.min_length).__name__}"'
                )
            if self.min_length < 0 or self.min_length > 6000:
                raise AttributeError("min_length must be between 0 and 6000 (inclusive)")
        if self.max_length is not None:
            if not isinstance(self.max_length, minmax_length_types):
                raise TypeError(
                    f'Expected {minmax_length_typehint} for max_length, got "{type(self.max_length).__name__}"'
                )
            if self.max_length < 1 or self.max_length > 6000:
                raise AttributeError("max_length must between 1 and 6000 (inclusive)")

        self.name_localizations = kwargs.pop("name_localizations", MISSING)
        self.description_localizations = kwargs.pop("description_localizations", MISSING)

        if input_type is None:
            raise TypeError("input_type cannot be NoneType.")

    @staticmethod
    def _parse_type_alias(input_type: InputType) -> InputType:
        if isinstance(input_type, TypeAliasType):
            return input_type.__value__
        return input_type

    @staticmethod
    def _strip_none_type(input_type):
        if isinstance(input_type, SlashCommandOptionType):
            return input_type

        if input_type is type(None):
            raise TypeError("Option type cannot be only NoneType")

        args = ()
        if isinstance(input_type, types.UnionType):
            args = get_args(input_type)
        elif getattr(input_type, "__origin__", None) is Union:
            args = get_args(input_type)
        elif isinstance(input_type, tuple):
            args = input_type

        if args:
            filtered = tuple(t for t in args if t is not type(None))
            if not filtered:
                raise TypeError("Option type cannot be only NoneType")
            if len(filtered) == 1:
                return filtered[0]

            return filtered

        return input_type

    def to_dict(self) -> dict:
        as_dict = {
            "name": self.name,
            "description": self.description,
            "type": self.input_type.value,
            "required": self.required,
            "choices": [c.to_dict() for c in self.choices],
            "autocomplete": bool(self.autocomplete),
        }
        if self.name_localizations is not MISSING:
            as_dict["name_localizations"] = self.name_localizations
        if self.description_localizations is not MISSING:
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

    def __repr__(self):
        return f"<discord.commands.{self.__class__.__name__} name={self.name}>"

    @property
    def autocomplete(self) -> AutocompleteFunction | None:
        """
        The autocomplete handler for the option. Accepts a callable (sync or async)
        that takes a single required argument of :class:`AutocompleteContext` or two arguments
        of :class:`discord.Cog` (being the command's cog) and :class:`AutocompleteContext`.
        The callable must return an iterable of :class:`str` or :class:`OptionChoice`.
        Alternatively, :func:`discord.utils.basic_autocomplete` may be used in place of the callable.

        Returns
        -------
        Optional[AutocompleteFunction]

        .. versionchanged:: 2.7

        .. note::
            Does not validate the input value against the autocomplete results.
        """
        return self._autocomplete

    @autocomplete.setter
    def autocomplete(self, value: AutocompleteFunction | None) -> None:
        self._autocomplete = value
        # this is done here so it does not have to be computed every time the autocomplete is invoked
        if self._autocomplete is not None:
            self._autocomplete._is_instance_method = (  # pyright: ignore [reportFunctionMemberAccess]
                sum(
                    1
                    for param in inspect.signature(self._autocomplete).parameters.values()
                    if param.default == param.empty  # pyright: ignore[reportAny]
                    and param.kind not in (param.VAR_POSITIONAL, param.VAR_KEYWORD)
                )
                == 2
            )


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
