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

import copy
import logging
from typing import Any

from typing_extensions import Self, override

from discord.app.event_emitter import Event
from discord.app.state import ConnectionState
from discord.stage_instance import StageInstance

_log = logging.getLogger(__name__)


class StageInstanceCreate(Event, StageInstance):
    """Called when a stage instance is created for a stage channel.

    This event inherits from :class:`StageInstance`.
    """

    __event_name__: str = "STAGE_INSTANCE_CREATE"

    def __init__(self) -> None: ...

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        guild = await state._get_guild(int(data["guild_id"]))
        if guild is None:
            _log.debug(
                "STAGE_INSTANCE_CREATE referencing unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )
            return

        stage_instance = StageInstance(guild=guild, state=state, data=data)
        guild._stage_instances[stage_instance.id] = stage_instance

        self = cls()
        self.__dict__.update(stage_instance.__dict__)
        return self


class StageInstanceUpdate(Event, StageInstance):
    """Called when a stage instance is updated.

    The following, but not limited to, examples illustrate when this event is called:
    - The topic is changed.
    - The privacy level is changed.

    This event inherits from :class:`StageInstance`.

    Attributes
    ----------
    old: :class:`StageInstance`
        The stage instance before the update.
    """

    __event_name__: str = "STAGE_INSTANCE_UPDATE"

    old: StageInstance

    def __init__(self) -> None: ...

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        guild = await state._get_guild(int(data["guild_id"]))
        if guild is None:
            _log.debug(
                "STAGE_INSTANCE_UPDATE referencing unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )
            return

        stage_instance = guild._stage_instances.get(int(data["id"]))
        if stage_instance is None:
            _log.debug(
                "STAGE_INSTANCE_UPDATE referencing unknown stage instance ID: %s. Discarding.",
                data["id"],
            )
            return

        old_stage_instance = copy.copy(stage_instance)
        stage_instance._update(data)

        self = cls()
        self.old = old_stage_instance
        self.__dict__.update(stage_instance.__dict__)
        return self


class StageInstanceDelete(Event, StageInstance):
    """Called when a stage instance is deleted for a stage channel.

    This event inherits from :class:`StageInstance`.
    """

    __event_name__: str = "STAGE_INSTANCE_DELETE"

    def __init__(self) -> None: ...

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        guild = await state._get_guild(int(data["guild_id"]))
        if guild is None:
            _log.debug(
                "STAGE_INSTANCE_DELETE referencing unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )
            return

        try:
            stage_instance = guild._stage_instances.pop(int(data["id"]))
        except KeyError:
            return

        self = cls()
        self.__dict__.update(stage_instance.__dict__)
        return self
