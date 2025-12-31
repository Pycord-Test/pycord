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

from typing import Any

from typing_extensions import Self, override

from discord.app.state import ConnectionState
from discord.channel import StageChannel, TextChannel, VoiceChannel
from discord.channel.thread import Thread
from discord.guild import Guild
from discord.member import Member
from discord.partial_emoji import PartialEmoji
from discord.poll import Poll, PollAnswer, PollAnswerCount
from discord.raw_models import (
    RawBulkMessageDeleteEvent,
    RawMessageDeleteEvent,
    RawMessagePollVoteEvent,
    RawMessageUpdateEvent,
    RawReactionActionEvent,
    RawReactionClearEmojiEvent,
    RawReactionClearEvent,
)
from discord.reaction import Reaction
from discord.types.message import Reaction as ReactionPayload
from discord.types.raw_models import ReactionActionEvent, ReactionClearEvent
from discord.user import User
from discord.utils import MISSING, Undefined
from discord.utils import private as utils

from ..app.event_emitter import Event
from ..message import Message, PartialMessage


class MessageCreate(Event, Message):
    """Called when a message is created and sent.

    This requires :attr:`Intents.messages` to be enabled.

    .. warning::
        Your bot's own messages and private messages are sent through this event.
        This can lead to cases of 'recursion' depending on how your bot was programmed.
        If you want the bot to not reply to itself, consider checking if :attr:`author`
        equals the bot user.

    This event inherits from :class:`Message`.
    """

    __event_name__: str = "MESSAGE_CREATE"

    def __init__(self) -> None: ...

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        channel, _ = await state._get_guild_channel(data)
        message = await Message._from_data(channel=channel, data=data, state=state)
        self = cls()
        self._populate_from_slots(message)

        await state.cache.store_built_message(message)

        # we ensure that the channel is either a TextChannel, VoiceChannel, StageChannel, or Thread
        if channel and channel.__class__ in (
            TextChannel,
            VoiceChannel,
            StageChannel,
            Thread,
        ):
            channel.last_message_id = message.id  # type: ignore

        return self


class MessageDelete(Event, Message):
    """Called when a message is deleted.

    This requires :attr:`Intents.messages` to be enabled.

    This event inherits from :class:`Message`.

    Attributes
    ----------
    raw: :class:`RawMessageDeleteEvent`
        The raw event payload data.
    is_cached: :class:`bool`
        Whether the message was found in the internal cache.
    """

    __event_name__: str = "MESSAGE_DELETE"

    raw: RawMessageDeleteEvent
    is_cached: bool

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        self = cls()
        raw = RawMessageDeleteEvent(data)
        msg = await state._get_message(raw.message_id)
        raw.cached_message = msg
        self.raw = raw
        self.id = raw.message_id
        if msg is not None:
            self.is_cached = True
            await state.cache.delete_message(raw.message_id)
            self.__dict__.update(msg.__dict__)
        else:
            self.is_cached = False

        return self


class MessageDeleteBulk(Event):
    """Called when messages are bulk deleted.

    This requires :attr:`Intents.messages` to be enabled.

    Attributes
    ----------
    raw: :class:`RawBulkMessageDeleteEvent`
        The raw event payload data.
    messages: list[:class:`Message`]
        The messages that have been deleted (only includes cached messages).
    """

    __event_name__: str = "MESSAGE_DELETE_BULK"

    raw: RawBulkMessageDeleteEvent
    messages: list[Message]

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self:
        self = cls()
        raw = RawBulkMessageDeleteEvent(data)
        messages = await state.cache.get_all_messages()
        found_messages = [message for message in messages if message.id in raw.message_ids]
        raw.cached_messages = found_messages
        self.messages = found_messages
        for message in messages:
            await state.cache.delete_message(message.id)
        return self


class MessageUpdate(Event, Message):
    """Called when a message receives an update event.

    This requires :attr:`Intents.messages` to be enabled.

    The following non-exhaustive cases trigger this event:
    - A message has been pinned or unpinned.
    - The message content has been changed.
    - The message has received an embed.
    - The message's embeds were suppressed or unsuppressed.
    - A call message has received an update to its participants or ending time.
    - A poll has ended and the results have been finalized.

    This event inherits from :class:`Message`.

    Attributes
    ----------
    raw: :class:`RawMessageUpdateEvent`
        The raw event payload data.
    old: :class:`Message` | :class:`Undefined`
        The previous version of the message (if it was cached).
    """

    __event_name__: str = "MESSAGE_UPDATE"

    raw: RawMessageUpdateEvent
    old: Message | Undefined

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self:
        self = cls()
        raw = RawMessageUpdateEvent(data)
        msg = await state._get_message(raw.message_id)
        raw.cached_message = msg
        self.raw = raw
        if msg is not None:
            new_msg = await state.cache.store_message(data, msg.channel)
            self.old = msg
            self.old.author = new_msg.author
            self.__dict__.update(new_msg.__dict__)
        else:
            self.old = MISSING
            if poll_data := data.get("poll"):
                channel = await state.get_channel(raw.channel_id)
                await state.store_poll(
                    Poll.from_dict(poll_data, PartialMessage(channel=channel, id=raw.message_id)),
                    message_id=raw.message_id,
                )

        return self


class ReactionAdd(Event):
    """Called when a message has a reaction added to it.

    This requires :attr:`Intents.reactions` to be enabled.

    .. note::
        To get the :class:`Message` being reacted to, access it via :attr:`reaction.message`.

    Attributes
    ----------
    raw: :class:`RawReactionActionEvent`
        The raw event payload data.
    user: :class:`Member` | :class:`User` | :class:`Undefined`
        The user who added the reaction.
    reaction: :class:`Reaction`
        The current state of the reaction.
    """

    __event_name__: str = "MESSAGE_REACTION_ADD"

    raw: RawReactionActionEvent
    user: Member | User | Undefined
    reaction: Reaction

    @classmethod
    @override
    async def __load__(cls, data: ReactionActionEvent, state: ConnectionState) -> Self:
        self = cls()
        emoji = data["emoji"]
        emoji_id = utils.get_as_snowflake(emoji, "id")
        emoji = PartialEmoji.with_state(state, id=emoji_id, animated=emoji.get("animated", False), name=emoji["name"])
        raw = RawReactionActionEvent(data, emoji, "REACTION_ADD")

        member_data = data.get("member")
        if member_data:
            guild = await state._get_guild(raw.guild_id)
            if guild is not None:
                raw.member = await Member._from_data(data=member_data, guild=guild, state=state)
            else:
                raw.member = None
        else:
            raw.member = None

        message = await state._get_message(raw.message_id)
        if message is not None:
            emoji = await state._upgrade_partial_emoji(emoji)
            self.reaction = message._add_reaction(data, emoji, raw.user_id)
            await state.cache.upsert_message(message)
            user = raw.member or await state._get_reaction_user(message.channel, raw.user_id)

            if user:
                self.user = user
            else:
                self.user = MISSING

        return self


class ReactionClear(Event):
    """Called when a message has all its reactions removed from it.

    This requires :attr:`Intents.reactions` to be enabled.

    Attributes
    ----------
    raw: :class:`RawReactionClearEvent`
        The raw event payload data.
    message: :class:`Message` | :class:`Undefined`
        The message that had its reactions cleared.
    old_reactions: list[:class:`Reaction`] | :class:`Undefined`
        The reactions that were removed.
    """

    __event_name__: str = "MESSAGE_REACTION_REMOVE_ALL"

    raw: RawReactionClearEvent
    message: Message | Undefined
    old_reactions: list[Reaction] | Undefined

    @classmethod
    @override
    async def __load__(cls, data: ReactionClearEvent, state: ConnectionState) -> Self | None:
        self = cls()
        self.raw = RawReactionClearEvent(data)
        message = await state._get_message(self.raw.message_id)
        if message is not None:
            old_reactions: list[Reaction] = message.reactions.copy()
            message.reactions.clear()
            self.message = message
            self.old_reactions = old_reactions
        else:
            self.message = MISSING
            self.old_reactions = MISSING
        return self


class ReactionRemove(Event):
    """Called when a message has a reaction removed from it.

    This requires :attr:`Intents.reactions` to be enabled.

    .. note::
        To get the :class:`Message` being reacted to, access it via :attr:`reaction.message`.

    Attributes
    ----------
    raw: :class:`RawReactionActionEvent`
        The raw event payload data.
    user: :class:`Member` | :class:`User` | :class:`Undefined`
        The user who removed the reaction.
    reaction: :class:`Reaction`
        The current state of the reaction.
    """

    __event_name__: str = "MESSAGE_REACTION_REMOVE"

    raw: RawReactionActionEvent
    user: Member | User | Undefined
    reaction: Reaction

    @classmethod
    @override
    async def __load__(cls, data: ReactionActionEvent, state: ConnectionState) -> Self:
        self = cls()
        emoji = data["emoji"]
        emoji_id = utils.get_as_snowflake(emoji, "id")
        emoji = PartialEmoji.with_state(state, id=emoji_id, animated=emoji.get("animated", False), name=emoji["name"])
        raw = RawReactionActionEvent(data, emoji, "REACTION_ADD")

        member_data = data.get("member")
        if member_data:
            guild = await state._get_guild(raw.guild_id)
            if guild is not None:
                raw.member = await Member._from_data(data=member_data, guild=guild, state=state)
            else:
                raw.member = None
        else:
            raw.member = None

        message = await state._get_message(raw.message_id)
        if message is not None:
            emoji = await state._upgrade_partial_emoji(emoji)
            try:
                self.reaction = message._remove_reaction(data, emoji, raw.user_id)
                await state.cache.upsert_message(message)
            except (AttributeError, ValueError):  # eventual consistency lol
                pass
            else:
                user = await state._get_reaction_user(message.channel, raw.user_id)
                if user:
                    self.user = user
                else:
                    self.user = MISSING

        return self


class ReactionRemoveEmoji(Event, Reaction):
    """Called when a message has a specific reaction removed from it.

    This requires :attr:`Intents.reactions` to be enabled.

    This event inherits from :class:`Reaction`.
    """

    __event_name__: str = "MESSAGE_REACTION_REMOVE_EMOJI"

    def __init__(self):
        pass

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        emoji = data["emoji"]
        emoji_id = utils.get_as_snowflake(emoji, "id")
        emoji = PartialEmoji.with_state(state, id=emoji_id, name=emoji["name"])
        raw = RawReactionClearEmojiEvent(data, emoji)

        message = await state._get_message(raw.message_id)
        if message is not None:
            try:
                reaction = message._clear_emoji(emoji)
                await state.cache.upsert_message(message)
            except (AttributeError, ValueError):  # evetnaul consistency
                pass
            else:
                if reaction:
                    self = cls()
                    self.__dict__.update(reaction.__dict__)
                    return self


class PollVoteAdd(Event):
    """Called when a vote is cast on a poll.

    This requires :attr:`Intents.polls` to be enabled.

    Attributes
    ----------
    raw: :class:`RawMessagePollVoteEvent`
        The raw event payload data.
    guild: :class:`Guild` | :class:`Undefined`
        The guild where the poll vote occurred, if in a guild.
    user: :class:`User` | :class:`Member` | None
        The user who added the vote.
    poll: :class:`Poll`
        The current state of the poll.
    answer: :class:`PollAnswer`
        The answer that was voted for.
    """

    __event_name__: str = "MESSAGE_POLL_VOTE_ADD"

    raw: RawMessagePollVoteEvent
    guild: Guild | Undefined
    user: User | Member | None
    poll: Poll
    answer: PollAnswer

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        self = cls()
        raw = RawMessagePollVoteEvent(data, False)
        self.raw = raw
        guild = await state._get_guild(raw.guild_id)
        if guild:
            self.user = await guild.get_member(raw.user_id)
        else:
            self.user = await state.get_user(raw.user_id)
        poll = await state.get_poll(raw.message_id)
        if poll and poll.results:
            answer = poll.get_answer(raw.answer_id)
            counts = poll.results._answer_counts
            if answer is not None:
                if answer.id in counts:
                    counts[answer.id].count += 1
                else:
                    counts[answer.id] = PollAnswerCount({"id": answer.id, "count": 1, "me_voted": False})
        if poll is not None and self.user is not None:
            answer = poll.get_answer(raw.answer_id)
            if answer is not None:
                self.poll = poll
                self.answer = answer
                return self


class PollVoteRemove(Event):
    """Called when a vote is removed from a poll.

    This requires :attr:`Intents.polls` to be enabled.

    Attributes
    ----------
    raw: :class:`RawMessagePollVoteEvent`
        The raw event payload data.
    guild: :class:`Guild` | :class:`Undefined`
        The guild where the poll vote occurred, if in a guild.
    user: :class:`User` | :class:`Member` | None
        The user who removed the vote.
    poll: :class:`Poll`
        The current state of the poll.
    answer: :class:`PollAnswer`
        The answer that had its vote removed.
    """

    __event_name__: str = "MESSAGE_POLL_VOTE_REMOVE"

    raw: RawMessagePollVoteEvent
    guild: Guild | Undefined
    user: User | Member | None
    poll: Poll
    answer: PollAnswer

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        self = cls()
        raw = RawMessagePollVoteEvent(data, False)
        self.raw = raw
        guild = await state._get_guild(raw.guild_id)
        if guild:
            self.user = await guild.get_member(raw.user_id)
        else:
            self.user = await state.get_user(raw.user_id)
        poll = await state.get_poll(raw.message_id)
        if poll and poll.results:
            answer = poll.get_answer(raw.answer_id)
            counts = poll.results._answer_counts
            if answer is not None:
                if answer.id in counts:
                    counts[answer.id].count += 1
                else:
                    counts[answer.id] = PollAnswerCount({"id": answer.id, "count": 1, "me_voted": False})
        if poll is not None and self.user is not None:
            answer = poll.get_answer(raw.answer_id)
            if answer is not None:
                self.poll = poll
                self.answer = answer
                return self
