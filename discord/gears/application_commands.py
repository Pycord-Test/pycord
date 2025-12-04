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

from abc import ABC
from functools import wraps
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Coroutine, Generic, ParamSpec, Protocol, TypeAlias, TypeVar

from typing_extensions import Unpack

from ..enums import ApplicationCommandType
from ..events import InteractionCreate
from ..interactions import ApplicationCommandInteraction
from ..utils import MISSING, Undefined
from ..utils.private import hybridmethod, maybe_awaitable
from .base import GearBase

if TYPE_CHECKING:
    from ..commands import ApplicationCommand
P = ParamSpec("P")
R = TypeVar("R")


class CommandListener(Protocol, Generic[P, R]):
    __command__: "ApplicationCommand"

    async def __call__(self, interaction: ApplicationCommandInteraction, *args: P.args, **kwargs: P.kwargs) -> R: ...


def _listener_factory(listener: CommandListener, command_name: str) -> Callable[..., ...]:
    @wraps(listener)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R | None:
        # Assume last positional arg is the interaction
        if args:
            interaction: Any = args[-1]
            if isinstance(interaction, ApplicationCommandInteraction) and interaction.command_name == command_name:
                interaction.command = listener.__command__
                if interaction.command_type == ApplicationCommandType.CHAT_INPUT:
                    ...
                elif interaction.command_type == ApplicationCommandType.USER:
                    ...

            return await listener(*args, **kwargs)
        return None

    return wrapper


ACG_t = TypeVar("ACG_t", bound="ApplicationCommandsGearMixin")


class ApplicationCommandsGearMixin(GearBase, ABC):
    """A mixin that provides application commands handling for a :class:`discord.Gear`.

    This mixin is used to handle application commands interactions.
    """
