.. currentmodule:: discord

.. _discord-api-events:

Event Reference
===============

This section outlines the different types of events in Pycord. Events are class-based objects that inherit from
:class:`~discord.app.event_emitter.Event` and are dispatched by the Discord gateway when certain actions occur.

.. seealso::

    For information about the Gears system and modular event handling, see :ref:`discord_api_gears`.

Listening to Events
-------------------

There are two main ways to listen to events in Pycord:

1. **Using** :meth:`Client.listen` **decorator** - This allows you to register typed event listeners directly on the client.
2. **Using Gears** - A modular event handling system that allows you to organize event listeners into reusable components.

Using the listen() Decorator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The modern way to register event listeners is by using the :meth:`~Client.listen` decorator with typed event classes:

.. code-block:: python3

    import discord
    from discord.events import MessageCreate, Ready

    client = discord.Client(intents=discord.Intents.default())

    @client.listen()
    async def on_message(event: MessageCreate) -> None:
        if event.author == client.user:
            return
        if event.content.startswith('$hello'):
            await event.channel.send('Hello World!')

    @client.listen(once=True)
    async def on_ready(event: Ready) -> None:
        print("Client is ready!")

    client.run("TOKEN")

Note that:

- Event listeners use type annotations to specify which event they handle
- Event objects may inherit from domain models (e.g., ``MessageCreate`` inherits from ``Message``)
- The ``once=True`` parameter creates a one-time listener that is automatically removed after being called once
- All event listeners must be coroutines (``async def`` functions)

Using Gears
~~~~~~~~~~~

For more organized code, especially in larger bots, you can use the Gears system:

.. code-block:: python3

    from discord.gears import Gear
    from discord.events import Ready, MessageCreate

    class MyGear(Gear):
        @Gear.listen()
        async def on_ready(self, event: Ready) -> None:
            print("Bot is ready!")

        @Gear.listen()
        async def on_message(self, event: MessageCreate) -> None:
            print(f"Message: {event.content}")

    bot = discord.Bot()
    bot.attach_gear(MyGear())
    bot.run("TOKEN")

See :ref:`discord_api_gears` for more information on using Gears.

.. warning::

    All event listeners must be |coroutine_link|_. If they aren't, then you might get unexpected
    errors. In order to turn a function into a coroutine they must be ``async def`` functions.

Event Classes
-------------

All events inherit from the base :class:`~discord.app.event_emitter.Event` class. Events are typed objects that
contain data related to the specific Discord gateway event that occurred.

Some event classes inherit from domain models, meaning they have all the attributes and methods of that model.
For example:

- :class:`~discord.events.MessageCreate` inherits from :class:`Message`
- :class:`~discord.events.GuildMemberJoin` inherits from :class:`Member`
- :class:`~discord.events.GuildJoin` inherits from :class:`Guild`

Events that don't inherit from a domain model will have specific attributes for accessing event data.

Many events also include a ``raw`` attribute that contains the raw event payload data from Discord, which can be
useful for accessing data that may not be in the cache.

Available Events
----------------

Below is a comprehensive list of all events available in Pycord, organized by category.

Audit Logs
~~~~~~~~~~

.. autoclass:: discord.events.GuildAuditLogEntryCreate()
    :members:
    :inherited-members:

AutoMod
~~~~~~~

.. autoclass:: discord.events.AutoModRuleCreate()
    :members:
    :inherited-members:

.. autoclass:: discord.events.AutoModRuleUpdate()
    :members:
    :inherited-members:

.. autoclass:: discord.events.AutoModRuleDelete()
    :members:
    :inherited-members:

.. autoclass:: discord.events.AutoModActionExecution()
    :members:
    :inherited-members:

Channels
~~~~~~~~

.. autoclass:: discord.events.ChannelCreate()
    :members:
    :inherited-members:

.. autoclass:: discord.events.ChannelDelete()
    :members:
    :inherited-members:

.. autoclass:: discord.events.ChannelUpdate()
    :members:
    :inherited-members:

.. autoclass:: discord.events.GuildChannelUpdate()
    :members:
    :inherited-members:

.. autoclass:: discord.events.PrivateChannelUpdate()
    :members:
    :inherited-members:

.. autoclass:: discord.events.ChannelPinsUpdate()
    :members:
    :inherited-members:

Connection & Gateway
~~~~~~~~~~~~~~~~~~~~

.. autoclass:: discord.events.Ready()
    :members:
    :inherited-members:

.. autoclass:: discord.events.Resumed()
    :members:
    :inherited-members:

Entitlements & Monetization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: discord.events.EntitlementCreate()
    :members:
    :inherited-members:

.. autoclass:: discord.events.EntitlementUpdate()
    :members:
    :inherited-members:

.. autoclass:: discord.events.EntitlementDelete()
    :members:
    :inherited-members:

.. autoclass:: discord.events.SubscriptionCreate()
    :members:
    :inherited-members:

.. autoclass:: discord.events.SubscriptionUpdate()
    :members:
    :inherited-members:

.. autoclass:: discord.events.SubscriptionDelete()
    :members:
    :inherited-members:

Guilds
~~~~~~

.. autoclass:: discord.events.GuildJoin()
    :members:
    :inherited-members:

.. autoclass:: discord.events.GuildCreate()
    :members:
    :inherited-members:

.. autoclass:: discord.events.GuildDelete()
    :members:
    :inherited-members:

.. autoclass:: discord.events.GuildUpdate()
    :members:
    :inherited-members:

.. autoclass:: discord.events.GuildAvailable()
    :members:
    :inherited-members:

.. autoclass:: discord.events.GuildUnavailable()
    :members:
    :inherited-members:

.. autoclass:: discord.events.GuildBanAdd()
    :members:
    :inherited-members:

.. autoclass:: discord.events.GuildBanRemove()
    :members:
    :inherited-members:

.. autoclass:: discord.events.GuildEmojisUpdate()
    :members:
    :inherited-members:

.. autoclass:: discord.events.GuildStickersUpdate()
    :members:
    :inherited-members:

Roles
^^^^^

.. autoclass:: discord.events.GuildRoleCreate()
    :members:
    :inherited-members:

.. autoclass:: discord.events.GuildRoleUpdate()
    :members:
    :inherited-members:

.. autoclass:: discord.events.GuildRoleDelete()
    :members:
    :inherited-members:

Integrations
~~~~~~~~~~~~

.. autoclass:: discord.events.GuildIntegrationsUpdate()
    :members:
    :inherited-members:

.. autoclass:: discord.events.IntegrationCreate()
    :members:
    :inherited-members:

.. autoclass:: discord.events.IntegrationUpdate()
    :members:
    :inherited-members:

.. autoclass:: discord.events.IntegrationDelete()
    :members:
    :inherited-members:

Interactions
~~~~~~~~~~~~

.. autoclass:: discord.events.InteractionCreate()
    :members:
    :inherited-members:

Invites
~~~~~~~

.. autoclass:: discord.events.InviteCreate()
    :members:
    :inherited-members:

.. autoclass:: discord.events.InviteDelete()
    :members:
    :inherited-members:

Members & Users
~~~~~~~~~~~~~~~

.. autoclass:: discord.events.GuildMemberJoin()
    :members:
    :inherited-members:

.. autoclass:: discord.events.GuildMemberRemove()
    :members:
    :inherited-members:

.. autoclass:: discord.events.GuildMemberUpdate()
    :members:
    :inherited-members:

.. autoclass:: discord.events.UserUpdate()
    :members:
    :inherited-members:

.. autoclass:: discord.events.PresenceUpdate()
    :members:
    :inherited-members:

Messages
~~~~~~~~

.. autoclass:: discord.events.MessageCreate()
    :members:
    :inherited-members:

.. autoclass:: discord.events.MessageUpdate()
    :members:
    :inherited-members:

.. autoclass:: discord.events.MessageDelete()
    :members:
    :inherited-members:

.. autoclass:: discord.events.MessageDeleteBulk()
    :members:
    :inherited-members:

Reactions
^^^^^^^^^

.. autoclass:: discord.events.ReactionAdd()
    :members:
    :inherited-members:

.. autoclass:: discord.events.ReactionRemove()
    :members:
    :inherited-members:

.. autoclass:: discord.events.ReactionClear()
    :members:
    :inherited-members:

.. autoclass:: discord.events.ReactionRemoveEmoji()
    :members:
    :inherited-members:

Polls
^^^^^

.. autoclass:: discord.events.PollVoteAdd()
    :members:
    :inherited-members:

.. autoclass:: discord.events.PollVoteRemove()
    :members:
    :inherited-members:

Scheduled Events
~~~~~~~~~~~~~~~~

.. autoclass:: discord.events.GuildScheduledEventCreate()
    :members:
    :inherited-members:

.. autoclass:: discord.events.GuildScheduledEventUpdate()
    :members:
    :inherited-members:

.. autoclass:: discord.events.GuildScheduledEventDelete()
    :members:
    :inherited-members:

.. autoclass:: discord.events.GuildScheduledEventUserAdd()
    :members:
    :inherited-members:

.. autoclass:: discord.events.GuildScheduledEventUserRemove()
    :members:
    :inherited-members:

Soundboard
~~~~~~~~~~

.. autoclass:: discord.events.GuildSoundboardSoundCreate()
    :members:
    :inherited-members:

.. autoclass:: discord.events.GuildSoundboardSoundUpdate()
    :members:
    :inherited-members:

.. autoclass:: discord.events.GuildSoundboardSoundDelete()
    :members:
    :inherited-members:

.. autoclass:: discord.events.GuildSoundboardSoundsUpdate()
    :members:
    :inherited-members:

Stage Instances
~~~~~~~~~~~~~~~

.. autoclass:: discord.events.StageInstanceCreate()
    :members:
    :inherited-members:

.. autoclass:: discord.events.StageInstanceUpdate()
    :members:
    :inherited-members:

.. autoclass:: discord.events.StageInstanceDelete()
    :members:
    :inherited-members:

Threads
~~~~~~~

.. autoclass:: discord.events.ThreadCreate()
    :members:
    :inherited-members:

.. autoclass:: discord.events.ThreadUpdate()
    :members:
    :inherited-members:

.. autoclass:: discord.events.ThreadDelete()
    :members:
    :inherited-members:

.. autoclass:: discord.events.ThreadJoin()
    :members:
    :inherited-members:

.. autoclass:: discord.events.ThreadRemove()
    :members:
    :inherited-members:

.. autoclass:: discord.events.ThreadMemberJoin()
    :members:
    :inherited-members:

.. autoclass:: discord.events.ThreadMemberRemove()
    :members:
    :inherited-members:

Typing
~~~~~~

.. autoclass:: discord.events.TypingStart()
    :members:
    :inherited-members:

Voice
~~~~~

.. autoclass:: discord.events.VoiceStateUpdate()
    :members:
    :inherited-members:

.. autoclass:: discord.events.VoiceServerUpdate()
    :members:
    :inherited-members:

.. autoclass:: discord.events.VoiceChannelStatusUpdate()
    :members:
    :inherited-members:

.. autoclass:: discord.events.VoiceChannelEffectSend()
    :members:
    :inherited-members:

Webhooks
~~~~~~~~

.. autoclass:: discord.events.WebhooksUpdate()
    :members:
    :inherited-members:
