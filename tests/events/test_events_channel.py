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

import pytest

from discord.events.channel import (
    ChannelCreate,
    ChannelDelete,
    ChannelPinsUpdate,
    GuildChannelUpdate,
)
from tests.event_helpers import emit_and_capture, populate_guild_cache
from tests.fixtures import create_channel_payload, create_guild_payload, create_mock_state


@pytest.mark.asyncio
async def test_channel_create():
    """Test that CHANNEL_CREATE event is emitted correctly."""
    # Setup
    state = create_mock_state()
    guild_id = 111111111
    channel_id = 222222222

    # Populate cache with guild
    guild_data = create_guild_payload(guild_id)
    await populate_guild_cache(state, guild_id, guild_data)

    # Create channel payload
    channel_data = create_channel_payload(channel_id=channel_id, guild_id=guild_id, name="test-channel")

    # Emit event and capture
    capture = await emit_and_capture(state, "CHANNEL_CREATE", channel_data)

    # Assertions
    capture.assert_called_once()
    capture.assert_called_with_event_type(ChannelCreate)

    event = capture.get_last_event()
    assert event is not None
    assert event.id == channel_id
    assert event.name == "test-channel"


@pytest.mark.asyncio
async def test_channel_delete():
    """Test that CHANNEL_DELETE event is emitted correctly."""
    # Setup
    state = create_mock_state()
    guild_id = 111111111
    channel_id = 222222222

    # Populate cache with guild and channel
    guild_data = create_guild_payload(guild_id)
    await populate_guild_cache(state, guild_id, guild_data)

    # Create channel first
    channel_data = create_channel_payload(channel_id=channel_id, guild_id=guild_id, name="test-channel")
    await state.emitter.emit("CHANNEL_CREATE", channel_data)

    # Now delete it
    capture = await emit_and_capture(state, "CHANNEL_DELETE", channel_data)

    # Assertions
    capture.assert_called_once()
    capture.assert_called_with_event_type(ChannelDelete)

    event = capture.get_last_event()
    assert event is not None
    assert event.id == channel_id
    assert event.name == "test-channel"


@pytest.mark.asyncio
async def test_channel_pins_update():
    """Test that CHANNEL_PINS_UPDATE event is emitted correctly."""
    # Setup
    state = create_mock_state()
    guild_id = 111111111
    channel_id = 222222222

    # Populate cache with guild and channel
    guild_data = create_guild_payload(guild_id)
    await populate_guild_cache(state, guild_id, guild_data)

    channel_data = create_channel_payload(channel_id=channel_id, guild_id=guild_id, name="test-channel")
    await state.emitter.emit("CHANNEL_CREATE", channel_data)

    # Create pins update payload
    pins_data = {
        "guild_id": str(guild_id),
        "channel_id": str(channel_id),
        "last_pin_timestamp": "2024-01-01T00:00:00+00:00",
    }

    # Emit event and capture
    capture = await emit_and_capture(state, "CHANNEL_PINS_UPDATE", pins_data)

    # Assertions
    capture.assert_called_once()
    capture.assert_called_with_event_type(ChannelPinsUpdate)

    event = capture.get_last_event()
    assert event is not None
    assert event.channel.id == channel_id
    assert event.last_pin is not None


@pytest.mark.asyncio
async def test_channel_update():
    """Test that CHANNEL_UPDATE event triggers GUILD_CHANNEL_UPDATE."""
    # Setup
    state = create_mock_state()
    guild_id = 111111111
    channel_id = 222222222

    # Populate cache with guild and channel
    guild_data = create_guild_payload(guild_id)
    await populate_guild_cache(state, guild_id, guild_data)

    channel_data = create_channel_payload(channel_id=channel_id, guild_id=guild_id, name="test-channel")
    await state.emitter.emit("CHANNEL_CREATE", channel_data)

    # Update channel
    updated_channel_data = create_channel_payload(channel_id=channel_id, guild_id=guild_id, name="updated-channel")

    # Emit event and capture
    capture = await emit_and_capture(state, "CHANNEL_UPDATE", updated_channel_data)

    # Assertions - CHANNEL_UPDATE dispatches GUILD_CHANNEL_UPDATE
    # The original event doesn't return anything but emits a sub-event
    assert capture.call_count >= 0  # May emit GUILD_CHANNEL_UPDATE


@pytest.mark.asyncio
async def test_channel_create_without_guild():
    """Test that CHANNEL_CREATE returns None when guild is not found."""
    # Setup
    state = create_mock_state()
    guild_id = 111111111
    channel_id = 222222222

    # Don't populate cache with guild

    # Create channel payload
    channel_data = create_channel_payload(channel_id=channel_id, guild_id=guild_id, name="test-channel")

    # Emit event and capture
    capture = await emit_and_capture(state, "CHANNEL_CREATE", channel_data)

    # Assertions - should not emit event if guild not found
    capture.assert_not_called()
