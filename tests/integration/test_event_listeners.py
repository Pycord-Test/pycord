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

from discord.bot import Bot
from discord.events.soundboard import GuildSoundboardSoundCreate
from discord.gears import Gear
from tests.fixtures import create_mock_bot, create_mock_state, create_soundboard_sound_payload


@pytest.mark.asyncio
async def test_add_listener():
    """Test adding a listener using add_listener method."""
    # Setup
    bot = create_mock_bot()

    # Track if listener was called
    called = []

    async def on_sound_create(event: GuildSoundboardSoundCreate):
        called.append(event)

    # Add listener
    bot.add_listener(on_sound_create, event=GuildSoundboardSoundCreate)

    # Create sound payload and emit event
    sound_data = create_soundboard_sound_payload(444444444, 111111111, "test-sound")
    await bot._connection.emitter.emit("GUILD_SOUNDBOARD_SOUND_CREATE", sound_data)

    # Wait a bit for event processing
    import asyncio

    await asyncio.sleep(0.1)

    # Assertions
    assert len(called) == 1
    assert isinstance(called[0], GuildSoundboardSoundCreate)
    assert called[0].sound.name == "test-sound"


@pytest.mark.asyncio
async def test_listen_decorator_on_bot_instance():
    """Test using @bot.listen decorator on a bot instance."""
    # Setup
    bot = create_mock_bot()

    # Track if listener was called
    called = []

    @bot.listen(GuildSoundboardSoundCreate)
    async def on_sound_create(event: GuildSoundboardSoundCreate):
        called.append(event)

    # Create sound payload and emit event
    sound_data = create_soundboard_sound_payload(444444444, 111111111, "test-sound")
    await bot._connection.emitter.emit("GUILD_SOUNDBOARD_SOUND_CREATE", sound_data)

    # Wait a bit for event processing
    import asyncio

    await asyncio.sleep(0.1)

    # Assertions
    assert len(called) == 1
    assert isinstance(called[0], GuildSoundboardSoundCreate)
    assert called[0].sound.name == "test-sound"


@pytest.mark.asyncio
async def test_gear_with_class_decorator():
    """Test using @Gear.listen decorator on a class method."""

    # Create a custom gear with class decorator
    class MyGear(Gear):
        def __init__(self):
            super().__init__()
            self.called = []

        @Gear.listen(GuildSoundboardSoundCreate)
        async def on_sound_create(self, event: GuildSoundboardSoundCreate):
            self.called.append(event)

    # Setup
    bot = create_mock_bot()

    # Add gear to bot
    my_gear = MyGear()
    bot.attach_gear(my_gear)

    # Create sound payload and emit event
    sound_data = create_soundboard_sound_payload(444444444, 111111111, "test-sound")
    await bot._connection.emitter.emit("GUILD_SOUNDBOARD_SOUND_CREATE", sound_data)

    # Wait a bit for event processing
    import asyncio

    await asyncio.sleep(0.1)

    # Assertions
    assert len(my_gear.called) == 1
    assert isinstance(my_gear.called[0], GuildSoundboardSoundCreate)
    assert my_gear.called[0].sound.name == "test-sound"


@pytest.mark.asyncio
async def test_gear_instance_decorator():
    """Test using @gear.listen decorator on a gear instance."""
    # Setup
    bot = create_mock_bot()

    # Create gear instance
    my_gear = Gear()

    # Track if listener was called
    called = []

    @my_gear.listen(GuildSoundboardSoundCreate)
    async def on_sound_create(event: GuildSoundboardSoundCreate):
        called.append(event)

    # Add gear to bot
    bot.attach_gear(my_gear)

    # Create sound payload and emit event
    sound_data = create_soundboard_sound_payload(444444444, 111111111, "test-sound")
    await bot._connection.emitter.emit("GUILD_SOUNDBOARD_SOUND_CREATE", sound_data)

    # Wait a bit for event processing
    import asyncio

    await asyncio.sleep(0.1)

    # Assertions
    assert len(called) == 1
    assert isinstance(called[0], GuildSoundboardSoundCreate)
    assert called[0].sound.name == "test-sound"


@pytest.mark.asyncio
async def test_gear_add_listener():
    """Test using gear.add_listener method."""
    # Setup
    bot = create_mock_bot()

    # Create gear instance
    my_gear = Gear()

    # Track if listener was called
    called = []

    async def on_sound_create(event: GuildSoundboardSoundCreate):
        called.append(event)

    # Add listener to gear
    my_gear.add_listener(on_sound_create, event=GuildSoundboardSoundCreate)

    # Add gear to bot
    bot.attach_gear(my_gear)

    # Create sound payload and emit event
    sound_data = create_soundboard_sound_payload(444444444, 111111111, "test-sound")
    await bot._connection.emitter.emit("GUILD_SOUNDBOARD_SOUND_CREATE", sound_data)

    # Wait a bit for event processing
    import asyncio

    await asyncio.sleep(0.1)

    # Assertions
    assert len(called) == 1
    assert isinstance(called[0], GuildSoundboardSoundCreate)
    assert called[0].sound.name == "test-sound"


@pytest.mark.asyncio
async def test_nested_gears():
    """Test that nested gears work correctly."""

    class ParentGear(Gear):
        def __init__(self):
            super().__init__()
            self.called = []

        @Gear.listen(GuildSoundboardSoundCreate)
        async def on_sound_create(self, event: GuildSoundboardSoundCreate):
            self.called.append(("parent", event))

    class ChildGear(Gear):
        def __init__(self):
            super().__init__()
            self.called = []

        @Gear.listen(GuildSoundboardSoundCreate)
        async def on_sound_create(self, event: GuildSoundboardSoundCreate):
            self.called.append(("child", event))

    # Setup
    bot = create_mock_bot()

    # Create gears
    parent_gear = ParentGear()
    child_gear = ChildGear()

    # Add child to parent
    parent_gear.attach_gear(child_gear)

    # Add parent to bot
    bot.attach_gear(parent_gear)

    # Create sound payload and emit event
    sound_data = create_soundboard_sound_payload(444444444, 111111111, "test-sound")
    await bot._connection.emitter.emit("GUILD_SOUNDBOARD_SOUND_CREATE", sound_data)

    # Wait a bit for event processing
    import asyncio

    await asyncio.sleep(0.1)

    # Assertions
    assert len(parent_gear.called) == 1
    assert parent_gear.called[0][0] == "parent"
    assert parent_gear.called[0][1].sound.name == "test-sound"

    assert len(child_gear.called) == 1
    assert child_gear.called[0][0] == "child"
    assert child_gear.called[0][1].sound.name == "test-sound"


@pytest.mark.asyncio
async def test_remove_listener():
    """Test removing a listener."""
    # Setup
    bot = create_mock_bot()

    # Track if listener was called
    called = []

    async def on_sound_create(event: GuildSoundboardSoundCreate):
        called.append(event)

    # Add listener
    bot.add_listener(on_sound_create, event=GuildSoundboardSoundCreate)

    # Create sound payload and emit event
    sound_data = create_soundboard_sound_payload(444444444, 111111111, "test-sound-1")
    await bot._connection.emitter.emit("GUILD_SOUNDBOARD_SOUND_CREATE", sound_data)

    # Wait a bit for event processing
    import asyncio

    await asyncio.sleep(0.1)

    # Should be called once
    assert len(called) == 1

    # Remove listener
    bot.remove_listener(on_sound_create)

    # Emit another event
    sound_data = create_soundboard_sound_payload(444444445, 111111111, "test-sound-2")
    await bot._connection.emitter.emit("GUILD_SOUNDBOARD_SOUND_CREATE", sound_data)

    await asyncio.sleep(0.1)

    # Should still be 1 (not called again)
    assert len(called) == 1


@pytest.mark.asyncio
async def test_multiple_listeners_same_event():
    """Test that multiple listeners for the same event all get called."""
    # Setup
    bot = create_mock_bot()

    # Track calls
    calls = []

    async def listener1(event: GuildSoundboardSoundCreate):
        calls.append("listener1")

    async def listener2(event: GuildSoundboardSoundCreate):
        calls.append("listener2")

    @bot.listen(GuildSoundboardSoundCreate)
    async def listener3(event: GuildSoundboardSoundCreate):
        calls.append("listener3")

    # Add listeners
    bot.add_listener(listener1, event=GuildSoundboardSoundCreate)
    bot.add_listener(listener2, event=GuildSoundboardSoundCreate)

    # Create sound payload and emit event
    sound_data = create_soundboard_sound_payload(444444444, 111111111, "test-sound")
    await bot._connection.emitter.emit("GUILD_SOUNDBOARD_SOUND_CREATE", sound_data)

    # Wait a bit for event processing
    import asyncio

    await asyncio.sleep(0.1)

    # Assertions - all three should be called
    assert len(calls) == 3
    assert "listener1" in calls
    assert "listener2" in calls
    assert "listener3" in calls
