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

from typing import Any, Self

from discord.enums import InteractionType
from discord.types.interactions import Interaction as InteractionPayload
from ..app.state import ConnectionState
from ..interactions import Interaction
from ..app.event_emitter import Event


class InteractionCreate(Event, Interaction):
    __event_name__ = "INTERACTION_CREATE"

    def __init__(self) -> None:
        pass

    @classmethod
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        interaction = Interaction(data=data, state=state)
        if data["type"] == 3:
            custom_id = interaction.data["custom_id"]  # type: ignore
            component_type = interaction.data["component_type"]  # type: ignore
            views = await state.cache.get_all_views()
            for view in views:
                if view.id == custom_id:
                    for item in view.children:
                        if item.type == component_type:
                            item.refresh_state(interaction)
                            view._dispatch_item(item, interaction)
        if interaction.type == InteractionType.modal_submit:
            custom_id = interaction.data["custom_id"]
            for modal in await state.cache.get_all_modals():
                if modal.custom_id != custom_id:
                    continue
                try:
                    components = [
                        component
                        for parent_component in interaction.data["components"]
                        for component in parent_component["components"]
                    ]
                    for component in components:
                        for child in modal.children:
                            if child.custom_id == component["custom_id"]:  # type: ignore
                                child.refresh_state(component)
                                break
                    await modal.callback(interaction)
                    await state.cache.delete_modal(modal.custom_id)
                except Exception as e:
                    return await modal.on_error(e, interaction)
        self = cls()
        self.__dict__.update(interaction.__dict__)
        return self
