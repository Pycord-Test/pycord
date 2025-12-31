.. currentmodule:: discord

.. _discord_api_gears:

Gears
=====

Gears are a modular event handling system in Pycord that allow you to organize your event listeners
into reusable components. They provide a clean way to structure event-driven code and enable
composition by allowing gears to be attached to other gears or to the bot itself.

Gear
----

.. attributetable:: discord.gears.Gear

.. autoclass:: discord.gears.Gear
    :members:
    :inherited-members:
    :exclude-members: listen,listen_component,listen_modal

    .. automethod:: discord.gears.Gear.listen(event, once=False)
        :decorator:

    .. automethod:: discord.gears.Gear.listen_component(predicate, once=False)
        :decorator:

    .. automethod:: discord.gears.Gear.listen_modal(predicate, once=False)
        :decorator:

Basic Usage
-----------

Creating a Gear
~~~~~~~~~~~~~~~

You can create a gear by subclassing :class:`discord.gears.Gear` and using the :meth:`~discord.gears.Gear.listen`
decorator to register event listeners:

.. code-block:: python3

    from discord.gears import Gear
    from discord.events import Ready, MessageCreate

    class MyGear(Gear):
        @Gear.listen()
        async def on_ready(self, event: Ready) -> None:
            print(f"Bot is ready!")

        @Gear.listen()
        async def on_message(self, event: MessageCreate) -> None:
            print(f"Message: {event.content}")

Attaching Gears
~~~~~~~~~~~~~~~

Gears can be attached to a :class:`Client` or :class:`Bot` using the :meth:`~Client.attach_gear` method:

.. code-block:: python3

    bot = discord.Bot()
    my_gear = MyGear()
    bot.attach_gear(my_gear)

You can also attach gears to other gears, creating a hierarchy:

.. code-block:: python3

    parent_gear = MyGear()
    child_gear = AnotherGear()
    parent_gear.attach_gear(child_gear)

Instance Listeners
~~~~~~~~~~~~~~~~~~

You can also add listeners to a gear instance dynamically:

.. code-block:: python3

    my_gear = MyGear()

    @my_gear.listen()
    async def on_guild_join(event: GuildJoin) -> None:
        print(f"Joined guild: {event.guild.name}")

Advanced Usage
--------------

One-Time Listeners
~~~~~~~~~~~~~~~~~~

Use the ``once`` parameter to create listeners that are automatically removed after being called once:

.. code-block:: python3

    class MyGear(Gear):
        @Gear.listen(once=True)
        async def on_first_message(self, event: MessageCreate) -> None:
            print("This will only run once!")

Component Interactions
~~~~~~~~~~~~~~~~~~~~~~

Gears can handle component interactions (buttons, select menus, etc.) using the
:meth:`~discord.gears.Gear.listen_component` decorator:

.. code-block:: python3

    from discord.gears import Gear
    from discord import ComponentInteraction

    class ButtonGear(Gear):
        @Gear.listen_component("my_button")
        async def handle_button(self, interaction: ComponentInteraction) -> None:
            await interaction.respond("Button clicked!")

        @Gear.listen_component(lambda custom_id: custom_id.startswith("page_"))
        async def handle_pagination(self, interaction: ComponentInteraction) -> None:
            page = interaction.custom_id.split("_")[1]
            await interaction.respond(f"Navigating to page {page}")

The predicate can be:

- A string for exact custom ID matching
- A function (sync or async) that takes a custom ID and returns a boolean

You can also add component listeners to gear instances:

.. code-block:: python3

    my_gear = ButtonGear()

    @my_gear.listen_component("instance_button")
    async def handle_instance_button(interaction: ComponentInteraction) -> None:
        await interaction.respond("Instance button clicked!")

Modal Interactions
~~~~~~~~~~~~~~~~~~

Similarly, gears can handle modal submissions using the :meth:`~discord.gears.Gear.listen_modal` decorator:

.. code-block:: python3

    from discord.gears import Gear
    from discord import ModalInteraction
    from discord.components import PartialLabel, PartialTextInput

    class FormGear(Gear):
        @Gear.listen_modal("feedback_form")
        async def handle_feedback(
            self,
            interaction: ModalInteraction[
                PartialLabel[PartialTextInput],
                PartialLabel[PartialTextInput],
            ],
        ) -> None:
            title = interaction.components[0].component.value
            content = interaction.components[1].component.value
            await interaction.respond(f"Feedback received: {title}")

        @Gear.listen_modal(lambda custom_id: custom_id.startswith("form_"))
        async def handle_dynamic_form(self, interaction: ModalInteraction) -> None:
            form_id = interaction.custom_id.split("_")[1]
            await interaction.respond(f"Processing form {form_id}")

Like component listeners, modal listeners can use string or function predicates and support the ``once`` parameter.

Manual Listener Management
~~~~~~~~~~~~~~~~~~~~~~~~~~

You can manually add and remove listeners using :meth:`~discord.gears.Gear.add_listener` and
:meth:`~discord.gears.Gear.remove_listener`:

.. code-block:: python3

    from discord.events import MessageCreate

    async def my_listener(event: MessageCreate) -> None:
        print(f"Message: {event.content}")

    gear = MyGear()
    gear.add_listener(my_listener, event=MessageCreate)

    # Later, remove it
    gear.remove_listener(my_listener, event=MessageCreate)

Detaching Gears
~~~~~~~~~~~~~~~

Remove a gear using :meth:`~discord.gears.Gear.detach_gear`:

.. code-block:: python3

    bot.detach_gear(my_gear)

Client and Bot Integration
---------------------------

Both :class:`Client` and :class:`Bot` provide gear-related methods:

- :meth:`Client.attach_gear` - Attach a gear to the client
- :meth:`Client.detach_gear` - Detach a gear from the client
- :meth:`Client.add_listener` - Add an event listener directly
- :meth:`Client.remove_listener` - Remove an event listener
- :meth:`Client.listen` - Decorator to add listeners to the client

These methods work identically to their :class:`~discord.gears.Gear` counterparts.

Example: Modular Bot Structure
-------------------------------

Here's an example of using gears to create a modular bot:

.. code-block:: python3

    from discord import Bot
    from discord.gears import Gear
    from discord.events import Ready, MessageCreate, GuildJoin

    class LoggingGear(Gear):
        @Gear.listen()
        async def log_ready(self, event: Ready) -> None:
            print("Bot started!")

        @Gear.listen()
        async def log_messages(self, event: MessageCreate) -> None:
            print(f"[{event.channel.name}] {event.author}: {event.content}")

    class ModerationGear(Gear):
        @Gear.listen()
        async def welcome_new_guilds(self, event: GuildJoin) -> None:
            system_channel = event.guild.system_channel
            if system_channel:
                await system_channel.send("Thanks for adding me!")

    bot = Bot()

    # Attach gears to the bot
    bot.attach_gear(LoggingGear())
    bot.attach_gear(ModerationGear())

    bot.run("TOKEN")
