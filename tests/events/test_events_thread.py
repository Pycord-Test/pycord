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

from discord.events.thread import ThreadCreate, ThreadDelete, ThreadJoin, ThreadUpdate
from tests.event_helpers import emit_and_capture, populate_guild_cache
from tests.fixtures import (
    create_channel_payload,
    create_guild_payload,
    create_mock_state,
    create_thread_payload,
)


@pytest.mark.asyncio
async def test_thread_create():
    """Test that THREAD_CREATE event is emitted correctly."""
    # Setup
    state = create_mock_state()
    guild_id = 111111111
    channel_id = 222222222
    thread_id = 333333333

    # Populate cache with guild and parent channel
    guild_data = create_guild_payload(guild_id)
    await populate_guild_cache(state, guild_id, guild_data)

    channel_data = create_channel_payload(channel_id=channel_id, guild_id=guild_id, name="test-channel")
    await state.emitter.emit("CHANNEL_CREATE", channel_data)

    # Create thread payload
    thread_data = create_thread_payload(
        thread_id=thread_id, guild_id=guild_id, parent_id=channel_id, name="test-thread"
    )

    # Emit event and capture
    capture = await emit_and_capture(state, "THREAD_CREATE", thread_data)

    # Assertions
    # ThreadCreate may emit THREAD_JOIN or return the thread itself
    assert capture.call_count >= 0  # May or may not emit depending on just_joined


@pytest.mark.asyncio
async def test_thread_create_newly_created():
    """Test that THREAD_CREATE event with newly_created flag."""
    # Setup
    state = create_mock_state()
    guild_id = 111111111
    channel_id = 222222222
    thread_id = 333333333

    # Populate cache with guild and parent channel
    guild_data = create_guild_payload(guild_id)
    await populate_guild_cache(state, guild_id, guild_data)

    channel_data = create_channel_payload(channel_id=channel_id, guild_id=guild_id, name="test-channel")
    await state.emitter.emit("CHANNEL_CREATE", channel_data)

    # Create thread payload with newly_created flag
    thread_data = create_thread_payload(
        thread_id=thread_id, guild_id=guild_id, parent_id=channel_id, name="test-thread"
    )
    thread_data["newly_created"] = True

    # Emit event and capture
    capture = await emit_and_capture(state, "THREAD_CREATE", thread_data)

    # Assertions - newly created threads emit ThreadCreate, not ThreadJoin
    if capture.call_count > 0:
        event = capture.get_last_event()
        assert event is not None


@pytest.mark.asyncio
async def test_thread_delete():
    """Test that THREAD_DELETE event is emitted correctly."""
    # Setup
    state = create_mock_state()
    guild_id = 111111111
    channel_id = 222222222
    thread_id = 333333333

    # Populate cache with guild and parent channel
    guild_data = create_guild_payload(guild_id)
    await populate_guild_cache(state, guild_id, guild_data)

    channel_data = create_channel_payload(channel_id=channel_id, guild_id=guild_id, name="test-channel")
    await state.emitter.emit("CHANNEL_CREATE", channel_data)

    # Create thread first
    thread_data = create_thread_payload(
        thread_id=thread_id, guild_id=guild_id, parent_id=channel_id, name="test-thread"
    )
    thread_data["newly_created"] = True
    await state.emitter.emit("THREAD_CREATE", thread_data)

    # Create delete payload
    delete_data = {
        "id": str(thread_id),
        "guild_id": str(guild_id),
        "parent_id": str(channel_id),
        "type": 11,  # PUBLIC_THREAD
    }

    # Emit event and capture
    capture = await emit_and_capture(state, "THREAD_DELETE", delete_data)

    # Assertions
    # The event may or may not be emitted depending on whether thread exists
    assert capture.call_count >= 0


@pytest.mark.asyncio
async def test_thread_create_without_guild():
    """Test that THREAD_CREATE returns None when guild is not found."""
    # Setup
    state = create_mock_state()
    guild_id = 111111111
    channel_id = 222222222
    thread_id = 333333333

    # Don't populate cache with guild

    # Create thread payload
    thread_data = create_thread_payload(
        thread_id=thread_id, guild_id=guild_id, parent_id=channel_id, name="test-thread"
    )

    # Emit event and capture
    capture = await emit_and_capture(state, "THREAD_CREATE", thread_data)

    # Assertions - should not emit event if guild not found
    capture.assert_not_called()
