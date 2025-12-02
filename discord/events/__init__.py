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

from ..app.event_emitter import Event
from .audit_log import GuildAuditLogEntryCreate
from .automod import (
    AutoModActionExecution,
    AutoModRuleCreate,
    AutoModRuleDelete,
    AutoModRuleUpdate,
)
from .channel import (
    ChannelCreate,
    ChannelDelete,
    ChannelPinsUpdate,
    ChannelUpdate,
    GuildChannelUpdate,
    PrivateChannelUpdate,
)
from .entitlement import EntitlementCreate, EntitlementDelete, EntitlementUpdate
from .gateway import (
    ApplicationCommandPermissionsUpdate,
    PresenceUpdate,
    Ready,
    Resumed,
    UserUpdate,
    _CacheAppEmojis,
)
from .guild import (
    GuildAvailable,
    GuildBanAdd,
    GuildBanRemove,
    GuildCreate,
    GuildDelete,
    GuildEmojisUpdate,
    GuildJoin,
    GuildMemberJoin,
    GuildMemberRemove,
    GuildMembersChunk,
    GuildMemberUpdate,
    GuildRoleCreate,
    GuildRoleDelete,
    GuildRoleUpdate,
    GuildStickersUpdate,
    GuildUnavailable,
    GuildUpdate,
)
from .integration import (
    GuildIntegrationsUpdate,
    IntegrationCreate,
    IntegrationDelete,
    IntegrationUpdate,
)
from .interaction import InteractionCreate
from .invite import InviteCreate, InviteDelete
from .message import (
    MessageCreate,
    MessageDelete,
    MessageDeleteBulk,
    MessageUpdate,
    PollVoteAdd,
    PollVoteRemove,
    ReactionAdd,
    ReactionClear,
    ReactionRemove,
    ReactionRemoveEmoji,
)
from .scheduled_event import (
    GuildScheduledEventCreate,
    GuildScheduledEventDelete,
    GuildScheduledEventUpdate,
    GuildScheduledEventUserAdd,
    GuildScheduledEventUserRemove,
)
from .soundboard import (
    GuildSoundboardSoundCreate,
    GuildSoundboardSoundDelete,
    GuildSoundboardSoundsUpdate,
    GuildSoundboardSoundUpdate,
    SoundboardSounds,
)
from .stage_instance import StageInstanceCreate, StageInstanceDelete, StageInstanceUpdate
from .subscription import SubscriptionCreate, SubscriptionDelete, SubscriptionUpdate
from .thread import (
    BulkThreadMemberUpdate,
    ThreadCreate,
    ThreadDelete,
    ThreadJoin,
    ThreadListSync,
    ThreadMemberJoin,
    ThreadMemberRemove,
    ThreadMemberUpdate,
    ThreadRemove,
    ThreadUpdate,
)
from .typing import TypingStart
from .voice import VoiceChannelEffectSend, VoiceChannelStatusUpdate, VoiceServerUpdate, VoiceStateUpdate
from .webhook import WebhooksUpdate

__all__ = (
    "ALL_EVENTS",
    "Event",
    # Audit Log
    "GuildAuditLogEntryCreate",
    # AutoMod
    "AutoModActionExecution",
    "AutoModRuleCreate",
    "AutoModRuleDelete",
    "AutoModRuleUpdate",
    # Channel
    "ChannelCreate",
    "ChannelDelete",
    "ChannelPinsUpdate",
    "ChannelUpdate",
    "GuildChannelUpdate",
    "PrivateChannelUpdate",
    # Entitlement
    "EntitlementCreate",
    "EntitlementDelete",
    "EntitlementUpdate",
    # Gateway
    "ApplicationCommandPermissionsUpdate",
    "PresenceUpdate",
    "Ready",
    "Resumed",
    "UserUpdate",
    "_CacheAppEmojis",
    # Guild
    "GuildAvailable",
    "GuildBanAdd",
    "GuildBanRemove",
    "GuildCreate",
    "GuildDelete",
    "GuildEmojisUpdate",
    "GuildJoin",
    "GuildMemberJoin",
    "GuildMemberRemove",
    "GuildMembersChunk",
    "GuildMemberUpdate",
    "GuildRoleCreate",
    "GuildRoleDelete",
    "GuildRoleUpdate",
    "GuildStickersUpdate",
    "GuildUnavailable",
    "GuildUpdate",
    # Integration
    "GuildIntegrationsUpdate",
    "IntegrationCreate",
    "IntegrationDelete",
    "IntegrationUpdate",
    # Interaction
    "InteractionCreate",
    # Invite
    "InviteCreate",
    "InviteDelete",
    # Message
    "MessageCreate",
    "MessageDelete",
    "MessageDeleteBulk",
    "MessageUpdate",
    "PollVoteAdd",
    "PollVoteRemove",
    "ReactionAdd",
    "ReactionClear",
    "ReactionRemove",
    "ReactionRemoveEmoji",
    # Scheduled Event
    "GuildScheduledEventCreate",
    "GuildScheduledEventDelete",
    "GuildScheduledEventUpdate",
    "GuildScheduledEventUserAdd",
    "GuildScheduledEventUserRemove",
    # Soundboard
    "GuildSoundboardSoundCreate",
    "GuildSoundboardSoundDelete",
    "GuildSoundboardSoundsUpdate",
    "GuildSoundboardSoundUpdate",
    "SoundboardSounds",
    # Stage Instance
    "StageInstanceCreate",
    "StageInstanceDelete",
    "StageInstanceUpdate",
    # Subscription
    "SubscriptionCreate",
    "SubscriptionDelete",
    "SubscriptionUpdate",
    # Thread
    "BulkThreadMemberUpdate",
    "ThreadCreate",
    "ThreadDelete",
    "ThreadJoin",
    "ThreadListSync",
    "ThreadMemberJoin",
    "ThreadMemberRemove",
    "ThreadMemberUpdate",
    "ThreadRemove",
    "ThreadUpdate",
    # Typing
    "TypingStart",
    # Voice
    "VoiceChannelEffectSend",
    "VoiceChannelStatusUpdate",
    "VoiceServerUpdate",
    "VoiceStateUpdate",
    # Webhook
    "WebhooksUpdate",
)

ALL_EVENTS: list[type[Event]] = [
    # Audit Log
    GuildAuditLogEntryCreate,
    # AutoMod
    AutoModActionExecution,
    AutoModRuleCreate,
    AutoModRuleDelete,
    AutoModRuleUpdate,
    # Channel
    ChannelCreate,
    ChannelDelete,
    ChannelPinsUpdate,
    ChannelUpdate,
    GuildChannelUpdate,
    PrivateChannelUpdate,
    # Entitlement
    EntitlementCreate,
    EntitlementDelete,
    EntitlementUpdate,
    # Gateway
    ApplicationCommandPermissionsUpdate,
    PresenceUpdate,
    Ready,
    Resumed,
    UserUpdate,
    _CacheAppEmojis,
    # Guild
    GuildAvailable,
    GuildBanAdd,
    GuildBanRemove,
    GuildCreate,
    GuildDelete,
    GuildEmojisUpdate,
    GuildJoin,
    GuildMemberJoin,
    GuildMemberRemove,
    GuildMembersChunk,
    GuildMemberUpdate,
    GuildRoleCreate,
    GuildRoleDelete,
    GuildRoleUpdate,
    GuildStickersUpdate,
    GuildUnavailable,
    GuildUpdate,
    # Integration
    GuildIntegrationsUpdate,
    IntegrationCreate,
    IntegrationDelete,
    IntegrationUpdate,
    # Interaction
    InteractionCreate,
    # Invite
    InviteCreate,
    InviteDelete,
    # Message
    MessageCreate,
    MessageDelete,
    MessageDeleteBulk,
    MessageUpdate,
    PollVoteAdd,
    PollVoteRemove,
    ReactionAdd,
    ReactionClear,
    ReactionRemove,
    ReactionRemoveEmoji,
    # Scheduled Event
    GuildScheduledEventCreate,
    GuildScheduledEventDelete,
    GuildScheduledEventUpdate,
    GuildScheduledEventUserAdd,
    GuildScheduledEventUserRemove,
    # Soundboard
    GuildSoundboardSoundCreate,
    GuildSoundboardSoundDelete,
    GuildSoundboardSoundsUpdate,
    GuildSoundboardSoundUpdate,
    SoundboardSounds,
    # Stage Instance
    StageInstanceCreate,
    StageInstanceDelete,
    StageInstanceUpdate,
    # Subscription
    SubscriptionCreate,
    SubscriptionDelete,
    SubscriptionUpdate,
    # Thread
    BulkThreadMemberUpdate,
    ThreadCreate,
    ThreadDelete,
    ThreadJoin,
    ThreadListSync,
    ThreadMemberJoin,
    ThreadMemberRemove,
    ThreadMemberUpdate,
    ThreadRemove,
    ThreadUpdate,
    # Typing
    TypingStart,
    # Voice
    VoiceChannelEffectSend,
    VoiceChannelStatusUpdate,
    VoiceServerUpdate,
    VoiceStateUpdate,
    # Webhook
    WebhooksUpdate,
]
