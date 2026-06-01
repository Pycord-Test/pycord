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

import asyncio
import collections
import collections.abc
import copy
import inspect
import logging
import sys
import traceback
from abc import ABC, abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Coroutine,
    Generator,
    Literal,
    Mapping,
    TypeVar,
)

from .client import Client
from .commands import (
    ApplicationCommand,
    ApplicationContext,
    AutocompleteContext,
    MessageCommand,
    SlashCommand,
    SlashCommandGroup,
    UserCommand,
    command,
)
from .enums import IntegrationType, InteractionContextType, InteractionType
from .errors import CheckFailure, DiscordException
from .events import InteractionCreate
from .interactions import Interaction
from .shard import AutoShardedClient
from .types import interactions
from .user import User
from .utils import MISSING, find
from .utils.private import async_all

if TYPE_CHECKING:
    from .member import Member

CoroFunc = Callable[..., Coroutine[Any, Any, Any]]
CFT = TypeVar("CFT", bound=CoroFunc)

__all__ = (
    "ApplicationCommandMixin",
    "Bot",
    "AutoShardedBot",
)

_log = logging.getLogger(__name__)


class BotBase(ABC):
    _supports_prefixed_commands = False

    def __init__(self, description=None, *args, **options):
        super().__init__(*args, **options)
        self.__cogs = {}  # TYPE: Dict[str, Cog]
        self.__extensions = {}  # TYPE: Dict[str, types.ModuleType]
        self._checks = []  # TYPE: List[Check]
        self._check_once = []
        self._before_invoke = None
        self._after_invoke = None
        self.description = inspect.cleandoc(description) if description else ""
        self.owner_id = options.get("owner_id")
        self.owner_ids = options.get("owner_ids", set())
        self.auto_sync_commands = options.get("auto_sync_commands", True)

        self.debug_guilds = options.pop("debug_guilds", None)
        self.default_command_contexts = options.pop(
            "default_command_contexts",
            {
                InteractionContextType.guild,
                InteractionContextType.bot_dm,
                InteractionContextType.private_channel,
            },
        )

        self.default_command_integration_types = options.pop(
            "default_command_integration_types",
            {
                IntegrationType.guild_install,
            },
        )

        if self.owner_id and self.owner_ids:
            raise TypeError("Both owner_id and owner_ids are set.")

        if self.owner_ids and not isinstance(self.owner_ids, collections.abc.Collection):
            raise TypeError(f"owner_ids must be a collection not {self.owner_ids.__class__!r}")
        if not isinstance(self.default_command_contexts, collections.abc.Collection):
            raise TypeError(
                f"default_command_contexts must be a collection not {self.default_command_contexts.__class__!r}"
            )
        if not isinstance(self.default_command_integration_types, collections.abc.Collection):
            raise TypeError(
                f"default_command_integration_types must be a collection not {self.default_command_integration_types.__class__!r}"
            )
        self.default_command_contexts = set(self.default_command_contexts)
        self.default_command_integration_types = set(self.default_command_integration_types)

        self._checks = []
        self._check_once = []
        self._before_invoke = None
        self._after_invoke = None

        self._bot.add_listener(self.on_interaction, event=InteractionCreate)

    async def on_connect(self):
        if self.auto_sync_commands:
            await self.sync_commands()

    async def on_interaction(self, interaction: InteractionCreate):
        await self.process_application_commands(interaction)

    async def on_application_command_error(self, context: ApplicationContext, exception: DiscordException) -> None:
        """|coro|

        The default command error handler provided by the bot.

        By default, this prints to :data:`sys.stderr` however it could be
        overridden to have a different implementation.

        This only fires if you do not specify any listeners for command error.
        """
        if self._event_handlers.get("on_application_command_error", None):
            return
        command = context.command
        if command and command.has_error_handler():
            return

        cog = context.cog
        if cog and cog.has_error_handler():
            return

        print(f"Ignoring exception in command {context.command}:", file=sys.stderr)
        traceback.print_exception(type(exception), exception, exception.__traceback__, file=sys.stderr)

    # global check registration
    # TODO: Remove these from commands.Bot

    def check(self, func):
        """A decorator that adds a global check to the bot. A global check is similar to a :func:`.check` that is
        applied on a per-command basis except it is run before any command checks have been verified and applies to
        every command the bot has.

        .. note::

           This function can either be a regular function or a coroutine. Similar to a command :func:`.check`, this
           takes a single parameter of type :class:`.Context` and can only raise exceptions inherited from
           :exc:`.ApplicationCommandError`.

        Example
        -------
        .. code-block:: python3

            @bot.check
            def check_commands(ctx):
                return ctx.command.qualified_name in allowed_commands
        """
        # T was used instead of Check to ensure the type matches on return
        self.add_check(func)  # type: ignore
        return func

    def add_check(self, func, *, call_once: bool = False) -> None:
        """Adds a global check to the bot. This is the non-decorator interface to :meth:`.check` and
        :meth:`.check_once`.

        Parameters
        ----------
        func
            The function that was used as a global check.
        call_once: :class:`bool`
            If the function should only be called once per :meth:`.Bot.invoke` call.
        """

        if call_once:
            self._check_once.append(func)
        else:
            self._checks.append(func)

    def remove_check(self, func, *, call_once: bool = False) -> None:
        """Removes a global check from the bot.
        This function is idempotent and will not raise an exception
        if the function is not in the global checks.

        Parameters
        ----------
        func
            The function to remove from the global checks.
        call_once: :class:`bool`
            If the function was added with ``call_once=True`` in
            the :meth:`.Bot.add_check` call or using :meth:`.check_once`.
        """
        checks = self._check_once if call_once else self._checks

        try:
            checks.remove(func)
        except ValueError:
            pass

    def check_once(self, func):
        """A decorator that adds a "call once" global check to the bot. Unlike regular global checks, this one is called
        only once per :meth:`.Bot.invoke` call. Regular global checks are called whenever a command is called or
        :meth:`.Command.can_run` is called. This type of check bypasses that and ensures that it's called only once,
        even inside the default help command.

        .. note::

           When using this function the :class:`.Context` sent to a group subcommand may only parse the parent command
           and not the subcommands due to it being invoked once per :meth:`.Bot.invoke` call.

        .. note::

           This function can either be a regular function or a coroutine. Similar to a command :func:`.check`,
           this takes a single parameter of type :class:`.Context` and can only raise exceptions inherited from
           :exc:`.ApplicationCommandError`.

        Example
        -------
        .. code-block:: python3

            @bot.check_once
            def whitelist(ctx):
                return ctx.message.author.id in my_whitelist
        """
        self.add_check(func, call_once=True)
        return func

    async def can_run(self, ctx: ApplicationContext, *, call_once: bool = False) -> bool:
        data = self._check_once if call_once else self._checks

        if not data:
            return True

        # type-checker doesn't distinguish between functions and methods
        return await async_all(f(ctx) for f in data)  # type: ignore

    def before_invoke(self, coro):
        """A decorator that registers a coroutine as a pre-invoke hook.
        A pre-invoke hook is called directly before the command is
        called. This makes it a useful function to set up database
        connections or any type of set up required.
        This pre-invoke hook takes a sole parameter, a :class:`.Context`.

        .. note::

            The :meth:`~.Bot.before_invoke` and :meth:`~.Bot.after_invoke` hooks are
            only called if all checks and argument parsing procedures pass
            without error. If any check or argument parsing procedures fail
            then the hooks are not called.

        Parameters
        ----------
        coro: :ref:`coroutine <coroutine>`
            The coroutine to register as the pre-invoke hook.

        Raises
        ------
        TypeError
            The coroutine passed is not actually a coroutine.
        """
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError("The pre-invoke hook must be a coroutine.")

        self._before_invoke = coro
        return coro

    def after_invoke(self, coro):
        r"""A decorator that registers a coroutine as a post-invoke hook.
        A post-invoke hook is called directly after the command is
        called. This makes it a useful function to clean-up database
        connections or any type of clean up required.
        This post-invoke hook takes a sole parameter, a :class:`.Context`.

        .. note::

            Similar to :meth:`~.Bot.before_invoke`\, this is not called unless
            checks and argument parsing procedures succeed. This hook is,
            however, **always** called regardless of the internal command
            callback raising an error (i.e. :exc:`.CommandInvokeError`\).
            This makes it ideal for clean-up scenarios.

        Parameters
        -----------
        coro: :ref:`coroutine <coroutine>`
            The coroutine to register as the post-invoke hook.

        Raises
        -------
        TypeError
            The coroutine passed is not actually a coroutine.

        """
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError("The post-invoke hook must be a coroutine.")

        self._after_invoke = coro
        return coro

    async def is_owner(self, user: User | Member) -> bool:
        """|coro|

        Checks if a :class:`~discord.User` or :class:`~discord.Member` is the owner of
        this bot.

        If an :attr:`owner_id` is not set, it is fetched automatically
        through the use of :meth:`~.Bot.application_info`.

        .. versionchanged:: 1.3
            The function also checks if the application is team-owned if
            :attr:`owner_ids` is not set.

        Parameters
        ----------
        user: Union[:class:`.abc.User`, :class:`.member.Member`]
            The user to check for.

        Returns
        -------
        :class:`bool`
            Whether the user is the owner.
        """

        if self.owner_id:
            return user.id == self.owner_id
        elif self.owner_ids:
            return user.id in self.owner_ids
        else:
            app = await self.application_info()  # type: ignore
            if app.team:
                self.owner_ids = ids = {m.id for m in app.team.members}
                return user.id in ids
            else:
                self.owner_id = owner_id = app.owner.id
                return user.id == owner_id


class Bot(BotBase, Client):
    """Represents a discord bot.

    This class is a subclass of :class:`discord.Client` and as a result
    anything that you can do with a :class:`discord.Client` you can do with
    this bot.

    This class also subclasses ``ApplicationCommandMixin`` to provide the functionality
    to manage commands.

    .. versionadded:: 2.0

    Attributes
    ----------
    description: :class:`str`
        The content prefixed into the default help message.
    owner_id: Optional[:class:`int`]
        The user ID that owns the bot. If this is not set and is then queried via
        :meth:`.is_owner` then it is fetched automatically using
        :meth:`~.Bot.application_info`.
    owner_ids: Optional[Collection[:class:`int`]]
        The user IDs that owns the bot. This is similar to :attr:`owner_id`.
        If this is not set and the application is team based, then it is
        fetched automatically using :meth:`~.Bot.application_info`.
        For performance reasons it is recommended to use a :class:`set`
        for the collection. You cannot set both ``owner_id`` and ``owner_ids``.

        .. versionadded:: 1.3
    debug_guilds: Optional[List[:class:`int`]]
        Guild IDs of guilds to use for testing commands.
        The bot will not create any global commands if debug guild IDs are passed.

        .. versionadded:: 2.0
    auto_sync_commands: :class:`bool`
        Whether to automatically sync slash commands. This will call :meth:`~.Bot.sync_commands` in :func:`discord.on_connect`, and in
        :attr:`.process_application_commands` if the command is not found. Defaults to ``True``.

        .. versionadded:: 2.0
    default_command_contexts: Collection[:class:`InteractionContextType`]
        The default context types that the bot will use for commands.
        Defaults to a set containing :attr:`InteractionContextType.guild`, :attr:`InteractionContextType.bot_dm`, and
        :attr:`InteractionContextType.private_channel`.

        .. versionadded:: 2.6
    default_command_integration_types: Collection[:class:`IntegrationType`]]
        The default integration types that the bot will use for commands.
        Defaults to a set containing :attr:`IntegrationType.guild_install`.

        .. versionadded:: 2.6
    """

    @property
    def _bot(self) -> Bot:
        return self


class AutoShardedBot(BotBase, AutoShardedClient):
    """This is similar to :class:`.Bot` except that it is inherited from
    :class:`discord.AutoShardedClient` instead.

    .. versionadded:: 2.0
    """

    @property
    def _bot(self) -> AutoShardedBot:
        return self
