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

from typing import TYPE_CHECKING, Any

from typing_extensions import Self, override

from ..app.event_emitter import Event
from ..raw_models import RawSoundboardSoundDeleteEvent
from ..soundboard import SoundboardSound

if TYPE_CHECKING:
    from ..app.state import ConnectionState

__all__ = (
    "SoundboardSounds",
    "GuildSoundboardSoundsUpdate",
    "GuildSoundboardSoundUpdate",
    "GuildSoundboardSoundCreate",
    "GuildSoundboardSoundDelete",
)


class SoundboardSounds(Event):
    __event_name__: str = "SOUNDBOARD_SOUNDS"

    def __init__(self, guild_id: int, sounds: list[SoundboardSound]) -> None:
        self.guild_id: int = guild_id
        self.sounds: list[SoundboardSound] = sounds

    @classmethod
    @override
    async def __load__(cls, data: Any, state: "ConnectionState") -> Self | None:
        guild_id = int(data["guild_id"])
        sounds: list[SoundboardSound] = []
        for sound_data in data["soundboard_sounds"]:
            sound = SoundboardSound(state=state, http=state.http, data=sound_data)
            await state.cache.store_sound(sound)
            sounds.append(sound)
        return cls(guild_id, sounds)


class GuildSoundboardSoundsUpdate(Event):
    """Called when multiple guild soundboard sounds are updated at once.

    This is called, for example, when a guild loses a boost level and some sounds become unavailable.

    Attributes
    ----------
    old_sounds: list[:class:`SoundboardSound`] | None
        The soundboard sounds prior to being updated (only if all were cached).
    new_sounds: list[:class:`SoundboardSound`]
        The soundboard sounds after being updated.
    """

    __event_name__: str = "GUILD_SOUNDBOARD_SOUNDS_UPDATE"

    def __init__(
        self,
        before_sounds: list[SoundboardSound],
        after_sounds: list[SoundboardSound],
    ) -> None:
        self.before: list[SoundboardSound] = before_sounds
        self.after: list[SoundboardSound] = after_sounds

    @classmethod
    @override
    async def __load__(cls, data: Any, state: "ConnectionState") -> Self | None:
        before_sounds: list[SoundboardSound] = []
        after_sounds: list[SoundboardSound] = []
        for sound_data in data["soundboard_sounds"]:
            after = SoundboardSound(state=state, http=state.http, data=sound_data)
            if before := await state.cache.get_sound(after.id):
                before_sounds.append(before)
            await state.cache.store_sound(after)
            after_sounds.append(after)

        if len(before_sounds) == len(after_sounds):
            return cls(before_sounds, after_sounds)
        return None


class GuildSoundboardSoundUpdate(Event):
    """Called when a soundboard sound is updated.

    Attributes
    ----------
    old: :class:`SoundboardSound` | None
        The soundboard sound prior to being updated (if it was cached).
    new: :class:`SoundboardSound`
        The soundboard sound after being updated.
    """

    __event_name__: str = "GUILD_SOUNDBOARD_SOUND_UPDATE"

    def __init__(self, before: SoundboardSound, after: SoundboardSound) -> None:
        self.before: SoundboardSound = before
        self.after: SoundboardSound = after

    @classmethod
    @override
    async def __load__(cls, data: Any, state: "ConnectionState") -> Self | None:
        after = SoundboardSound(state=state, http=state.http, data=data)
        before = await state.cache.get_sound(after.id)
        await state.cache.store_sound(after)
        if before:
            return cls(before, after)
        return None


class GuildSoundboardSoundCreate(Event):
    """Called when a soundboard sound is created.

    This event inherits from :class:`SoundboardSound`.
    """

    __event_name__: str = "GUILD_SOUNDBOARD_SOUND_CREATE"

    def __init__(self, sound: SoundboardSound) -> None:
        self.sound: SoundboardSound = sound

    @classmethod
    @override
    async def __load__(cls, data: Any, state: "ConnectionState") -> Self | None:
        sound = SoundboardSound(state=state, http=state.http, data=data)
        await state.cache.store_sound(sound)
        return cls(sound)


class GuildSoundboardSoundDelete(Event):
    """Called when a soundboard sound is deleted.

    Attributes
    ----------
    raw: :class:`RawSoundboardSoundDeleteEvent`
        The raw event payload data.
    sound: :class:`SoundboardSound` | None
        The deleted sound (if it was cached).
    """

    __event_name__: str = "GUILD_SOUNDBOARD_SOUND_DELETE"

    def __init__(self, sound: SoundboardSound | None, raw: RawSoundboardSoundDeleteEvent) -> None:
        self.sound: SoundboardSound | None = sound
        self.raw: RawSoundboardSoundDeleteEvent = raw

    @classmethod
    @override
    async def __load__(cls, data: Any, state: "ConnectionState") -> Self | None:
        sound_id = int(data["sound_id"])
        sound = await state.cache.get_sound(sound_id)
        if sound is not None:
            await state.cache.delete_sound(sound_id)
        raw = RawSoundboardSoundDeleteEvent(data)
        return cls(sound, raw)
