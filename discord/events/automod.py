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

from typing import Any

from typing_extensions import Self, override

from discord.app.state import ConnectionState
from discord.automod import AutoModRule
from discord.raw_models import AutoModActionExecutionEvent

from ..app.event_emitter import Event


class AutoModRuleCreate(Event):
    """Called when an auto moderation rule is created.

    The bot must have :attr:`~Permissions.manage_guild` to receive this, and
    :attr:`Intents.auto_moderation_configuration` must be enabled.

    Attributes
    ----------
    rule: :class:`AutoModRule`
        The newly created rule.
    """

    __event_name__: str = "AUTO_MODERATION_RULE_CREATE"
    __slots__ = ("rule",)

    rule: AutoModRule

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self:
        self = cls()
        self.rule = AutoModRule(state=state, data=data)
        return self


class AutoModRuleUpdate(Event):
    """Called when an auto moderation rule is updated.

    The bot must have :attr:`~Permissions.manage_guild` to receive this, and
    :attr:`Intents.auto_moderation_configuration` must be enabled.

    Attributes
    ----------
    rule: :class:`AutoModRule`
        The updated rule.
    """

    __event_name__: str = "AUTO_MODERATION_RULE_UPDATE"
    __slots__ = ("rule",)

    rule: AutoModRule

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self:
        self = cls()
        self.rule = AutoModRule(state=state, data=data)
        return self


class AutoModRuleDelete(Event):
    """Called when an auto moderation rule is deleted.

    The bot must have :attr:`~Permissions.manage_guild` to receive this, and
    :attr:`Intents.auto_moderation_configuration` must be enabled.

    Attributes
    ----------
    rule: :class:`AutoModRule`
        The deleted rule.
    """

    __event_name__: str = "AUTO_MODERATION_RULE_DELETE"
    __slots__ = ("rule",)

    rule: AutoModRule

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self:
        self = cls()
        self.rule = AutoModRule(state=state, data=data)
        return self


class AutoModActionExecution(Event, AutoModActionExecutionEvent):
    """Called when an auto moderation action is executed.

    The bot must have :attr:`~Permissions.manage_guild` to receive this, and
    :attr:`Intents.auto_moderation_execution` must be enabled.

    This event inherits from :class:`AutoModActionExecutionEvent`.
    """

    __event_name__: str = "AUTO_MODERATION_ACTION_EXECUTION"

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self:
        self = cls()
        event = await AutoModActionExecutionEvent.from_data(state, data)
        self.__dict__.update(event.__dict__)
        return self
