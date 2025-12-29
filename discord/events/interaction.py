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

from typing import Any, TypeAlias

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

Interaction: TypeAlias = (
    ApplicationCommandInteraction | AutocompleteInteraction | ComponentInteraction | ModalInteraction
)


async def _interaction_factory(payload: InteractionPayload, state: "ConnectionState") -> Interaction:
    _type: int = payload["type"]
    cls: type[Interaction] = BaseInteraction  # pyright: ignore[reportAssignmentType] # TODO: This should also cover ping interactions @Paillat-dev
    if _type == InteractionType.application_command.value:
        cls = ApplicationCommandInteraction
    elif _type == InteractionType.auto_complete.value:
        cls = AutocompleteInteraction
    elif _type == InteractionType.component.value:
        cls = ComponentInteraction
    elif _type == InteractionType.modal_submit.value:
        cls = ModalInteraction

    return await cls._from_data(payload=payload, state=state)  # pyright: ignore[reportArgumentType]


class InteractionCreate(Event):
    """Called when an interaction is created.

    This currently happens due to application command invocations or components being used.
    """

    __event_name__: str = "INTERACTION_CREATE"

    def __init__(self, interaction: Interaction) -> None:
        self.interaction: Interaction = interaction

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        interaction = await _interaction_factory(data, state)
        return cls(interaction)
