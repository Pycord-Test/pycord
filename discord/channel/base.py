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

import copy
import datetime
import logging
from abc import ABC, abstractmethod
from collections.abc import Collection, Iterable, Sequence
from typing import TYPE_CHECKING, Any, Callable, Generic, cast, overload

from typing_extensions import Self, TypeVar, override

from ..abc import Messageable, Snowflake, SnowflakeTime, User, _Overwrites, _purge_messages_helper
from ..emoji import GuildEmoji, PartialEmoji
from ..enums import ChannelType, InviteTarget, SortOrder, try_enum
from ..errors import ClientException
from ..flags import ChannelFlags, MessageFlags
from ..iterators import ArchivedThreadIterator
from ..mixins import Hashable
from ..utils import MISSING, Undefined, find, snowflake_time
from ..utils.private import SnowflakeList, bytes_to_base64_data, copy_doc, get_as_snowflake

if TYPE_CHECKING:
    from ..embeds import Embed
    from ..errors import InvalidArgument
    from ..file import File
    from ..guild import Guild
    from ..invite import Invite
    from ..member import Member
    from ..mentions import AllowedMentions
    from ..message import EmojiInputType, Message, PartialMessage
    from ..object import Object
    from ..partial_emoji import _EmojiTag
    from ..permissions import PermissionOverwrite, Permissions
    from ..role import Role
    from ..scheduled_events import ScheduledEvent
    from ..sticker import GuildSticker, StickerItem
    from ..types.channel import CategoryChannel as CategoryChannelPayload
    from ..types.channel import Channel as ChannelPayload
    from ..types.channel import ForumChannel as ForumChannelPayload
    from ..types.channel import ForumTag as ForumTagPayload
    from ..types.channel import GuildChannel as GuildChannelPayload
    from ..types.channel import MediaChannel as MediaChannelPayload
    from ..types.channel import NewsChannel as NewsChannelPayload
    from ..types.channel import StageChannel as StageChannelPayload
    from ..types.channel import TextChannel as TextChannelPayload
    from ..types.channel import VoiceChannel as VoiceChannelPayload
    from ..types.guild import ChannelPositionUpdate as ChannelPositionUpdatePayload
    from ..ui.view import View
    from ..webhook import Webhook
    from .category import CategoryChannel
    from .channel import ForumTag
    from .text import TextChannel
    from .thread import Thread

_log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ..app.state import ConnectionState


P = TypeVar("P", bound="ChannelPayload")


class BaseChannel(ABC, Generic[P]):
    __slots__: tuple[str, ...] = ("id", "_type", "_state", "_data")  # pyright: ignore [reportIncompatibleUnannotatedOverride]

    def __init__(self, id: int, state: ConnectionState):
        self.id: int = id
        self._state: ConnectionState = state
        self._data: P = {}  # type: ignore

    async def _update(self, data: P) -> None:
        self._type: int = data["type"]
        self._data = self._data | data  # type: ignore

    @classmethod
    async def _from_data(cls, *, data: P, state: ConnectionState, **kwargs) -> Self:
        if kwargs:
            _log.warning("Unexpected keyword arguments passed to %s._from_data: %r", cls.__name__, kwargs)
        self = cls(int(data["id"]), state)
        await self._update(data)
        return self

    @property
    def type(self) -> ChannelType:
        """The channel's Discord channel type."""
        return try_enum(ChannelType, self._type)

    async def _get_channel(self) -> Self:
        return self

    @property
    def created_at(self) -> datetime.datetime:
        """The channel's creation time in UTC."""
        return snowflake_time(self.id)

    @abstractmethod
    @override
    def __repr__(self) -> str: ...

    @property
    @abstractmethod
    def jump_url(self) -> str: ...


P_guild = TypeVar(
    "P_guild",
    bound="TextChannelPayload | NewsChannelPayload | VoiceChannelPayload | CategoryChannelPayload | StageChannelPayload | ForumChannelPayload",
    default="TextChannelPayload | NewsChannelPayload | VoiceChannelPayload | CategoryChannelPayload | StageChannelPayload | ForumChannelPayload",
)


class GuildChannel(BaseChannel[P_guild], ABC, Generic[P_guild]):
    """Represents a Discord guild channel."""

    """An ABC that details the common operations on a Discord guild channel.

    The following implement this ABC:

    - :class:`~discord.TextChannel`
    - :class:`~discord.VoiceChannel`
    - :class:`~discord.CategoryChannel`
    - :class:`~discord.StageChannel`
    - :class:`~discord.ForumChannel`

    This ABC must also implement :class:`~discord.abc.Snowflake`.

    Attributes
    ----------
    name: :class:`str`
        The channel name.
    guild: :class:`~discord.Guild`
        The guild the channel belongs to.
    position: :class:`int`
        The position in the channel list. This is a number that starts at 0.
        e.g. the top channel is position 0.
    """

    __slots__: tuple[str, ...] = ("name", "guild", "category_id", "flags", "_overwrites")

    @override
    def __init__(self, id: int, *, guild: Guild, state: ConnectionState) -> None:
        self.guild: Guild = guild
        super().__init__(id, state)

    @classmethod
    @override
    async def _from_data(cls, *, data: P_guild, state: ConnectionState, guild: Guild, **kwargs) -> Self:
        if kwargs:
            _log.warning("Unexpected keyword arguments passed to %s._from_data: %r", cls.__name__, kwargs)
        self = cls(int(data["id"]), guild=guild, state=state)
        await self._update(data)
        return self

    @override
    async def _update(self, data: P_guild) -> None:
        await super()._update(data)
        self.name: str = data["name"]
        self.category_id: int | None = get_as_snowflake(data, "parent_id") or getattr(self, "category_id", None)
        if flags_value := data.get("flags", 0):
            self.flags: ChannelFlags = ChannelFlags._from_value(flags_value)
        self._fill_overwrites(data)

    @override
    def __str__(self) -> str:
        return self.name

    async def _edit(self, options: dict[str, Any], reason: str | None) -> ChannelPayload | None:
        try:
            parent = options.pop("category")
        except KeyError:
            parent_id = MISSING
        else:
            parent_id = parent and parent.id

        try:
            options["rate_limit_per_user"] = options.pop("slowmode_delay")
        except KeyError:
            pass

        try:
            options["default_thread_rate_limit_per_user"] = options.pop("default_thread_slowmode_delay")
        except KeyError:
            pass

        try:
            options["flags"] = options.pop("flags").value
        except KeyError:
            pass

        try:
            options["available_tags"] = [tag.to_dict() for tag in options.pop("available_tags")]
        except KeyError:
            pass

        try:
            rtc_region = options.pop("rtc_region")
        except KeyError:
            pass
        else:
            options["rtc_region"] = None if rtc_region is None else str(rtc_region)

        try:
            video_quality_mode = options.pop("video_quality_mode")
        except KeyError:
            pass
        else:
            options["video_quality_mode"] = int(video_quality_mode)

        lock_permissions = options.pop("sync_permissions", False)

        try:
            position = options.pop("position")
        except KeyError:
            if parent_id is not MISSING:
                if lock_permissions:
                    category = self.guild.get_channel(parent_id)
                    if category:
                        options["permission_overwrites"] = [c._asdict() for c in category._overwrites]
                options["parent_id"] = parent_id
            elif lock_permissions and self.category_id is not None:
                # if we're syncing permissions on a pre-existing channel category without changing it
                # we need to update the permissions to point to the pre-existing category
                category = self.guild.get_channel(self.category_id)
                if category:
                    options["permission_overwrites"] = [c._asdict() for c in category._overwrites]
        else:
            await self._move(
                position,
                parent_id=parent_id,
                lock_permissions=lock_permissions,
                reason=reason,
            )

        overwrites = options.get("overwrites")
        if overwrites is not None:
            perms = []
            for target, perm in overwrites.items():
                if not isinstance(perm, PermissionOverwrite):
                    raise InvalidArgument(f"Expected PermissionOverwrite received {perm.__class__.__name__}")

                allow, deny = perm.pair()
                payload = {
                    "allow": allow.value,
                    "deny": deny.value,
                    "id": target.id,
                    "type": (_Overwrites.ROLE if isinstance(target, Role) else _Overwrites.MEMBER),
                }

                perms.append(payload)
            options["permission_overwrites"] = perms

        try:
            ch_type = options["type"]
        except KeyError:
            pass
        else:
            if not isinstance(ch_type, ChannelType):
                raise InvalidArgument("type field must be of type ChannelType")
            options["type"] = ch_type.value

        try:
            default_reaction_emoji = options["default_reaction_emoji"]
        except KeyError:
            pass
        else:
            if isinstance(default_reaction_emoji, _EmojiTag):  # GuildEmoji, PartialEmoji
                default_reaction_emoji = default_reaction_emoji._to_partial()
            elif isinstance(default_reaction_emoji, int):
                default_reaction_emoji = PartialEmoji(name=None, id=default_reaction_emoji)
            elif isinstance(default_reaction_emoji, str):
                default_reaction_emoji = PartialEmoji.from_str(default_reaction_emoji)
            elif default_reaction_emoji is None:
                pass
            else:
                raise InvalidArgument("default_reaction_emoji must be of type: GuildEmoji | int | str | None")

            options["default_reaction_emoji"] = (
                default_reaction_emoji._to_forum_reaction_payload() if default_reaction_emoji else None
            )

        if options:
            return await self._state.http.edit_channel(self.id, reason=reason, **options)

    def _fill_overwrites(self, data: GuildChannelPayload) -> None:
        self._overwrites: list[_Overwrites] = []
        everyone_index = 0
        everyone_id = self.guild.id

        for index, overridden in enumerate(data.get("permission_overwrites", [])):
            overwrite = _Overwrites(overridden)
            self._overwrites.append(overwrite)

            if overwrite.type == _Overwrites.MEMBER:
                continue

            if overwrite.id == everyone_id:
                # the @everyone role is not guaranteed to be the first one
                # in the list of permission overwrites, however the permission
                # resolution code kind of requires that it is the first one in
                # the list since it is special. So we need the index so we can
                # swap it to be the first one.
                everyone_index = index

        # do the swap
        tmp = self._overwrites
        if tmp:
            tmp[everyone_index], tmp[0] = tmp[0], tmp[everyone_index]

    @property
    def changed_roles(self) -> list[Role]:
        """Returns a list of roles that have been overridden from
        their default values in the :attr:`~discord.Guild.roles` attribute.
        """
        ret = []
        g = self.guild
        for overwrite in filter(lambda o: o.is_role(), self._overwrites):
            role = g.get_role(overwrite.id)
            if role is None:
                continue

            role = copy.copy(role)
            role.permissions.handle_overwrite(overwrite.allow, overwrite.deny)
            ret.append(role)
        return ret

    @property
    def mention(self) -> str:
        """The string that allows you to mention the channel."""
        return f"<#{self.id}>"

    @property
    @override
    def jump_url(self) -> str:
        """Returns a URL that allows the client to jump to the channel.

        .. versionadded:: 2.0
        """
        return f"https://discord.com/channels/{self.guild.id}/{self.id}"

    def overwrites_for(self, obj: Role | User) -> PermissionOverwrite:
        """Returns the channel-specific overwrites for a member or a role.

        Parameters
        ----------
        obj: Union[:class:`~discord.Role`, :class:`~discord.abc.User`]
            The role or user denoting
            whose overwrite to get.

        Returns
        -------
        :class:`~discord.PermissionOverwrite`
            The permission overwrites for this object.
        """

        if isinstance(obj, User):
            predicate: Callable[[Any], bool] = lambda p: p.is_member()
        elif isinstance(obj, Role):
            predicate = lambda p: p.is_role()
        else:
            predicate = lambda p: True

        for overwrite in filter(predicate, self._overwrites):
            if overwrite.id == obj.id:
                allow = Permissions(overwrite.allow)
                deny = Permissions(overwrite.deny)
                return PermissionOverwrite.from_pair(allow, deny)

        return PermissionOverwrite()

    async def get_overwrites(self) -> dict[Role | Member | Object, PermissionOverwrite]:
        """Returns all of the channel's overwrites.

        This is returned as a dictionary where the key contains the target which
        can be either a :class:`~discord.Role` or a :class:`~discord.Member` and the value is the
        overwrite as a :class:`~discord.PermissionOverwrite`.

        Returns
        -------
        Dict[Union[:class:`~discord.Role`, :class:`~discord.Member`, :class:`~discord.Object`], :class:`~discord.PermissionOverwrite`]
            The channel's permission overwrites.
        """
        ret: dict[Role | Member | Object, PermissionOverwrite] = {}
        for ow in self._overwrites:
            allow = Permissions(ow.allow)
            deny = Permissions(ow.deny)
            overwrite = PermissionOverwrite.from_pair(allow, deny)
            target = None

            if ow.is_role():
                target = self.guild.get_role(ow.id)
            elif ow.is_member():
                target = await self.guild.get_member(ow.id)

            if target is not None:
                ret[target] = overwrite
            else:
                ret[Object(id=ow.id)] = overwrite
        return ret

    @property
    def category(self) -> CategoryChannel | None:
        """The category this channel belongs to.

        If there is no category then this is ``None``.
        """
        return cast("CategoryChannel | None", self.guild.get_channel(self.category_id)) if self.category_id else None

    @property
    def members(self) -> Collection[Member]:
        """Returns all members that can view this channel.

        This is calculated based on the channel's permission overwrites and
        the members' roles.

        Returns
        -------
        Collection[:class:`Member`]
            All members who have permission to view this channel.
        """
        return [m for m in self.guild.members if self.permissions_for(m).read_messages]

    async def permissions_are_synced(self) -> bool:
        """Whether the permissions for this channel are synced with the
        category it belongs to.

        If there is no category then this is ``False``.

        .. versionadded:: 3.0
        """
        if self.category_id is None:
            return False

        category: CategoryChannel | None = cast("CategoryChannel | None", self.guild.get_channel(self.category_id))
        return bool(category and await category.get_overwrites() == await self.get_overwrites())

    def permissions_for(self, obj: Member | Role, /) -> Permissions:
        """Handles permission resolution for the :class:`~discord.Member`
        or :class:`~discord.Role`.

        This function takes into consideration the following cases:

        - Guild owner
        - Guild roles
        - Channel overrides
        - Member overrides

        If a :class:`~discord.Role` is passed, then it checks the permissions
        someone with that role would have, which is essentially:

        - The default role permissions
        - The permissions of the role used as a parameter
        - The default role permission overwrites
        - The permission overwrites of the role used as a parameter

        .. versionchanged:: 2.0
            The object passed in can now be a role object.

        Parameters
        ----------
        obj: Union[:class:`~discord.Member`, :class:`~discord.Role`]
            The object to resolve permissions for. This could be either
            a member or a role. If it's a role then member overwrites
            are not computed.

        Returns
        -------
        :class:`~discord.Permissions`
            The resolved permissions for the member or role.
        """

        # The current cases can be explained as:
        # Guild owner get all permissions -- no questions asked. Otherwise...
        # The @everyone role gets the first application.
        # After that, the applied roles that the user has in the channel
        # (or otherwise) are then OR'd together.
        # After the role permissions are resolved, the member permissions
        # have to take into effect.
        # After all that is done, you have to do the following:

        # If manage permissions is True, then all permissions are set to True.

        # The operation first takes into consideration the denied
        # and then the allowed.

        if self.guild.owner_id == obj.id:
            return Permissions.all()

        default = self.guild.default_role
        base = Permissions(default.permissions.value if default else 0)

        # Handle the role case first
        if isinstance(obj, Role):
            base.value |= obj._permissions

            if base.administrator:
                return Permissions.all()

            # Apply @everyone allow/deny first since it's special
            try:
                maybe_everyone = self._overwrites[0]
                if maybe_everyone.id == self.guild.id:
                    base.handle_overwrite(allow=maybe_everyone.allow, deny=maybe_everyone.deny)
            except IndexError:
                pass

            if obj.is_default():
                return base

            overwrite = find(lambda o: o.type == _Overwrites.ROLE and o.id == obj.id, self._overwrites)
            if overwrite is not None:
                base.handle_overwrite(overwrite.allow, overwrite.deny)

            return base

        roles = obj._roles
        get_role = self.guild.get_role

        # Apply guild roles that the member has.
        for role_id in roles:
            role = get_role(role_id)
            if role is not None:
                base.value |= role._permissions

        # Guild-wide Administrator -> True for everything
        # Bypass all channel-specific overrides
        if base.administrator:
            return Permissions.all()

        # Apply @everyone allow/deny first since it's special
        try:
            maybe_everyone = self._overwrites[0]
            if maybe_everyone.id == self.guild.id:
                base.handle_overwrite(allow=maybe_everyone.allow, deny=maybe_everyone.deny)
                remaining_overwrites = self._overwrites[1:]
            else:
                remaining_overwrites = self._overwrites
        except IndexError:
            remaining_overwrites = self._overwrites

        denies = 0
        allows = 0

        # Apply channel specific role permission overwrites
        for overwrite in remaining_overwrites:
            if overwrite.is_role() and roles.has(overwrite.id):
                denies |= overwrite.deny
                allows |= overwrite.allow

        base.handle_overwrite(allow=allows, deny=denies)

        # Apply member specific permission overwrites
        for overwrite in remaining_overwrites:
            if overwrite.is_member() and overwrite.id == obj.id:
                base.handle_overwrite(allow=overwrite.allow, deny=overwrite.deny)
                break

        # if you can't send a message in a channel then you can't have certain
        # permissions as well
        if not base.send_messages:
            base.send_tts_messages = False
            base.mention_everyone = False
            base.embed_links = False
            base.attach_files = False

        # if you can't read a channel then you have no permissions there
        if not base.read_messages:
            denied = Permissions.all_channel()
            base.value &= ~denied.value

        return base

    async def delete(self, *, reason: str | None = None) -> None:
        """|coro|

        Deletes the channel.

        You must have :attr:`~discord.Permissions.manage_channels` permission to use this.

        Parameters
        ----------
        reason: Optional[:class:`str`]
            The reason for deleting this channel.
            Shows up on the audit log.

        Raises
        ------
        ~discord.Forbidden
            You do not have proper permissions to delete the channel.
        ~discord.NotFound
            The channel was not found or was already deleted.
        ~discord.HTTPException
            Deleting the channel failed.
        """
        await self._state.http.delete_channel(self.id, reason=reason)

    @overload
    async def set_permissions(
        self,
        target: Member | Role,
        *,
        overwrite: PermissionOverwrite | None = ...,
        reason: str | None = ...,
    ) -> None: ...

    @overload
    async def set_permissions(
        self,
        target: Member | Role,
        *,
        overwrite: Undefined = MISSING,
        reason: str | None = ...,
        **permissions: bool,
    ) -> None: ...

    async def set_permissions(
        self,
        target: Member | Role,
        *,
        overwrite: PermissionOverwrite | None | Undefined = MISSING,
        reason: str | None = None,
        **permissions: bool,
    ) -> None:
        r"""|coro|

        Sets the channel specific permission overwrites for a target in the
        channel.

        The ``target`` parameter should either be a :class:`~discord.Member` or a
        :class:`~discord.Role` that belongs to guild.

        The ``overwrite`` parameter, if given, must either be ``None`` or
        :class:`~discord.PermissionOverwrite`. For convenience, you can pass in
        keyword arguments denoting :class:`~discord.Permissions` attributes. If this is
        done, then you cannot mix the keyword arguments with the ``overwrite``
        parameter.

        If the ``overwrite`` parameter is ``None``, then the permission
        overwrites are deleted.

        You must have the :attr:`~discord.Permissions.manage_roles` permission to use this.

        .. note::

            This method *replaces* the old overwrites with the ones given.

        Examples
        ----------

        Setting allow and deny: ::

            await message.channel.set_permissions(message.author, read_messages=True, send_messages=False)

        Deleting overwrites ::

            await channel.set_permissions(member, overwrite=None)

        Using :class:`~discord.PermissionOverwrite` ::

            overwrite = discord.PermissionOverwrite()
            overwrite.send_messages = False
            overwrite.read_messages = True
            await channel.set_permissions(member, overwrite=overwrite)

        Parameters
        -----------
        target: Union[:class:`~discord.Member`, :class:`~discord.Role`]
            The member or role to overwrite permissions for.
        overwrite: Optional[:class:`~discord.PermissionOverwrite`]
            The permissions to allow and deny to the target, or ``None`` to
            delete the overwrite.
        \*\*permissions
            A keyword argument list of permissions to set for ease of use.
            Cannot be mixed with ``overwrite``.
        reason: Optional[:class:`str`]
            The reason for doing this action. Shows up on the audit log.

        Raises
        -------
        ~discord.Forbidden
            You do not have permissions to edit channel specific permissions.
        ~discord.HTTPException
            Editing channel specific permissions failed.
        ~discord.NotFound
            The role or member being edited is not part of the guild.
        ~discord.InvalidArgument
            The overwrite parameter invalid or the target type was not
            :class:`~discord.Role` or :class:`~discord.Member`.
        """

        http = self._state.http

        if isinstance(target, User):
            perm_type = _Overwrites.MEMBER
        elif isinstance(target, Role):
            perm_type = _Overwrites.ROLE
        else:
            raise InvalidArgument("target parameter must be either Member or Role")

        if overwrite is MISSING:
            if len(permissions) == 0:
                raise InvalidArgument("No overwrite provided.")
            try:
                overwrite = PermissionOverwrite(**permissions)
            except (ValueError, TypeError) as e:
                raise InvalidArgument("Invalid permissions given to keyword arguments.") from e
        elif len(permissions) > 0:
            raise InvalidArgument("Cannot mix overwrite and keyword arguments.")

        # TODO: wait for event

        if overwrite is None:
            await http.delete_channel_permissions(self.id, target.id, reason=reason)
        elif isinstance(overwrite, PermissionOverwrite):
            (allow, deny) = overwrite.pair()
            await http.edit_channel_permissions(self.id, target.id, allow.value, deny.value, perm_type, reason=reason)
        else:
            raise InvalidArgument("Invalid overwrite type provided.")

    async def _clone_impl(
        self,
        base_attrs: dict[str, Any],
        *,
        name: str | None = None,
        reason: str | None = None,
    ) -> Self:
        base_attrs["permission_overwrites"] = [x._asdict() for x in self._overwrites]
        base_attrs["parent_id"] = self.category_id
        base_attrs["name"] = name or self.name
        guild_id = self.guild.id
        cls = self.__class__
        data: P_guild = cast(
            "P_guild", await self._state.http.create_channel(guild_id, self.type.value, reason=reason, **base_attrs)
        )
        clone = cls(id=int(data["id"]), guild=self.guild, state=self._state)
        await clone._update(data)

        self.guild._channels[clone.id] = clone
        return clone

    async def clone(self, *, name: str | None = None, reason: str | None = None) -> Self:
        """|coro|

        Clones this channel. This creates a channel with the same properties
        as this channel.

        You must have the :attr:`~discord.Permissions.manage_channels` permission to
        do this.

        .. versionadded:: 1.1

        Parameters
        ----------
        name: Optional[:class:`str`]
            The name of the new channel. If not provided, defaults to this
            channel name.
        reason: Optional[:class:`str`]
            The reason for cloning this channel. Shows up on the audit log.

        Returns
        -------
        :class:`.abc.GuildChannel`
            The channel that was created.

        Raises
        ------
        ~discord.Forbidden
            You do not have the proper permissions to create this channel.
        ~discord.HTTPException
            Creating the channel failed.
        """
        raise NotImplementedError

    async def create_invite(
        self,
        *,
        reason: str | None = None,
        max_age: int = 0,
        max_uses: int = 0,
        temporary: bool = False,
        unique: bool = True,
        target_event: ScheduledEvent | None = None,
        target_type: InviteTarget | None = None,
        target_user: User | None = None,
        target_application_id: int | None = None,
    ) -> Invite:
        """|coro|

        Creates an instant invite from a text or voice channel.

        You must have the :attr:`~discord.Permissions.create_instant_invite` permission to
        do this.

        Parameters
        ----------
        max_age: :class:`int`
            How long the invite should last in seconds. If it's 0 then the invite
            doesn't expire. Defaults to ``0``.
        max_uses: :class:`int`
            How many uses the invite could be used for. If it's 0 then there
            are unlimited uses. Defaults to ``0``.
        temporary: :class:`bool`
            Denotes that the invite grants temporary membership
            (i.e. they get kicked after they disconnect). Defaults to ``False``.
        unique: :class:`bool`
            Indicates if a unique invite URL should be created. Defaults to True.
            If this is set to ``False`` then it will return a previously created
            invite.
        reason: Optional[:class:`str`]
            The reason for creating this invite. Shows up on the audit log.
        target_type: Optional[:class:`.InviteTarget`]
            The type of target for the voice channel invite, if any.

            .. versionadded:: 2.0

        target_user: Optional[:class:`User`]
            The user whose stream to display for this invite, required if `target_type` is `TargetType.stream`.
            The user must be streaming in the channel.

            .. versionadded:: 2.0

        target_application_id: Optional[:class:`int`]
            The id of the embedded application for the invite, required if `target_type` is
            `TargetType.embedded_application`.

            .. versionadded:: 2.0

        target_event: Optional[:class:`.ScheduledEvent`]
            The scheduled event object to link to the event.
            Shortcut to :meth:`.Invite.set_scheduled_event`

            See :meth:`.Invite.set_scheduled_event` for more
            info on event invite linking.

            .. versionadded:: 2.0

        Returns
        -------
        :class:`~discord.Invite`
            The invite that was created.

        Raises
        ------
        ~discord.HTTPException
            Invite creation failed.

        ~discord.NotFound
            The channel that was passed is a category or an invalid channel.
        """
        if target_type is InviteTarget.unknown:
            raise TypeError("target_type cannot be unknown")

        data = await self._state.http.create_invite(
            self.id,
            reason=reason,
            max_age=max_age,
            max_uses=max_uses,
            temporary=temporary,
            unique=unique,
            target_type=target_type.value if target_type else None,
            target_user_id=target_user.id if target_user else None,
            target_application_id=target_application_id,
        )
        invite = await Invite.from_incomplete(data=data, state=self._state)
        if target_event:
            invite.set_scheduled_event(target_event)
        return invite

    async def invites(self) -> list[Invite]:
        """|coro|

        Returns a list of all active instant invites from this channel.

        You must have :attr:`~discord.Permissions.manage_channels` to get this information.

        Returns
        -------
        List[:class:`~discord.Invite`]
            The list of invites that are currently active.

        Raises
        ------
        ~discord.Forbidden
            You do not have proper permissions to get the information.
        ~discord.HTTPException
            An error occurred while fetching the information.
        """

        data = await self._state.http.invites_from_channel(self.id)
        guild = self.guild
        return [Invite(state=self._state, data=invite, channel=self, guild=guild) for invite in data]


P_guild_top_level = TypeVar(
    "P_guild_top_level",
    bound="TextChannelPayload | NewsChannelPayload | VoiceChannelPayload | CategoryChannelPayload | StageChannelPayload | ForumChannelPayload",
    default="TextChannelPayload | NewsChannelPayload | VoiceChannelPayload | CategoryChannelPayload | StageChannelPayload | ForumChannelPayload",
)


class GuildTopLevelChannel(GuildChannel[P_guild_top_level], ABC, Generic[P_guild_top_level]):
    """An ABC for guild channels that can be positioned in the channel list.

    This includes categories and all channels that appear in the channel sidebar
    (text, voice, news, stage, forum, media channels). Threads do not inherit from
    this class as they are not positioned in the main channel list.

    .. versionadded:: 3.0

    Attributes
    ----------
    position: int
        The position in the channel list. This is a number that starts at 0.
        e.g. the top channel is position 0.
    """

    __slots__: tuple[str, ...] = ("position",)

    @override
    async def _update(self, data: P_guild_top_level) -> None:
        await super()._update(data)
        self.position: int = data.get("position", 0)

    @property
    @abstractmethod
    def _sorting_bucket(self) -> int:
        """Returns the bucket for sorting channels by type."""
        raise NotImplementedError

    async def _move(
        self,
        position: int,
        parent_id: Any | None = None,
        lock_permissions: bool = False,
        *,
        reason: str | None,
    ) -> None:
        """Internal method to move a channel to a specific position.

        Parameters
        ----------
        position: int
            The new position for the channel.
        parent_id: Any | None
            The parent category ID, if moving to a category.
        lock_permissions: bool
            Whether to sync permissions with the category.
        reason: str | None
            The reason for moving the channel.

        Raises
        ------
        InvalidArgument
            The position is less than 0.
        """
        if position < 0:
            raise InvalidArgument("Channel position cannot be less than 0.")

        bucket = self._sorting_bucket
        channels: list[Self] = [c for c in self.guild.channels if c._sorting_bucket == bucket]

        channels.sort(key=lambda c: c.position)

        try:
            # remove ourselves from the channel list
            channels.remove(self)
        except ValueError:
            # not there somehow lol
            return
        else:
            index = next(
                (i for i, c in enumerate(channels) if c.position >= position),
                len(channels),
            )
            # add ourselves at our designated position
            channels.insert(index, self)

        payload: list[ChannelPositionUpdatePayload] = []
        for index, c in enumerate(channels):
            d: ChannelPositionUpdatePayload = {"id": c.id, "position": index}
            if parent_id is not MISSING and c.id == self.id:
                d.update(parent_id=parent_id, lock_permissions=lock_permissions)
            payload.append(d)

        await self._state.http.bulk_channel_update(self.guild.id, payload, reason=reason)

    @overload
    async def move(
        self,
        *,
        beginning: bool,
        offset: int | Undefined = MISSING,
        category: Snowflake | None | Undefined = MISSING,
        sync_permissions: bool | Undefined = MISSING,
        reason: str | None | Undefined = MISSING,
    ) -> None: ...

    @overload
    async def move(
        self,
        *,
        end: bool,
        offset: int | Undefined = MISSING,
        category: Snowflake | None | Undefined = MISSING,
        sync_permissions: bool | Undefined = MISSING,
        reason: str | Undefined = MISSING,
    ) -> None: ...

    @overload
    async def move(
        self,
        *,
        before: Snowflake,
        offset: int | Undefined = MISSING,
        category: Snowflake | None | Undefined = MISSING,
        sync_permissions: bool | Undefined = MISSING,
        reason: str | Undefined = MISSING,
    ) -> None: ...

    @overload
    async def move(
        self,
        *,
        after: Snowflake,
        offset: int | Undefined = MISSING,
        category: Snowflake | None | Undefined = MISSING,
        sync_permissions: bool | Undefined = MISSING,
        reason: str | Undefined = MISSING,
    ) -> None: ...

    async def move(self, **kwargs: Any) -> None:
        """|coro|

        A rich interface to help move a channel relative to other channels.

        If exact position movement is required, ``edit`` should be used instead.

        You must have :attr:`~discord.Permissions.manage_channels` permission to
        do this.

        .. note::

            Voice channels will always be sorted below text channels.
            This is a Discord limitation.

        .. versionadded:: 1.7

        Parameters
        ----------
        beginning: bool
            Whether to move the channel to the beginning of the
            channel list (or category if given).
            This is mutually exclusive with ``end``, ``before``, and ``after``.
        end: bool
            Whether to move the channel to the end of the
            channel list (or category if given).
            This is mutually exclusive with ``beginning``, ``before``, and ``after``.
        before: ~discord.abc.Snowflake
            The channel that should be before our current channel.
            This is mutually exclusive with ``beginning``, ``end``, and ``after``.
        after: ~discord.abc.Snowflake
            The channel that should be after our current channel.
            This is mutually exclusive with ``beginning``, ``end``, and ``before``.
        offset: int
            The number of channels to offset the move by. For example,
            an offset of ``2`` with ``beginning=True`` would move
            it 2 after the beginning. A positive number moves it below
            while a negative number moves it above. Note that this
            number is relative and computed after the ``beginning``,
            ``end``, ``before``, and ``after`` parameters.
        category: ~discord.abc.Snowflake | None
            The category to move this channel under.
            If ``None`` is given then it moves it out of the category.
            This parameter is ignored if moving a category channel.
        sync_permissions: bool
            Whether to sync the permissions with the category (if given).
        reason: str | None
            The reason for the move.

        Raises
        ------
        InvalidArgument
            An invalid position was given or a bad mix of arguments was passed.
        Forbidden
            You do not have permissions to move the channel.
        HTTPException
            Moving the channel failed.
        """

        if not kwargs:
            return

        beginning, end = kwargs.get("beginning"), kwargs.get("end")
        before, after = kwargs.get("before"), kwargs.get("after")
        offset = kwargs.get("offset", 0)
        if sum(bool(a) for a in (beginning, end, before, after)) > 1:
            raise InvalidArgument("Only one of [before, after, end, beginning] can be used.")

        bucket = self._sorting_bucket
        parent_id = kwargs.get("category", MISSING)
        channels: list[GuildChannel]
        if parent_id not in (MISSING, None):
            parent_id = parent_id.id
            channels = [
                ch for ch in self.guild.channels if ch._sorting_bucket == bucket and ch.category_id == parent_id
            ]
        else:
            channels = [
                ch for ch in self.guild.channels if ch._sorting_bucket == bucket and ch.category_id == self.category_id
            ]

        channels.sort(key=lambda c: (c.position, c.id))

        try:
            # Try to remove ourselves from the channel list
            channels.remove(self)
        except ValueError:
            # If we're not there then it's probably due to not being in the category
            pass

        index = None
        if beginning:
            index = 0
        elif end:
            index = len(channels)
        elif before:
            index = next((i for i, c in enumerate(channels) if c.id == before.id), None)
        elif after:
            index = next((i + 1 for i, c in enumerate(channels) if c.id == after.id), None)

        if index is None:
            raise InvalidArgument("Could not resolve appropriate move position")
        # TODO: This could use self._move to avoid code duplication
        channels.insert(max((index + offset), 0), self)
        payload: list[ChannelPositionUpdatePayload] = []
        lock_permissions = kwargs.get("sync_permissions", False)
        reason = kwargs.get("reason")
        for index, channel in enumerate(channels):
            d: ChannelPositionUpdatePayload = {"id": channel.id, "position": index}  # pyright: ignore[reportAssignmentType]
            if parent_id is not MISSING and channel.id == self.id:
                d.update(parent_id=parent_id, lock_permissions=lock_permissions)
            payload.append(d)

        await self._state.http.bulk_channel_update(self.guild.id, payload, reason=reason)


P_guild_threadable = TypeVar(
    "P_guild_threadable",
    bound="TextChannelPayload | NewsChannelPayload | ForumChannelPayload | MediaChannelPayload",
    default="TextChannelPayload | NewsChannelPayload | ForumChannelPayload | MediaChannelPayload",
)


class GuildThreadableChannel:
    """An ABC for guild channels that support thread creation.

    This includes text, news, forum, and media channels.
    Voice, stage, and category channels do not support threads.

    This is a mixin class that adds threading capabilities to guild channels.

    .. versionadded:: 3.0

    Attributes
    ----------
    default_auto_archive_duration: int
        The default auto archive duration in minutes for threads created in this channel.
    default_thread_slowmode_delay: int | None
        The initial slowmode delay to set on newly created threads in this channel.
    """

    __slots__ = ()  # Mixin class - slots defined in concrete classes

    # Type hints for attributes that this mixin expects from the inheriting class
    if TYPE_CHECKING:
        id: int
        guild: Guild
        default_auto_archive_duration: int
        default_thread_slowmode_delay: int | None

    async def _update(self, data) -> None:
        """Update threadable channel attributes."""
        await super()._update(data)  # Call next in MRO
        self.default_auto_archive_duration: int = data.get("default_auto_archive_duration", 1440)
        self.default_thread_slowmode_delay: int | None = data.get("default_thread_rate_limit_per_user")

    @property
    def threads(self) -> list[Thread]:
        """Returns all the threads that you can see in this channel.

        .. versionadded:: 2.0

        Returns
        -------
        list[:class:`Thread`]
            All active threads in this channel.
        """
        return [thread for thread in self.guild._threads.values() if thread.parent_id == self.id]

    def get_thread(self, thread_id: int, /) -> Thread | None:
        """Returns a thread with the given ID.

        .. versionadded:: 2.0

        Parameters
        ----------
        thread_id: int
            The ID to search for.

        Returns
        -------
        Thread | None
            The returned thread or ``None`` if not found.
        """
        return self.guild.get_thread(thread_id)

    def archived_threads(
        self,
        *,
        private: bool = False,
        joined: bool = False,
        limit: int | None = 50,
        before: Snowflake | datetime.datetime | None = None,
    ) -> ArchivedThreadIterator:
        """Returns an iterator that iterates over all archived threads in the channel.

        You must have :attr:`~Permissions.read_message_history` to use this. If iterating over private threads
        then :attr:`~Permissions.manage_threads` is also required.

        .. versionadded:: 2.0

        Parameters
        ----------
        limit: int | None
            The number of threads to retrieve.
            If ``None``, retrieves every archived thread in the channel. Note, however,
            that this would make it a slow operation.
        before: Snowflake | datetime.datetime | None
            Retrieve archived channels before the given date or ID.
        private: bool
            Whether to retrieve private archived threads.
        joined: bool
            Whether to retrieve private archived threads that you've joined.
            You cannot set ``joined`` to ``True`` and ``private`` to ``False``.

        Yields
        ------
        :class:`Thread`
            The archived threads.

        Raises
        ------
        Forbidden
            You do not have permissions to get archived threads.
        HTTPException
            The request to get the archived threads failed.
        """
        return ArchivedThreadIterator(
            self.id,
            self.guild,
            limit=limit,
            joined=joined,
            private=private,
            before=before,
        )


P_guild_postable = TypeVar(
    "P_guild_postable",
    bound="ForumChannelPayload | MediaChannelPayload",
    default="ForumChannelPayload | MediaChannelPayload",
)


class ForumTag(Hashable):
    """Represents a forum tag that can be added to a thread inside a :class:`ForumChannel`
    .
        .. versionadded:: 2.3

        .. container:: operations

            .. describe:: x == y

                Checks if two forum tags are equal.

            .. describe:: x != y

                Checks if two forum tags are not equal.

            .. describe:: hash(x)

                Returns the forum tag's hash.

            .. describe:: str(x)

                Returns the forum tag's name.

        Attributes
        ----------
        id: :class:`int`
            The tag ID.
            Note that if the object was created manually then this will be ``0``.
        name: :class:`str`
            The name of the tag. Can only be up to 20 characters.
        moderated: :class:`bool`
            Whether this tag can only be added or removed by a moderator with
            the :attr:`~Permissions.manage_threads` permission.
        emoji: :class:`PartialEmoji`
            The emoji that is used to represent this tag.
            Note that if the emoji is a custom emoji, it will *not* have name information.
    """

    __slots__ = ("name", "id", "moderated", "emoji")

    def __init__(self, *, name: str, emoji: EmojiInputType, moderated: bool = False) -> None:
        self.name: str = name
        self.id: int = 0
        self.moderated: bool = moderated
        self.emoji: PartialEmoji
        if isinstance(emoji, _EmojiTag):
            self.emoji = emoji._to_partial()
        elif isinstance(emoji, str):
            self.emoji = PartialEmoji.from_str(emoji)
        else:
            raise TypeError(f"emoji must be a GuildEmoji, PartialEmoji, or str and not {emoji.__class__!r}")

    def __repr__(self) -> str:
        return f"<ForumTag id={self.id} name={self.name!r} emoji={self.emoji!r} moderated={self.moderated}>"

    def __str__(self) -> str:
        return self.name

    @classmethod
    def from_data(cls, *, state: ConnectionState, data: ForumTagPayload) -> ForumTag:
        self = cls.__new__(cls)
        self.name = data["name"]
        self.id = int(data["id"])
        self.moderated = data.get("moderated", False)

        emoji_name = data["emoji_name"] or ""
        emoji_id = get_as_snowflake(data, "emoji_id") or None
        self.emoji = PartialEmoji.with_state(state=state, name=emoji_name, id=emoji_id)
        return self

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": self.name,
            "moderated": self.moderated,
        } | self.emoji._to_forum_reaction_payload()

        if self.id:
            payload["id"] = self.id

        return payload


class GuildPostableChannel(
    GuildTopLevelChannel[P_guild_postable], GuildThreadableChannel, ABC, Generic[P_guild_postable]
):
    """An ABC for guild channels that support posts (threads with tags).

    This is a common base for forum and media channels. These channels don't support
    direct messaging, but users create posts (which are threads) with associated tags.

    .. versionadded:: 3.0

    Attributes
    ----------
    topic: str | None
        The channel's topic/guidelines. ``None`` if it doesn't exist.
    nsfw: bool
        Whether the channel is marked as NSFW.
    slowmode_delay: int
        The number of seconds a member must wait between creating posts
        in this channel. A value of ``0`` denotes that it is disabled.
    last_message_id: int | None
        The ID of the last message sent in this channel. It may not always point to an existing or valid message.
    available_tags: list[ForumTag]
        The set of tags that can be used in this channel.
    default_sort_order: SortOrder | None
        The default sort order type used to order posts in this channel.
    default_reaction_emoji: str | GuildEmoji | None
        The default reaction emoji for posts in this channel.
    """

    __slots__: tuple[str, ...] = (
        "topic",
        "nsfw",
        "slowmode_delay",
        "last_message_id",
        "default_auto_archive_duration",
        "default_thread_slowmode_delay",
        "available_tags",
        "default_sort_order",
        "default_reaction_emoji",
    )

    @override
    async def _update(self, data: P_guild_postable) -> None:
        await super()._update(data)
        if not data.pop("_invoke_flag", False):
            self.topic: str | None = data.get("topic")
            self.nsfw: bool = data.get("nsfw", False)
            self.slowmode_delay: int = data.get("rate_limit_per_user", 0)
            self.last_message_id: int | None = get_as_snowflake(data, "last_message_id")

            self.available_tags: list[ForumTag] = [
                ForumTag.from_data(state=self._state, data=tag) for tag in (data.get("available_tags") or [])
            ]
            self.default_sort_order: SortOrder | None = data.get("default_sort_order", None)
            if self.default_sort_order is not None:
                self.default_sort_order = try_enum(SortOrder, self.default_sort_order)

            self.default_reaction_emoji = None
            reaction_emoji_ctx: dict = data.get("default_reaction_emoji")
            if reaction_emoji_ctx is not None:
                emoji_name = reaction_emoji_ctx.get("emoji_name")
                if emoji_name is not None:
                    self.default_reaction_emoji = reaction_emoji_ctx["emoji_name"]
                else:
                    emoji_id = get_as_snowflake(reaction_emoji_ctx, "emoji_id")
                    if emoji_id:
                        self.default_reaction_emoji = await self._state.get_emoji(emoji_id)

    @property
    def guidelines(self) -> str | None:
        """The channel's guidelines. An alias of :attr:`topic`."""
        return self.topic

    @property
    def requires_tag(self) -> bool:
        """Whether a tag is required to be specified when creating a post in this channel.

        .. versionadded:: 2.3
        """
        return self.flags.require_tag

    def get_tag(self, id: int, /) -> ForumTag | None:
        """Returns the :class:`ForumTag` from this channel with the given ID, if any.

        .. versionadded:: 2.3
        """
        return find(lambda t: t.id == id, self.available_tags)

    async def create_thread(
        self,
        name: str,
        content: str | None = None,
        *,
        embed: Embed | None = None,
        embeds: list[Embed] | None = None,
        file: File | None = None,
        files: list[File] | None = None,
        stickers: Sequence[GuildSticker | StickerItem] | None = None,
        delete_message_after: float | None = None,
        nonce: int | str | None = None,
        allowed_mentions: AllowedMentions | None = None,
        view: View | None = None,
        applied_tags: list[ForumTag] | None = None,
        suppress: bool = False,
        silent: bool = False,
        auto_archive_duration: int | Undefined = MISSING,
        slowmode_delay: int | Undefined = MISSING,
        reason: str | None = None,
    ) -> Thread:
        """|coro|

        Creates a post (thread with initial message) in this forum or media channel.

        To create a post, you must have :attr:`~discord.Permissions.create_public_threads` or
        :attr:`~discord.Permissions.send_messages` permission.

        .. versionadded:: 2.0

        Parameters
        ----------
        name: :class:`str`
            The name of the post/thread.
        content: :class:`str`
            The content of the initial message.
        embed: :class:`~discord.Embed`
            The rich embed for the content.
        embeds: list[:class:`~discord.Embed`]
            A list of embeds to upload. Must be a maximum of 10.
        file: :class:`~discord.File`
            The file to upload.
        files: list[:class:`~discord.File`]
            A list of files to upload. Must be a maximum of 10.
        stickers: Sequence[:class:`~discord.GuildSticker` | :class:`~discord.StickerItem`]
            A list of stickers to upload. Must be a maximum of 3.
        delete_message_after: :class:`float`
            The time in seconds to wait before deleting the initial message.
        nonce: :class:`str` | :class:`int`
            The nonce to use for sending this message.
        allowed_mentions: :class:`~discord.AllowedMentions`
            Controls the mentions being processed in this message.
        view: :class:`discord.ui.View`
            A Discord UI View to add to the message.
        applied_tags: list[:class:`ForumTag`]
            A list of tags to apply to the new post.
        suppress: :class:`bool`
            Whether to suppress embeds in the initial message.
        silent: :class:`bool`
            Whether to send the message without triggering a notification.
        auto_archive_duration: :class:`int`
            The duration in minutes before the post is automatically archived for inactivity.
            If not provided, the channel's default auto archive duration is used.
        slowmode_delay: :class:`int`
            The number of seconds a member must wait between sending messages in the new post.
            If not provided, the channel's default slowmode is used.
        reason: :class:`str`
            The reason for creating the post. Shows up on the audit log.

        Returns
        -------
        :class:`Thread`
            The created post/thread.

        Raises
        ------
        Forbidden
            You do not have permissions to create a post.
        HTTPException
            Creating the post failed.
        InvalidArgument
            You provided invalid arguments.
        """
        from ..errors import InvalidArgument
        from ..file import File
        from ..flags import MessageFlags

        state = self._state
        message_content = str(content) if content is not None else None

        if embed is not None and embeds is not None:
            raise InvalidArgument("cannot pass both embed and embeds parameter to create_thread()")

        if embed is not None:
            embed = embed.to_dict()

        elif embeds is not None:
            if len(embeds) > 10:
                raise InvalidArgument("embeds parameter must be a list of up to 10 elements")
            embeds = [e.to_dict() for e in embeds]

        if stickers is not None:
            stickers = [sticker.id for sticker in stickers]

        if allowed_mentions is None:
            allowed_mentions = state.allowed_mentions and state.allowed_mentions.to_dict()
        elif state.allowed_mentions is not None:
            allowed_mentions = state.allowed_mentions.merge(allowed_mentions).to_dict()
        else:
            allowed_mentions = allowed_mentions.to_dict()

        flags = MessageFlags(
            suppress_embeds=bool(suppress),
            suppress_notifications=bool(silent),
        )

        if view:
            if not hasattr(view, "__discord_ui_view__"):
                raise InvalidArgument(f"view parameter must be View not {view.__class__!r}")

            components = view.to_components()
            if view.is_components_v2():
                if embeds or content:
                    raise TypeError("cannot send embeds or content with a view using v2 component logic")
                flags.is_components_v2 = True
        else:
            components = None

        if applied_tags is not None:
            applied_tags = [str(tag.id) for tag in applied_tags]

        if file is not None and files is not None:
            raise InvalidArgument("cannot pass both file and files parameter to create_thread()")

        if files is not None:
            if len(files) > 10:
                raise InvalidArgument("files parameter must be a list of up to 10 elements")
            elif not all(isinstance(f, File) for f in files):
                raise InvalidArgument("files parameter must be a list of File")

        if file is not None:
            if not isinstance(file, File):
                raise InvalidArgument("file parameter must be File")
            files = [file]

        try:
            data = await state.http.start_forum_thread(
                self.id,
                content=message_content,
                name=name,
                files=files,
                embed=embed,
                embeds=embeds,
                nonce=nonce,
                allowed_mentions=allowed_mentions,
                stickers=stickers,
                components=components,
                auto_archive_duration=auto_archive_duration
                if auto_archive_duration is not MISSING
                else self.default_auto_archive_duration,
                rate_limit_per_user=slowmode_delay
                if slowmode_delay is not MISSING
                else self.default_thread_slowmode_delay,
                applied_tags=applied_tags,
                flags=flags.value,
                reason=reason,
            )
        finally:
            if files is not None:
                for f in files:
                    f.close()

        from .thread import Thread

        ret = Thread(guild=self.guild, state=self._state, data=data)
        msg = ret.get_partial_message(int(data["last_message_id"]))
        if view and view.is_dispatchable():
            await state.store_view(view, msg.id)

        if delete_message_after is not None:
            await msg.delete(delay=delete_message_after)
        return ret


P_guild_messageable = TypeVar(
    "P_guild_messageable",
    bound="TextChannelPayload | NewsChannelPayload | VoiceChannelPayload | StageChannelPayload | ForumChannelPayload",
    default="TextChannelPayload | NewsChannelPayload | VoiceChannelPayload | StageChannelPayload | ForumChannelPayload",
)


class GuildMessageableChannel(Messageable, ABC):
    """An ABC mixin for guild channels that support messaging.

    This includes text and news channels, as well as threads. Voice and stage channels
    do not support direct messaging (though they can have threads).

    This is a mixin class that adds messaging capabilities to guild channels.

    .. versionadded:: 3.0

    Attributes
    ----------
    topic: str | None
        The channel's topic. ``None`` if it doesn't exist.
    nsfw: bool
        Whether the channel is marked as NSFW.
    slowmode_delay: int
        The number of seconds a member must wait between sending messages
        in this channel. A value of ``0`` denotes that it is disabled.
        Bots and users with :attr:`~Permissions.manage_channels` or
        :attr:`~Permissions.manage_messages` bypass slowmode.
    last_message_id: int | None
        The ID of the last message sent in this channel. It may not always point to an existing or valid message.
    """

    __slots__ = ()  # Mixin class - slots defined in concrete classes

    # Attributes expected from inheriting classes
    id: int
    guild: Guild
    _state: ConnectionState
    topic: str | None
    nsfw: bool
    slowmode_delay: int
    last_message_id: int | None

    async def _update(self, data) -> None:
        """Update mutable attributes from API payload."""
        await super()._update(data)
        # This data may be missing depending on how this object is being created/updated
        if not data.pop("_invoke_flag", False):
            self.topic = data.get("topic")
            self.nsfw = data.get("nsfw", False)
            # Does this need coercion into `int`? No idea yet.
            self.slowmode_delay = data.get("rate_limit_per_user", 0)
            self.last_message_id = get_as_snowflake(data, "last_message_id")

    @copy_doc(GuildChannel.permissions_for)
    @override
    def permissions_for(self, obj: Member | Role, /) -> Permissions:
        base = super().permissions_for(obj)

        # text channels do not have voice related permissions
        denied = Permissions.voice()
        base.value &= ~denied.value
        return base

    async def get_members(self) -> list[Member]:
        """Returns all members that can see this channel."""
        return [m for m in await self.guild.get_members() if self.permissions_for(m).read_messages]

    async def get_last_message(self) -> Message | None:
        """Fetches the last message from this channel in cache.

        The message might not be valid or point to an existing message.

        .. admonition:: Reliable Fetching
            :class: helpful

            For a slightly more reliable method of fetching the
            last message, consider using either :meth:`history`
            or :meth:`fetch_message` with the :attr:`last_message_id`
            attribute.

        Returns
        -------
        Optional[:class:`Message`]
            The last message in this channel or ``None`` if not found.
        """
        return await self._state._get_message(self.last_message_id) if self.last_message_id else None

    async def edit(self, **options) -> Self:
        """Edits the channel."""
        raise NotImplementedError

    @copy_doc(GuildChannel.clone)
    @override
    async def clone(self, *, name: str | None = None, reason: str | None = None) -> Self:
        return await self._clone_impl(
            {
                "topic": self.topic,
                "nsfw": self.nsfw,
                "rate_limit_per_user": self.slowmode_delay,
            },
            name=name,
            reason=reason,
        )

    async def delete_messages(self, messages: Iterable[Snowflake], *, reason: str | None = None) -> None:
        """|coro|

        Deletes a list of messages. This is similar to :meth:`Message.delete`
        except it bulk deletes multiple messages.

        As a special case, if the number of messages is 0, then nothing
        is done. If the number of messages is 1 then single message
        delete is done. If it's more than two, then bulk delete is used.

        You cannot bulk delete more than 100 messages or messages that
        are older than 14 days old.

        You must have the :attr:`~Permissions.manage_messages` permission to
        use this.

        Parameters
        ----------
        messages: Iterable[:class:`abc.Snowflake`]
            An iterable of messages denoting which ones to bulk delete.
        reason: Optional[:class:`str`]
            The reason for deleting the messages. Shows up on the audit log.

        Raises
        ------
        ClientException
            The number of messages to delete was more than 100.
        Forbidden
            You do not have proper permissions to delete the messages.
        NotFound
            If single delete, then the message was already deleted.
        HTTPException
            Deleting the messages failed.
        """
        if not isinstance(messages, (list, tuple)):
            messages = list(messages)

        if len(messages) == 0:
            return  # do nothing

        if len(messages) == 1:
            message_id: int = messages[0].id
            await self._state.http.delete_message(self.id, message_id, reason=reason)
            return

        if len(messages) > 100:
            raise ClientException("Can only bulk delete messages up to 100 messages")

        message_ids: SnowflakeList = [m.id for m in messages]
        await self._state.http.delete_messages(self.id, message_ids, reason=reason)

    async def purge(
        self,
        *,
        limit: int | None = 100,
        check: Callable[[Message], bool] | Undefined = MISSING,
        before: SnowflakeTime | None = None,
        after: SnowflakeTime | None = None,
        around: SnowflakeTime | None = None,
        oldest_first: bool | None = False,
        bulk: bool = True,
        reason: str | None = None,
    ) -> list[Message]:
        """|coro|

        Purges a list of messages that meet the criteria given by the predicate
        ``check``. If a ``check`` is not provided then all messages are deleted
        without discrimination.

        You must have the :attr:`~Permissions.manage_messages` permission to
        delete messages even if they are your own.
        The :attr:`~Permissions.read_message_history` permission is
        also needed to retrieve message history.

        Parameters
        ----------
        limit: Optional[:class:`int`]
            The number of messages to search through. This is not the number
            of messages that will be deleted, though it can be.
        check: Callable[[:class:`Message`], :class:`bool`]
            The function used to check if a message should be deleted.
            It must take a :class:`Message` as its sole parameter.
        before: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
            Same as ``before`` in :meth:`history`.
        after: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
            Same as ``after`` in :meth:`history`.
        around: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
            Same as ``around`` in :meth:`history`.
        oldest_first: Optional[:class:`bool`]
            Same as ``oldest_first`` in :meth:`history`.
        bulk: :class:`bool`
            If ``True``, use bulk delete. Setting this to ``False`` is useful for mass-deleting
            a bot's own messages without :attr:`Permissions.manage_messages`. When ``True``, will
            fall back to single delete if messages are older than two weeks.
        reason: Optional[:class:`str`]
            The reason for deleting the messages. Shows up on the audit log.

        Returns
        -------
        List[:class:`.Message`]
            The list of messages that were deleted.

        Raises
        ------
        Forbidden
            You do not have proper permissions to do the actions required.
        HTTPException
            Purging the messages failed.

        Examples
        --------

        Deleting bot's messages ::

            def is_me(m):
                return m.author == client.user


            deleted = await channel.purge(limit=100, check=is_me)
            await channel.send(f"Deleted {len(deleted)} message(s)")
        """
        return await _purge_messages_helper(
            self,
            limit=limit,
            check=check,
            before=before,
            after=after,
            around=around,
            oldest_first=oldest_first,
            bulk=bulk,
            reason=reason,
        )

    async def webhooks(self) -> list[Webhook]:
        """|coro|

        Gets the list of webhooks from this channel.

        Requires :attr:`~.Permissions.manage_webhooks` permissions.

        Returns
        -------
        List[:class:`Webhook`]
            The webhooks for this channel.

        Raises
        ------
        Forbidden
            You don't have permissions to get the webhooks.
        """

        from .webhook import Webhook

        data = await self._state.http.channel_webhooks(self.id)
        return [Webhook.from_state(d, state=self._state) for d in data]

    async def create_webhook(self, *, name: str, avatar: bytes | None = None, reason: str | None = None) -> Webhook:
        """|coro|

        Creates a webhook for this channel.

        Requires :attr:`~.Permissions.manage_webhooks` permissions.

        .. versionchanged:: 1.1
            Added the ``reason`` keyword-only parameter.

        Parameters
        ----------
        name: :class:`str`
            The webhook's name.
        avatar: Optional[:class:`bytes`]
            A :term:`py:bytes-like object` representing the webhook's default avatar.
            This operates similarly to :meth:`~ClientUser.edit`.
        reason: Optional[:class:`str`]
            The reason for creating this webhook. Shows up in the audit logs.

        Returns
        -------
        :class:`Webhook`
            The created webhook.

        Raises
        ------
        HTTPException
            Creating the webhook failed.
        Forbidden
            You do not have permissions to create a webhook.
        """

        from .webhook import Webhook

        if avatar is not None:
            avatar = bytes_to_base64_data(avatar)  # type: ignore

        data = await self._state.http.create_webhook(self.id, name=str(name), avatar=avatar, reason=reason)
        return Webhook.from_state(data, state=self._state)

    async def follow(self, *, destination: TextChannel, reason: str | None = None) -> Webhook:
        """
        Follows a channel using a webhook.

        Only news channels can be followed.

        .. note::

            The webhook returned will not provide a token to do webhook
            actions, as Discord does not provide it.

        .. versionadded:: 1.3

        Parameters
        ----------
        destination: :class:`TextChannel`
            The channel you would like to follow from.
        reason: Optional[:class:`str`]
            The reason for following the channel. Shows up on the destination guild's audit log.

            .. versionadded:: 1.4

        Returns
        -------
        :class:`Webhook`
            The created webhook.

        Raises
        ------
        HTTPException
            Following the channel failed.
        Forbidden
            You do not have the permissions to create a webhook.
        """

        from .news import NewsChannel
        from .text import TextChannel

        if not isinstance(self, NewsChannel):
            raise ClientException("The channel must be a news channel.")

        if not isinstance(destination, TextChannel):
            raise InvalidArgument(f"Expected TextChannel received {destination.__class__.__name__}")

        from .webhook import Webhook

        data = await self._state.http.follow_webhook(self.id, webhook_channel_id=destination.id, reason=reason)
        return Webhook._as_follower(data, channel=destination, user=self._state.user)

    def get_partial_message(self, message_id: int, /) -> PartialMessage:
        """Creates a :class:`PartialMessage` from the message ID.

        This is useful if you want to work with a message and only have its ID without
        doing an unnecessary API call.

        .. versionadded:: 1.6

        Parameters
        ----------
        message_id: :class:`int`
            The message ID to create a partial message for.

        Returns
        -------
        :class:`PartialMessage`
            The partial message.
        """

        from .message import PartialMessage

        return PartialMessage(channel=self, id=message_id)
