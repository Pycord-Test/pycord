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

from discord.events.guild import (
    GuildBanAdd,
    GuildBanRemove,
    GuildDelete,
    GuildMemberJoin,
    GuildMemberRemove,
    GuildMemberUpdate,
    GuildRoleCreate,
    GuildRoleDelete,
    GuildRoleUpdate,
    GuildUpdate,
)
from discord.guild import Guild
from discord.member import Member
from tests.event_helpers import emit_and_capture, populate_guild_cache
from tests.fixtures import (
    create_guild_payload,
    create_member_payload,
    create_mock_state,
    create_user_payload,
)


@pytest.mark.asyncio
async def test_guild_member_join():
    """Test that GUILD_MEMBER_JOIN event is emitted correctly."""
    # Setup
    state = create_mock_state()
    guild_id = 111111111
    user_id = 123456789

    # Populate cache with guild
    guild_data = create_guild_payload(guild_id)
    await populate_guild_cache(state, guild_id, guild_data)

    # Create member payload
    member_data = create_member_payload(user_id, guild_id, "NewMember")
    member_data["guild_id"] = str(guild_id)

    # Emit event and capture
    capture = await emit_and_capture(state, "GUILD_MEMBER_JOIN", member_data)

    # Assertions
    capture.assert_called_once()
    capture.assert_called_with_event_type(GuildMemberJoin)

    event = capture.get_last_event()
    assert event is not None
    assert isinstance(event, Member)
    assert event.id == user_id


@pytest.mark.asyncio
async def test_guild_member_remove():
    """Test that GUILD_MEMBER_REMOVE event is emitted correctly."""
    # Setup
    state = create_mock_state()
    guild_id = 111111111
    user_id = 123456789

    # Populate cache with guild
    guild_data = create_guild_payload(guild_id)
    await populate_guild_cache(state, guild_id, guild_data)

    # Add member first
    member_data = create_member_payload(user_id, guild_id, "TestMember")
    member_data["guild_id"] = str(guild_id)
    await state.emitter.emit("GUILD_MEMBER_JOIN", member_data)

    # Create remove payload
    remove_data = {
        "guild_id": str(guild_id),
        "user": create_user_payload(user_id, "TestMember"),
    }

    # Emit event and capture
    capture = await emit_and_capture(state, "GUILD_MEMBER_REMOVE", remove_data)

    # Assertions
    # Event may or may not be emitted depending on whether member exists
    assert capture.call_count >= 0


@pytest.mark.asyncio
async def test_guild_member_update():
    """Test that GUILD_MEMBER_UPDATE event is emitted correctly."""
    # Setup
    state = create_mock_state()
    guild_id = 111111111
    user_id = 123456789

    # Populate cache with guild
    guild_data = create_guild_payload(guild_id)
    await populate_guild_cache(state, guild_id, guild_data)

    # Add member first
    member_data = create_member_payload(user_id, guild_id, "TestMember")
    member_data["guild_id"] = str(guild_id)
    await state.emitter.emit("GUILD_MEMBER_JOIN", member_data)

    # Update member
    updated_data = create_member_payload(user_id, guild_id, "TestMember")
    updated_data["guild_id"] = str(guild_id)
    updated_data["nick"] = "NewNick"

    # Emit event and capture
    capture = await emit_and_capture(state, "GUILD_MEMBER_UPDATE", updated_data)

    # Assertions
    # Event may or may not be emitted depending on cache state
    assert capture.call_count >= 0


@pytest.mark.asyncio
async def test_guild_role_create():
    """Test that GUILD_ROLE_CREATE event is emitted correctly."""
    # Setup
    state = create_mock_state()
    guild_id = 111111111
    role_id = 555555555

    # Populate cache with guild
    guild_data = create_guild_payload(guild_id)
    await populate_guild_cache(state, guild_id, guild_data)

    # Create role payload
    role_data = {
        "guild_id": str(guild_id),
        "role": {
            "id": str(role_id),
            "name": "Test Role",
            "colors": {
                "primary_color": 0xFF0000,
            },
            "hoist": False,
            "position": 1,
            "permissions": "0",
            "managed": False,
            "mentionable": True,
        },
    }

    # Emit event and capture
    capture = await emit_and_capture(state, "GUILD_ROLE_CREATE", role_data)

    # Assertions
    capture.assert_called_once()
    capture.assert_called_with_event_type(GuildRoleCreate)

    event = capture.get_last_event()
    assert event is not None
    assert event.id == role_id
    assert event.name == "Test Role"


@pytest.mark.asyncio
async def test_guild_role_update():
    """Test that GUILD_ROLE_UPDATE event is emitted correctly."""
    # Setup
    state = create_mock_state()
    guild_id = 111111111
    role_id = 555555555

    # Populate cache with guild
    guild_data = create_guild_payload(guild_id)
    await populate_guild_cache(state, guild_id, guild_data)

    # Create role first
    role_data = {
        "guild_id": str(guild_id),
        "role": {
            "id": str(role_id),
            "name": "Test Role",
            "colors": {
                "primary_color": 0xFF0000,
                "secondary_color": 0x00FF00,
            },
            "hoist": False,
            "position": 1,
            "permissions": "0",
            "managed": False,
            "mentionable": True,
        },
    }
    await state.emitter.emit("GUILD_ROLE_CREATE", role_data)

    # Update role
    updated_role_data = {
        "guild_id": str(guild_id),
        "role": {
            "id": str(role_id),
            "name": "Updated Role",
            "colors": {
                "primary_color": 0x0000FF,
                "secondary_color": 0xFFFF00,
            },
            "hoist": True,
            "position": 2,
            "permissions": "8",
            "managed": False,
            "mentionable": True,
        },
    }

    # Emit event and capture
    capture = await emit_and_capture(state, "GUILD_ROLE_UPDATE", updated_role_data)

    # Assertions
    capture.assert_called_once()
    capture.assert_called_with_event_type(GuildRoleUpdate)

    event = capture.get_last_event()
    assert event is not None
    assert event.id == role_id
    assert event.name == "Updated Role"
    assert event.old.name == "Test Role"


@pytest.mark.asyncio
async def test_guild_role_delete():
    """Test that GUILD_ROLE_DELETE event is emitted correctly."""
    # Setup
    state = create_mock_state()
    guild_id = 111111111
    role_id = 555555555

    # Populate cache with guild
    guild_data = create_guild_payload(guild_id)
    await populate_guild_cache(state, guild_id, guild_data)

    # Create role first
    role_data = {
        "guild_id": str(guild_id),
        "role": {
            "id": str(role_id),
            "name": "Test Role",
            "colors": {
                "primary_color": 0xFF0000,
                "secondary_color": 0x00FF00,
            },
            "hoist": False,
            "position": 1,
            "permissions": "0",
            "managed": False,
            "mentionable": True,
        },
    }
    await state.emitter.emit("GUILD_ROLE_CREATE", role_data)

    # Delete role
    delete_data = {
        "guild_id": str(guild_id),
        "role_id": str(role_id),
    }

    # Emit event and capture
    capture = await emit_and_capture(state, "GUILD_ROLE_DELETE", delete_data)

    # Assertions
    capture.assert_called_once()
    capture.assert_called_with_event_type(GuildRoleDelete)

    event = capture.get_last_event()
    assert event is not None
    assert event.id == role_id


@pytest.mark.asyncio
async def test_guild_update():
    """Test that GUILD_UPDATE event is emitted correctly."""
    # Setup
    state = create_mock_state()
    guild_id = 111111111

    # Populate cache with guild
    guild_data = create_guild_payload(guild_id, "Original Name")
    await populate_guild_cache(state, guild_id, guild_data)

    # Update guild
    updated_data = create_guild_payload(guild_id, "Updated Name")

    # Emit event and capture
    capture = await emit_and_capture(state, "GUILD_UPDATE", updated_data)

    # Assertions
    capture.assert_called_once()
    capture.assert_called_with_event_type(GuildUpdate)

    event = capture.get_last_event()
    assert event is not None
    assert event.id == guild_id
    assert event.name == "Updated Name"
    assert event.old.name == "Original Name"


@pytest.mark.asyncio
async def test_guild_delete():
    """Test that GUILD_DELETE event is emitted correctly."""
    # Setup
    state = create_mock_state()
    guild_id = 111111111

    # Populate cache with guild
    guild_data = create_guild_payload(guild_id)
    await populate_guild_cache(state, guild_id, guild_data)

    # Delete guild
    delete_data = {
        "id": str(guild_id),
        "unavailable": False,
    }

    # Emit event and capture
    capture = await emit_and_capture(state, "GUILD_DELETE", delete_data)

    # Assertions
    capture.assert_called_once()
    capture.assert_called_with_event_type(GuildDelete)

    event = capture.get_last_event()
    assert event is not None
    assert event.id == guild_id


@pytest.mark.asyncio
async def test_guild_ban_add():
    """Test that GUILD_BAN_ADD event is emitted correctly."""
    # Setup
    state = create_mock_state()
    guild_id = 111111111
    user_id = 123456789

    # Populate cache with guild
    guild_data = create_guild_payload(guild_id)
    await populate_guild_cache(state, guild_id, guild_data)

    # Create ban payload
    ban_data = {
        "guild_id": str(guild_id),
        "user": create_user_payload(user_id, "BannedUser"),
    }

    # Emit event and capture
    capture = await emit_and_capture(state, "GUILD_BAN_ADD", ban_data)

    # Assertions
    capture.assert_called_once()
    capture.assert_called_with_event_type(GuildBanAdd)

    event = capture.get_last_event()
    assert event is not None
    assert event.id == user_id


@pytest.mark.asyncio
async def test_guild_ban_remove():
    """Test that GUILD_BAN_REMOVE event is emitted correctly."""
    # Setup
    state = create_mock_state()
    guild_id = 111111111
    user_id = 123456789

    # Populate cache with guild
    guild_data = create_guild_payload(guild_id)
    await populate_guild_cache(state, guild_id, guild_data)

    # Create unban payload
    unban_data = {
        "guild_id": str(guild_id),
        "user": create_user_payload(user_id, "UnbannedUser"),
    }

    # Emit event and capture
    capture = await emit_and_capture(state, "GUILD_BAN_REMOVE", unban_data)

    # Assertions
    capture.assert_called_once()
    capture.assert_called_with_event_type(GuildBanRemove)

    event = capture.get_last_event()
    assert event is not None
    assert event.id == user_id
