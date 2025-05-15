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

from typing import Any, Self
from discord import utils
from discord.app.state import ConnectionState
from discord.channel import StageChannel, TextChannel, VoiceChannel
from discord.emoji import AppEmoji, GuildEmoji
from discord.guild import Guild
from discord.member import Member
from discord.partial_emoji import PartialEmoji
from discord.poll import Poll, PollAnswer, PollAnswerCount
from discord.raw_models import RawBulkMessageDeleteEvent, RawMessageDeleteEvent, RawMessagePollVoteEvent, RawMessageUpdateEvent, RawReactionActionEvent, RawReactionClearEmojiEvent, RawReactionClearEvent
from discord.reaction import Reaction
from discord.threads import Thread
from discord.types.message import Reaction as ReactionPayload
from discord.types.raw_models import ReactionActionEvent, ReactionClearEvent
from discord.user import User
from discord.utils import Undefined
from ..message import Message, PartialMessage
from ..app.event_emitter import Event


class MessageCreate(Event, Message):
    __event_name__ = "MESSAGE_CREATE"

    @classmethod
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        channel, _ = await state._get_guild_channel(data)
        message = await Message._from_data(channel=channel, data=data, state=state)
        self = cls()
        self.__dict__.update(message.__dict__)

        await state.cache.store_message(data, channel)
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
    __event_name__ = "MESSAGE_DELETE"

    raw: RawMessageDeleteEvent

    @classmethod
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        self = cls()
        raw = RawMessageDeleteEvent(data)
        msg = await state._get_message(raw.message_id)
        raw.cached_message = msg
        self.raw = raw
        if msg is not None:
            await state.cache.delete_message(raw.message_id)
            self.__dict__.update(msg.__dict__)

        return self


class MessageDeleteBulk(Event):
    __event_name__ = "MESSAGE_DELETE_BULK"

    raw: RawBulkMessageDeleteEvent
    messages: list[Message]

    @classmethod
    async def __load__(cls, data: Any, state: ConnectionState) -> Self :
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
    __event_name__ = "MESSAGE_UPDATE"

    raw: RawMessageUpdateEvent
    old: Message | Undefined

    @classmethod
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
            self.old = utils.MISSING
            if poll_data := data.get("poll"):
                channel = await state.get_channel(raw.channel_id)
                await state.store_poll(Poll.from_dict(poll_data, PartialMessage(channel=channel, id=raw.message_id)), message_id=raw.message_id)

        return self


class ReactionAdd(Event):
    __event_name__ = "MESSAGE_REACTION_ADD"

    raw: RawReactionActionEvent
    user: Member | User | Undefined
    reaction: Reaction

    @classmethod
    async def __load__(cls, data: ReactionActionEvent, state: ConnectionState) -> Self:
        self = cls()
        emoji = data["emoji"]
        emoji_id = utils._get_as_snowflake(emoji, "id")
        emoji = PartialEmoji.with_state(
            state, id=emoji_id, animated=emoji.get("animated", False), name=emoji["name"]
        )
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
                self.user = utils.MISSING

        return self

class ReactionClear(Event):
    __event_name__ = "MESSAGE_REACTION_REMOVE_ALL"

    raw: RawReactionClearEvent
    message: Message | Undefined
    old_reactions: list[Reaction] | Undefined

    @classmethod
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
            self.message = utils.MISSING
            self.old_reactions = utils.MISSING
        return self

class ReactionRemove(Event):
    __event_name__ = "MESSAGE_REACTION_REMOVE"

    raw: RawReactionActionEvent
    user: Member | User | Undefined
    reaction: Reaction

    @classmethod
    async def __load__(cls, data: ReactionActionEvent, state: ConnectionState) -> Self:
        self = cls()
        emoji = data["emoji"]
        emoji_id = utils._get_as_snowflake(emoji, "id")
        emoji = PartialEmoji.with_state(
            state, id=emoji_id, animated=emoji.get("animated", False), name=emoji["name"]
        )
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
                    self.user = utils.MISSING

        return self


class ReactionRemoveEmoji(Event, Reaction):
    __event_name__ = "MESSAGE_REACTION_REMOVE_EMOJI"

    def __init__(self):
        pass

    @classmethod
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        emoji = data["emoji"]
        emoji_id = utils._get_as_snowflake(emoji, "id")
        emoji = PartialEmoji.with_state(self, id=emoji_id, name=emoji["name"])
        raw = RawReactionClearEmojiEvent(data, emoji)

        message = await state._get_message(raw.message_id)
        if message is not None:
            try:
                reaction = message._clear_emoji(emoji)
                await state.cache.upsert_message(message)
            except (AttributeError, ValueError): # evetnaul consistency
                pass
            else:
                if reaction:
                    self = cls()
                    self.__dict__.update(reaction.__dict__)
                    return self


class PollVoteAdd(Event):
    __event_name__ = "MESSAGE_POLL_VOTE_ADD"

    raw: RawMessagePollVoteEvent
    guild: Guild | Undefined
    user: User | Member | None
    poll: Poll
    answer: PollAnswer

    @classmethod
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        self = cls()
        raw = RawMessagePollVoteEvent(data, False)
        self.raw = raw
        guild = await state._get_guild(raw.guild_id)
        if guild:
            self.user = guild.get_member(raw.user_id)
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
                    counts[answer.id] = PollAnswerCount(
                        {"id": answer.id, "count": 1, "me_voted": False}
                    )
        if poll is not None and self.user is not None:
            answer = poll.get_answer(raw.answer_id)
            if answer is not None:
                self.poll = poll
                self.answer = answer
                return self

class PollVoteRemove(Event):
    __event_name__ = "MESSAGE_POLL_VOTE_REMOVE"

    raw: RawMessagePollVoteEvent
    guild: Guild | Undefined
    user: User | Member | None
    poll: Poll
    answer: PollAnswer

    @classmethod
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        self = cls()
        raw = RawMessagePollVoteEvent(data, False)
        self.raw = raw
        guild = await state._get_guild(raw.guild_id)
        if guild:
            self.user = guild.get_member(raw.user_id)
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
                    counts[answer.id] = PollAnswerCount(
                        {"id": answer.id, "count": 1, "me_voted": False}
                    )
        if poll is not None and self.user is not None:
            answer = poll.get_answer(raw.answer_id)
            if answer is not None:
                self.poll = poll
                self.answer = answer
                return self
