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

from __future__ import annotations

from datetime import timedelta
from functools import cached_property
from typing import TYPE_CHECKING

from . import utils
from .enums import (
    AutoModActionType,
    AutoModEventType,
    AutoModKeywordPresetType,
    AutoModTriggerType,
    try_enum,
)
from .mixins import Hashable
from .object import Object

__all__ = (
    "AutoModRule",
    "AutoModAction",
    "AutoModActionMetadata",
    "AutoModTriggerMetadata",
)

if TYPE_CHECKING:
    from .abc import Snowflake
    from .channel import ForumChannel, TextChannel, VoiceChannel
    from .guild import Guild
    from .member import Member
    from .role import Role
    from .state import ConnectionState
    from .types.automod import AutoModAction as AutoModActionPayload
    from .types.automod import AutoModActionMetadata as AutoModActionMetadataPayload
    from .types.automod import AutoModRule as AutoModRulePayload
    from .types.automod import AutoModTriggerMetadata as AutoModTriggerMetadataPayload

MISSING = utils.MISSING


class AutoModActionMetadata:
    """Represents an action's metadata.

    Depending on the action's type, different attributes will be used.

    .. versionadded:: 2.0

    Attributes
    ----------
    channel_id: :class:`int`
        The ID of the channel to send the message to.
        Only for actions of type :attr:`AutoModActionType.send_alert_message`.
    timeout_duration: :class:`datetime.timedelta`
        How long the member that triggered the action should be timed out for.
        Only for actions of type :attr:`AutoModActionType.timeout`.
    custom_message: :class:`str`
        An additional message shown to members when their message is blocked.
        Maximum 150 characters.
        Only for actions of type :attr:`AutoModActionType.block_message`.
    """

    # maybe add a table of action types and attributes?

    __slots__ = (
        "channel_id",
        "timeout_duration",
        "custom_message",
    )

    def __init__(
        self,
        channel_id: int | utils.Undefined = MISSING,
        timeout_duration: timedelta | utils.Undefined = MISSING,
        custom_message: str | utils.Undefined = MISSING,
    ):
        self.channel_id: int = channel_id
        self.timeout_duration: timedelta = timeout_duration
        self.custom_message: str = custom_message

    def to_dict(self) -> dict:
        data = {}

        if self.channel_id is not MISSING:
            data["channel_id"] = self.channel_id

        if self.timeout_duration is not MISSING:
            data["duration_seconds"] = self.timeout_duration.total_seconds()

        if self.custom_message is not MISSING:
            data["custom_message"] = self.custom_message

        return data

    @classmethod
    def from_dict(cls, data: AutoModActionMetadataPayload):
        kwargs = {}

        if (channel_id := data.get("channel_id")) is not None:
            kwargs["channel_id"] = int(channel_id)

        if (duration_seconds := data.get("duration_seconds")) is not None:
            # might need an explicit int cast
            kwargs["timeout_duration"] = timedelta(seconds=duration_seconds)

        if (custom_message := data.get("custom_message")) is not None:
            kwargs["custom_message"] = custom_message

        return cls(**kwargs)

    def __repr__(self) -> str:
        repr_attrs = (
            "channel_id",
            "timeout_duration",
            "custom_message",
        )
        inner = []

        for attr in repr_attrs:
            if (value := getattr(self, attr)) is not MISSING:
                inner.append(f"{attr}={value}")
        inner = " ".join(inner)

        return f"<AutoModActionMetadata {inner}>"


class AutoModAction:
    """Represents an action for a guild's auto moderation rule.

    .. versionadded:: 2.0

    Attributes
    ----------
    type: :class:`AutoModActionType`
        The action's type.
    metadata: :class:`AutoModActionMetadata`
        The action's metadata.
    """

    # note that AutoModActionType.timeout is only valid for trigger type 1?

    __slots__ = (
        "type",
        "metadata",
    )

    def __init__(self, action_type: AutoModActionType, metadata: AutoModActionMetadata):
        self.type: AutoModActionType = action_type
        self.metadata: AutoModActionMetadata = metadata

    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "metadata": self.metadata.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: AutoModActionPayload):
        return cls(
            try_enum(AutoModActionType, data["type"]),
            AutoModActionMetadata.from_dict(data["metadata"]),
        )

    def __repr__(self) -> str:
        return f"<AutoModAction type={self.type}>"


class AutoModTriggerMetadata:
    r"""Represents a rule's trigger metadata, defining additional data used to determine when a rule triggers.

    Depending on the trigger type, different metadata attributes will be used:

    +-----------------------------+--------------------------------------------------------------------------------+
    |   Attribute                 |   Trigger Types                                                                |
    +=============================+================================================================================+
    | :attr:`keyword_filter`      | :attr:`AutoModTriggerType.keyword`                                             |
    +-----------------------------+--------------------------------------------------------------------------------+
    | :attr:`regex_patterns`      | :attr:`AutoModTriggerType.keyword`                                             |
    +-----------------------------+--------------------------------------------------------------------------------+
    | :attr:`presets`             | :attr:`AutoModTriggerType.keyword_preset`                                      |
    +-----------------------------+--------------------------------------------------------------------------------+
    | :attr:`allow_list`          | :attr:`AutoModTriggerType.keyword`\, :attr:`AutoModTriggerType.keyword_preset` |
    +-----------------------------+--------------------------------------------------------------------------------+
    | :attr:`mention_total_limit` | :attr:`AutoModTriggerType.mention_spam`                                        |
    +-----------------------------+--------------------------------------------------------------------------------+

    Each attribute has limits that may change based on the trigger type.
    See `here <https://discord.com/developers/docs/resources/auto-moderation#auto-moderation-rule-object-trigger-metadata-field-limits>`_
    for information on attribute limits.

    .. versionadded:: 2.0

    Attributes
    ----------
    keyword_filter: List[:class:`str`]
        A list of substrings to filter.

    regex_patterns: List[:class:`str`]
        A list of regex patterns to filter using Rust-flavored regex, which is not
        fully compatible with regex syntax supported by the builtin `re` module.

        .. versionadded:: 2.4

    presets: List[:class:`AutoModKeywordPresetType`]
        A list of preset keyword sets to filter.

    allow_list: List[:class:`str`]
        A list of substrings to allow, overriding keyword and regex matches.

        .. versionadded:: 2.4

    mention_total_limit: :class:`int`
        The total number of unique role and user mentions allowed.

        .. versionadded:: 2.4
    """

    __slots__ = (
        "keyword_filter",
        "regex_patterns",
        "presets",
        "allow_list",
        "mention_total_limit",
    )

    def __init__(
        self,
        keyword_filter: list[str] | utils.Undefined = MISSING,
        regex_patterns: list[str] | utils.Undefined = MISSING,
        presets: list[AutoModKeywordPresetType] | utils.Undefined = MISSING,
        allow_list: list[str] | utils.Undefined = MISSING,
        mention_total_limit: int | utils.Undefined = MISSING,
    ):
        self.keyword_filter = keyword_filter
        self.regex_patterns = regex_patterns
        self.presets = presets
        self.allow_list = allow_list
        self.mention_total_limit = mention_total_limit

    def to_dict(self) -> dict:
        data = {}

        if self.keyword_filter is not MISSING:
            data["keyword_filter"] = self.keyword_filter

        if self.regex_patterns is not MISSING:
            data["regex_patterns"] = self.regex_patterns

        if self.presets is not MISSING:
            data["presets"] = [wordset.value for wordset in self.presets]

        if self.allow_list is not MISSING:
            data["allow_list"] = self.allow_list

        if self.mention_total_limit is not MISSING:
            data["mention_total_limit"] = self.mention_total_limit

        return data

    @classmethod
    def from_dict(cls, data: AutoModTriggerMetadataPayload):
        kwargs = {}

        if (keyword_filter := data.get("keyword_filter")) is not None:
            kwargs["keyword_filter"] = keyword_filter

        if (regex_patterns := data.get("regex_patterns")) is not None:
            kwargs["regex_patterns"] = regex_patterns

        if (presets := data.get("presets")) is not None:
            kwargs["presets"] = [
                try_enum(AutoModKeywordPresetType, wordset) for wordset in presets
            ]

        if (allow_list := data.get("allow_list")) is not None:
            kwargs["allow_list"] = allow_list

        if (mention_total_limit := data.get("mention_total_limit")) is not None:
            kwargs["mention_total_limit"] = mention_total_limit

        return cls(**kwargs)

    def __repr__(self) -> str:
        repr_attrs = (
            "keyword_filter",
            "regex_patterns",
            "presets",
            "allow_list",
            "mention_total_limit",
        )
        inner = []

        for attr in repr_attrs:
            if (value := getattr(self, attr)) is not MISSING:
                inner.append(f"{attr}={value}")
        inner = " ".join(inner)

        return f"<AutoModTriggerMetadata {inner}>"


class AutoModRule(Hashable):
    """Represents a guild's auto moderation rule.

    .. versionadded:: 2.0

    .. container:: operations

        .. describe:: x == y

            Checks if two rules are equal.

        .. describe:: x != y

            Checks if two rules are not equal.

        .. describe:: hash(x)

            Returns the rule's hash.

        .. describe:: str(x)

            Returns the rule's name.

    Attributes
    ----------
    id: :class:`int`
        The rule's ID.
    name: :class:`str`
        The rule's name.
    creator_id: :class:`int`
        The ID of the user who created this rule.
    event_type: :class:`AutoModEventType`
        Indicates in what context the rule is checked.
    trigger_type: :class:`AutoModTriggerType`
        Indicates what type of information is checked to determine whether the rule is triggered.
    trigger_metadata: :class:`AutoModTriggerMetadata`
        The rule's trigger metadata.
    actions: List[:class:`AutoModAction`]
        The actions to perform when the rule is triggered.
    enabled: :class:`bool`
        Whether this rule is enabled.
    exempt_role_ids: List[:class:`int`]
        The IDs of the roles that are exempt from this rule.
    exempt_channel_ids: List[:class:`int`]
        The IDs of the channels that are exempt from this rule.
    """

    __slots__ = (
        "__dict__",
        "_state",
        "id",
        "guild_id",
        "name",
        "creator_id",
        "event_type",
        "trigger_type",
        "trigger_metadata",
        "actions",
        "enabled",
        "exempt_role_ids",
        "exempt_channel_ids",
    )

    def __init__(
        self,
        *,
        state: ConnectionState,
        data: AutoModRulePayload,
    ):
        self._state: ConnectionState = state
        self.id: int = int(data["id"])
        self.guild_id: int = int(data["guild_id"])
        self.name: str = data["name"]
        self.creator_id: int = int(data["creator_id"])
        self.event_type: AutoModEventType = try_enum(
            AutoModEventType, data["event_type"]
        )
        self.trigger_type: AutoModTriggerType = try_enum(
            AutoModTriggerType, data["trigger_type"]
        )
        self.trigger_metadata: AutoModTriggerMetadata = (
            AutoModTriggerMetadata.from_dict(data["trigger_metadata"])
        )
        self.actions: list[AutoModAction] = [
            AutoModAction.from_dict(d) for d in data["actions"]
        ]
        self.enabled: bool = data["enabled"]
        self.exempt_role_ids: list[int] = [int(r) for r in data["exempt_roles"]]
        self.exempt_channel_ids: list[int] = [int(c) for c in data["exempt_channels"]]

    def __repr__(self) -> str:
        return f"<AutoModRule name={self.name} id={self.id}>"

    def __str__(self) -> str:
        return self.name

    @cached_property
    def guild(self) -> Guild | None:
        """The guild this rule belongs to."""
        return self._state._get_guild(self.guild_id)

    @cached_property
    def creator(self) -> Member | None:
        """The member who created this rule."""
        if self.guild is None:
            return None
        return self.guild.get_member(self.creator_id)

    @cached_property
    def exempt_roles(self) -> list[Role | Object]:
        """The roles that are exempt
        from this rule.

        If a role is not found in the guild's cache,
        then it will be returned as an :class:`Object`.
        """
        if self.guild is None:
            return [Object(role_id) for role_id in self.exempt_role_ids]
        return [
            self.guild.get_role(role_id) or Object(role_id)
            for role_id in self.exempt_role_ids
        ]

    @cached_property
    def exempt_channels(
        self,
    ) -> list[TextChannel | ForumChannel | VoiceChannel | Object]:
        """The channels that are exempt from this rule.

        If a channel is not found in the guild's cache,
        then it will be returned as an :class:`Object`.
        """
        if self.guild is None:
            return [Object(channel_id) for channel_id in self.exempt_channel_ids]
        return [
            self.guild.get_channel(channel_id) or Object(channel_id)
            for channel_id in self.exempt_channel_ids
        ]

    async def delete(self, reason: str | None = None) -> None:
        """|coro|

        Deletes this rule.

        Parameters
        ----------
        reason: Optional[:class:`str`]
            The reason for deleting this rule. Shows up in the audit log.

        Raises
        ------
        Forbidden
            You do not have the Manage Guild permission.
        HTTPException
            The operation failed.
        """
        await self._state.http.delete_auto_moderation_rule(
            self.guild_id, self.id, reason=reason
        )

    async def edit(
        self,
        *,
        name: str | utils.Undefined = MISSING,
        event_type: AutoModEventType | utils.Undefined = MISSING,
        trigger_metadata: AutoModTriggerMetadata | utils.Undefined = MISSING,
        actions: list[AutoModAction] | utils.Undefined = MISSING,
        enabled: bool | utils.Undefined = MISSING,
        exempt_roles: list[Snowflake] | utils.Undefined = MISSING,
        exempt_channels: list[Snowflake] | utils.Undefined = MISSING,
        reason: str | None = None,
    ) -> AutoModRule | None:
        """|coro|

        Edits this rule.

        Parameters
        ----------
        name: :class:`str`
            The rule's new name.
        event_type: :class:`AutoModEventType`
            The new context in which the rule is checked.
        trigger_metadata: :class:`AutoModTriggerMetadata`
            The new trigger metadata.
        actions: List[:class:`AutoModAction`]
            The new actions to perform when the rule is triggered.
        enabled: :class:`bool`
            Whether this rule is enabled.
        exempt_roles: List[:class:`abc.Snowflake`]
            The roles that will be exempt from this rule.
        exempt_channels: List[:class:`abc.Snowflake`]
            The channels that will be exempt from this rule.
        reason: Optional[:class:`str`]
            The reason for editing this rule. Shows up in the audit log.

        Returns
        -------
        Optional[:class:`.AutoModRule`]
            The newly updated rule, if applicable. This is only returned
            when fields are updated.

        Raises
        ------
        Forbidden
            You do not have the Manage Guild permission.
        HTTPException
            The operation failed.
        """
        http = self._state.http
        payload = {}

        if name is not MISSING:
            payload["name"] = name

        if event_type is not MISSING:
            payload["event_type"] = event_type.value

        if trigger_metadata is not MISSING:
            payload["trigger_metadata"] = trigger_metadata.to_dict()

        if actions is not MISSING:
            payload["actions"] = [a.to_dict() for a in actions]

        if enabled is not MISSING:
            payload["enabled"] = enabled

        # Maybe consider enforcing limits on the number of exempt roles/channels?
        if exempt_roles is not MISSING:
            payload["exempt_roles"] = [r.id for r in exempt_roles]

        if exempt_channels is not MISSING:
            payload["exempt_channels"] = [c.id for c in exempt_channels]

        if payload:
            data = await http.edit_auto_moderation_rule(
                self.guild_id, self.id, payload, reason=reason
            )
            return AutoModRule(state=self._state, data=data)
