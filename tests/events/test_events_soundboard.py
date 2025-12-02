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

from discord.events.soundboard import (
    GuildSoundboardSoundCreate,
    GuildSoundboardSoundDelete,
    GuildSoundboardSoundUpdate,
    SoundboardSounds,
)
from discord.soundboard import SoundboardSound
from tests.event_helpers import emit_and_capture
from tests.fixtures import create_mock_state, create_soundboard_sound_payload


@pytest.mark.asyncio
async def test_soundboard_sounds():
    """Test that SOUNDBOARD_SOUNDS event is emitted correctly."""
    # Setup
    state = create_mock_state()
    guild_id = 111111111

    # Create soundboard sounds payload
    sounds_data = {
        "guild_id": str(guild_id),
        "soundboard_sounds": [
            create_soundboard_sound_payload(444444444, guild_id, "sound1"),
            create_soundboard_sound_payload(444444445, guild_id, "sound2"),
        ],
    }

    # Emit event and capture
    capture = await emit_and_capture(state, "SOUNDBOARD_SOUNDS", sounds_data)

    # Assertions
    capture.assert_called_once()
    capture.assert_called_with_event_type(SoundboardSounds)

    event = capture.get_last_event()
    assert event is not None
    assert event.guild_id == guild_id
    assert len(event.sounds) == 2
    assert event.sounds[0].name == "sound1"
    assert event.sounds[1].name == "sound2"

    # Verify sounds are cached
    sound1 = await state.cache.get_sound(444444444)
    assert sound1 is not None
    assert sound1.name == "sound1"


@pytest.mark.asyncio
async def test_guild_soundboard_sound_create():
    """Test that GUILD_SOUNDBOARD_SOUND_CREATE event is emitted correctly."""
    # Setup
    state = create_mock_state()
    guild_id = 111111111
    sound_id = 444444444

    # Create sound payload
    sound_data = create_soundboard_sound_payload(sound_id, guild_id, "new-sound", emoji_name="🎵")

    # Emit event and capture
    capture = await emit_and_capture(state, "GUILD_SOUNDBOARD_SOUND_CREATE", sound_data)

    # Assertions
    capture.assert_called_once()
    capture.assert_called_with_event_type(GuildSoundboardSoundCreate)

    event = capture.get_last_event()
    assert event is not None
    assert event.sound.id == sound_id
    assert event.sound.name == "new-sound"

    # Verify sound is cached
    cached_sound = await state.cache.get_sound(sound_id)
    assert cached_sound is not None
    assert cached_sound.name == "new-sound"


@pytest.mark.asyncio
async def test_guild_soundboard_sound_update():
    """Test that GUILD_SOUNDBOARD_SOUND_UPDATE event is emitted correctly."""
    # Setup
    state = create_mock_state()
    guild_id = 111111111
    sound_id = 444444444

    # Create and cache original sound
    original_sound = SoundboardSound(
        state=state,
        http=state.http,
        data=create_soundboard_sound_payload(sound_id, guild_id, "original-name"),
    )
    await state.cache.store_sound(original_sound)

    # Create updated sound payload
    updated_data = create_soundboard_sound_payload(sound_id, guild_id, "updated-name")

    # Emit event and capture
    capture = await emit_and_capture(state, "GUILD_SOUNDBOARD_SOUND_UPDATE", updated_data)

    # Assertions
    capture.assert_called_once()
    capture.assert_called_with_event_type(GuildSoundboardSoundUpdate)

    event = capture.get_last_event()
    assert event is not None
    assert event.before.name == "original-name"
    assert event.after.name == "updated-name"
    assert event.before.id == sound_id
    assert event.after.id == sound_id


@pytest.mark.asyncio
async def test_guild_soundboard_sound_update_without_cache():
    """Test that GUILD_SOUNDBOARD_SOUND_UPDATE returns None when sound is not cached."""
    # Setup
    state = create_mock_state()
    guild_id = 111111111
    sound_id = 444444444

    # Don't cache the sound

    # Create sound payload
    sound_data = create_soundboard_sound_payload(sound_id, guild_id, "new-sound")

    # Emit event and capture
    capture = await emit_and_capture(state, "GUILD_SOUNDBOARD_SOUND_UPDATE", sound_data)

    # Assertions - should not emit event if sound not found
    capture.assert_not_called()


@pytest.mark.asyncio
async def test_guild_soundboard_sound_delete():
    """Test that GUILD_SOUNDBOARD_SOUND_DELETE event is emitted correctly."""
    # Setup
    state = create_mock_state()
    guild_id = 111111111
    sound_id = 444444444

    # Create and cache sound
    sound = SoundboardSound(
        state=state,
        http=state.http,
        data=create_soundboard_sound_payload(sound_id, guild_id, "test-sound"),
    )
    await state.cache.store_sound(sound)

    # Create delete payload
    delete_data = {
        "guild_id": str(guild_id),
        "sound_id": str(sound_id),
    }

    # Emit event and capture
    capture = await emit_and_capture(state, "GUILD_SOUNDBOARD_SOUND_DELETE", delete_data)

    # Assertions
    capture.assert_called_once()
    capture.assert_called_with_event_type(GuildSoundboardSoundDelete)

    event = capture.get_last_event()
    assert event is not None
    assert event.sound is not None
    assert event.sound.id == sound_id
    assert event.sound.name == "test-sound"
    assert event.raw.sound_id == sound_id
    assert event.raw.guild_id == guild_id

    # Verify sound is removed from cache
    cached_sound = await state.cache.get_sound(sound_id)
    assert cached_sound is None


@pytest.mark.asyncio
async def test_guild_soundboard_sound_delete_without_cache():
    """Test that GUILD_SOUNDBOARD_SOUND_DELETE handles missing sound gracefully."""
    # Setup
    state = create_mock_state()
    guild_id = 111111111
    sound_id = 444444444

    # Don't cache the sound

    # Create delete payload
    delete_data = {
        "guild_id": str(guild_id),
        "sound_id": str(sound_id),
    }

    # Emit event and capture
    capture = await emit_and_capture(state, "GUILD_SOUNDBOARD_SOUND_DELETE", delete_data)

    # Assertions - should still emit event with None sound
    capture.assert_called_once()
    capture.assert_called_with_event_type(GuildSoundboardSoundDelete)

    event = capture.get_last_event()
    assert event is not None
    assert event.sound is None
    assert event.raw.sound_id == sound_id
    assert event.raw.guild_id == guild_id
