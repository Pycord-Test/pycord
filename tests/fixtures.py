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

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from discord.app.cache import Cache
from discord.app.state import ConnectionState
from discord.bot import Bot
from discord.channel import DMChannel, TextChannel
from discord.channel.thread import Thread
from discord.enums import ChannelType
from discord.flags import Intents
from discord.guild import Guild
from discord.http import HTTPClient
from discord.member import Member
from discord.soundboard import SoundboardSound
from discord.user import ClientUser, User


class MockCache:
    """Mock implementation of the Cache protocol for testing."""

    def __init__(self):
        self._users: dict[int, User] = {}
        self._guilds: dict[int, Guild] = {}
        self._sounds: dict[int, SoundboardSound] = {}
        self._guild_members: dict[int, dict[int, Member]] = defaultdict(dict)
        self.__state: ConnectionState | None = None

    @property
    def _state(self) -> ConnectionState:
        if self.__state is None:
            raise RuntimeError("Cache state has not been initialized.")
        return self.__state

    @_state.setter
    def _state(self, state: ConnectionState) -> None:
        self.__state = state

    # Users
    async def get_all_users(self) -> list[User]:
        return list(self._users.values())

    async def store_user(self, payload: dict[str, Any]) -> User:
        user = User(state=self._state, data=payload)
        self._users[user.id] = user
        return user

    async def delete_user(self, user_id: int) -> None:
        self._users.pop(user_id, None)

    async def get_user(self, user_id: int) -> User | None:
        return self._users.get(user_id)

    # Guilds
    async def get_all_guilds(self) -> list[Guild]:
        return list(self._guilds.values())

    async def get_guild(self, id: int) -> Guild | None:
        return self._guilds.get(id)

    async def add_guild(self, guild: Guild) -> None:
        self._guilds[guild.id] = guild

    async def delete_guild(self, guild: Guild) -> None:
        self._guilds.pop(guild.id, None)

    # Soundboard sounds
    async def get_sound(self, sound_id: int) -> SoundboardSound | None:
        return self._sounds.get(sound_id)

    async def store_sound(self, sound: SoundboardSound) -> None:
        self._sounds[sound.id] = sound

    async def delete_sound(self, sound_id: int) -> None:
        self._sounds.pop(sound_id, None)

    # Guild members
    async def store_member(self, member: Member) -> None:
        self._guild_members[member.guild.id][member.id] = member

    async def get_member(self, guild_id: int, user_id: int) -> Member | None:
        return self._guild_members[guild_id].get(user_id)

    async def delete_member(self, guild_id: int, user_id: int) -> None:
        self._guild_members[guild_id].pop(user_id, None)

    async def delete_guild_members(self, guild_id: int) -> None:
        self._guild_members.pop(guild_id, None)

    async def get_guild_members(self, guild_id: int) -> list[Member]:
        return list(self._guild_members.get(guild_id, {}).values())

    async def get_all_members(self) -> list[Member]:
        members = []
        for guild_members in self._guild_members.values():
            members.extend(guild_members.values())
        return members

    # Stubs for other required methods
    async def get_all_stickers(self) -> list:
        return []

    async def get_sticker(self, sticker_id: int):
        return None

    async def store_sticker(self, guild, data):
        return None

    async def delete_sticker(self, sticker_id: int) -> None:
        pass

    async def store_view(self, view, message_id: int | None) -> None:
        pass

    async def delete_view_on(self, message_id: int) -> None:
        pass

    async def get_all_views(self) -> list:
        return []

    async def store_modal(self, modal, user_id: int) -> None:
        pass

    async def delete_modal(self, custom_id: str) -> None:
        pass

    async def get_all_modals(self) -> list:
        return []

    async def store_guild_emoji(self, guild, data):
        return None

    async def store_app_emoji(self, application_id: int, data):
        return None

    async def get_all_emojis(self) -> list:
        return []

    async def get_emoji(self, emoji_id: int | None):
        return None

    async def delete_emoji(self, emoji) -> None:
        pass

    async def get_all_polls(self) -> list:
        return []

    async def get_poll(self, message_id: int):
        return None

    async def store_poll(self, poll, message_id: int) -> None:
        pass

    async def get_private_channels(self) -> list:
        return []

    async def get_private_channel(self, channel_id: int):
        return None

    async def get_private_channel_by_user(self, user_id: int):
        return None

    async def store_private_channel(self, channel) -> None:
        pass

    async def store_message(self, message, channel):
        return None

    async def store_built_message(self, message) -> None:
        pass

    async def upsert_message(self, message) -> None:
        pass

    async def delete_message(self, message_id: int) -> None:
        pass

    async def get_message(self, message_id: int):
        return None

    async def get_all_messages(self) -> list:
        return []


def create_mock_http() -> HTTPClient:
    """Create a mock HTTP client."""
    http = MagicMock(spec=HTTPClient)
    http.get_all_application_emojis = AsyncMock(return_value={"items": []})
    return http


def create_mock_state(*, intents: Intents | None = None, cache: Cache | None = None) -> ConnectionState:
    """Create a mock ConnectionState for testing."""
    from discord.app.event_emitter import EventEmitter
    from discord.flags import MemberCacheFlags

    if cache is None:
        cache = MockCache()

    http = create_mock_http()

    state = MagicMock(spec=ConnectionState)
    state.http = http
    state.cache = cache
    state.cache._state = state
    state.intents = intents or Intents.default()
    state.application_id = 123456789
    state.self_id = 987654321
    state.cache_app_emojis = False
    state._guilds = {}
    state._private_channels = {}
    state.member_cache_flags = MemberCacheFlags.from_intents(state.intents)

    # Create real EventEmitter
    state.emitter = EventEmitter(state)

    # Make _get_guild async
    async def _get_guild(guild_id: int) -> Guild | None:
        return await state.cache.get_guild(guild_id)

    state._get_guild = _get_guild

    # Make _add_guild async
    async def _add_guild(guild: Guild) -> None:
        await state.cache.add_guild(guild)

    state._add_guild = _add_guild

    # Make _remove_guild async
    async def _remove_guild(guild: Guild) -> None:
        await state.cache.delete_guild(guild)

    state._remove_guild = _remove_guild

    # Make store_user async
    async def store_user(payload: dict[str, Any]) -> User:
        return await state.cache.store_user(payload)

    state.store_user = store_user

    # Make _get_private_channel async
    async def _get_private_channel(channel_id: int):
        return await state.cache.get_private_channel(channel_id)

    state._get_private_channel = _get_private_channel

    return state


def create_mock_bot(*, intents: Intents | None = None, cache: Cache | None = None) -> Bot:
    """Create a mock ClientUser for testing."""
    state = create_mock_state(intents=intents, cache=cache)
    bot = Bot()
    state.emitter = bot._connection.emitter
    bot._connection = state
    return bot


def create_user_payload(user_id: int = 123456789, username: str = "TestUser") -> dict[str, Any]:
    """Create a mock user payload."""
    return {
        "id": str(user_id),
        "username": username,
        "discriminator": "0001",
        "global_name": username,
        "avatar": "abc123",
        "bot": False,
    }


def create_guild_payload(guild_id: int = 111111111, name: str = "Test Guild") -> dict[str, Any]:
    """Create a mock guild payload."""
    return {
        "id": str(guild_id),
        "name": name,
        "icon": None,
        "splash": None,
        "discovery_splash": None,
        "owner_id": "123456789",
        "afk_channel_id": None,
        "afk_timeout": 300,
        "verification_level": 0,
        "default_message_notifications": 0,
        "explicit_content_filter": 0,
        "roles": [],
        "emojis": [],
        "features": [],
        "mfa_level": 0,
        "system_channel_id": None,
        "system_channel_flags": 0,
        "rules_channel_id": None,
        "vanity_url_code": None,
        "description": None,
        "banner": None,
        "premium_tier": 0,
        "preferred_locale": "en-US",
        "public_updates_channel_id": None,
        "nsfw_level": 0,
        "premium_progress_bar_enabled": False,
    }


def create_channel_payload(
    channel_id: int = 222222222,
    guild_id: int = 111111111,
    name: str = "test-channel",
    channel_type: int = 0,
) -> dict[str, Any]:
    """Create a mock channel payload."""
    return {
        "id": str(channel_id),
        "type": channel_type,
        "guild_id": str(guild_id),
        "name": name,
        "position": 0,
        "permission_overwrites": [],
        "nsfw": False,
        "parent_id": None,
    }


def create_thread_payload(
    thread_id: int = 333333333,
    guild_id: int = 111111111,
    parent_id: int = 222222222,
    name: str = "test-thread",
    owner_id: int = 123456789,
) -> dict[str, Any]:
    """Create a mock thread payload."""
    return {
        "id": str(thread_id),
        "type": ChannelType.public_thread.value,
        "guild_id": str(guild_id),
        "name": name,
        "parent_id": str(parent_id),
        "owner_id": str(owner_id),
        "thread_metadata": {
            "archived": False,
            "auto_archive_duration": 1440,
            "archive_timestamp": datetime.now(timezone.utc).isoformat(),
            "locked": False,
            "create_timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "message_count": 0,
        "member_count": 1,
    }


def create_soundboard_sound_payload(
    sound_id: int = 444444444,
    guild_id: int = 111111111,
    name: str = "test-sound",
    emoji_name: str | None = None,
) -> dict[str, Any]:
    """Create a mock soundboard sound payload."""
    payload = {
        "sound_id": str(sound_id),
        "name": name,
        "volume": 1.0,
        "guild_id": str(guild_id),
        "available": True,
    }
    if emoji_name:
        payload["emoji_name"] = emoji_name
    return payload


def create_member_payload(
    user_id: int = 123456789,
    guild_id: int = 111111111,
    username: str = "TestUser",
    roles: list[str] | None = None,
) -> dict[str, Any]:
    """Create a mock member payload."""
    return {
        "user": create_user_payload(user_id, username),
        "nick": None,
        "roles": roles or [],
        "joined_at": datetime.now(timezone.utc).isoformat(),
        "premium_since": None,
        "deaf": False,
        "mute": False,
    }
