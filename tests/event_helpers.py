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
from unittest.mock import AsyncMock

from discord.app.event_emitter import Event, EventEmitter
from discord.app.state import ConnectionState


class EventCapture:
    """Helper class to capture events emitted by the EventEmitter."""

    def __init__(self):
        self.events: list[Event] = []
        self.call_count = 0

    async def __call__(self, event: Event) -> None:
        """Called when an event is received."""
        self.events.append(event)
        self.call_count += 1

    def assert_called_once(self):
        """Assert that the event was received exactly once."""
        assert self.call_count == 1, f"Expected 1 event, got {self.call_count}"

    def assert_called_with_event_type(self, event_type: type[Event]):
        """Assert that the event received is of the expected type."""
        assert len(self.events) > 0, "No events were captured"
        event = self.events[-1]
        assert isinstance(event, event_type), f"Expected {event_type.__name__}, got {type(event).__name__}"

    def assert_not_called(self):
        """Assert that no events were received."""
        assert self.call_count == 0, f"Expected 0 events, got {self.call_count}"

    def get_last_event(self) -> Event | None:
        """Get the last event that was captured."""
        return self.events[-1] if self.events else None

    def reset(self):
        """Reset the capture state."""
        self.events.clear()
        self.call_count = 0


async def emit_and_capture(
    state: ConnectionState,
    event_name: str,
    payload: Any,
) -> EventCapture:
    """
    Emit an event and capture it using an EventCapture receiver.

    Args:
        state: The ConnectionState to use for emission
        event_name: The name of the event to emit
        payload: The payload to emit

    Returns:
        EventCapture instance containing captured events
    """
    capture = EventCapture()
    state.emitter.add_receiver(capture)

    try:
        await state.emitter.emit(event_name, payload)
    finally:
        state.emitter.remove_receiver(capture)

    return capture


async def populate_guild_cache(state: ConnectionState, guild_id: int, guild_data: dict[str, Any]):
    """
    Populate the cache with a guild.

    Args:
        state: The ConnectionState to populate
        guild_id: The ID of the guild
        guild_data: The guild data payload
    """
    from discord.guild import Guild

    guild = await Guild._from_data(guild_data, state)
    await state.cache.add_guild(guild)
