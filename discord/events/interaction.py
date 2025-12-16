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

from functools import lru_cache
from typing import Any

from typing_extensions import Self, override

from discord.enums import InteractionType
from discord.types.interactions import Interaction as InteractionPayload

from ..app.event_emitter import Event
from ..app.state import ConnectionState
from ..interactions import (
    ApplicationCommandInteraction,
    AutocompleteInteraction,
    BaseInteraction,
    ComponentInteraction,
    ModalInteraction,
)


def _interaction_factory(payload: InteractionPayload) -> type[BaseInteraction]:
    type: int = payload["type"]
    if type == InteractionType.application_command.value:
        return ApplicationCommandInteraction
    if type == InteractionType.auto_complete.value:
        return AutocompleteInteraction
    if type == InteractionType.component.value:
        return ComponentInteraction
    if type == InteractionType.modal_submit.value:
        return ModalInteraction
    return BaseInteraction


@lru_cache(maxsize=128)
def _create_event_interaction_class(interaction_cls: type[BaseInteraction]) -> type[BaseInteraction]:
    class EventInteraction(interaction_cls, Event):  # type: ignore
        __slots__ = ()

        @override
        def __init__(self) -> None:
            pass

        @override
        @classmethod
        def event_type(self) -> type[Event]:
            return InteractionCreate

        @classmethod
        @override
        async def __load__(cls, data: InteractionPayload, state: ConnectionState) -> None:
            return None

    return EventInteraction  # type: ignore


class InteractionCreate(Event, BaseInteraction):
    """Called when an interaction is created.

    This currently happens due to application command invocations or components being used.

    This event inherits from :class:`Interaction`.
    """

    __event_name__: str = "INTERACTION_CREATE"

    def __init__(self) -> None:
        pass

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        factory = _interaction_factory(data)
        interaction = await factory._from_data(payload=data, state=state)
        interaction_event_cls = _create_event_interaction_class(factory)
        self = interaction_event_cls()
        self._populate_from_slots(interaction)
        return self
