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
from .gateway import GuildAvailable as GatewayGuildAvailable
from .gateway import GuildCreate as GatewayGuildCreate
from .gateway import GuildJoin as GatewayGuildJoin
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
from .voice import VoiceChannelStatusUpdate, VoiceServerUpdate, VoiceStateUpdate
from .webhook import WebhooksUpdate

__all__ = (
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
    "GatewayGuildAvailable",
    "GatewayGuildCreate",
    "GatewayGuildJoin",
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
    GatewayGuildAvailable,
    GatewayGuildCreate,
    GatewayGuildJoin,
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
    VoiceChannelStatusUpdate,
    VoiceServerUpdate,
    VoiceStateUpdate,
    # Webhook
    WebhooksUpdate,
]
