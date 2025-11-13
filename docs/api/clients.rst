.. currentmodule:: discord

Client Objects
==============

Bots
----

.. attributetable:: Bot
.. autoclass:: Bot
    :members:
    :inherited-members:
    :exclude-members: command, message_command, slash_command, user_command, listen

    .. automethod:: Bot.command(**kwargs)
        :decorator:

    .. automethod:: Bot.message_command(**kwargs)
        :decorator:

    .. automethod:: Bot.slash_command(**kwargs)
        :decorator:

    .. automethod:: Bot.user_command(**kwargs)
        :decorator:

    .. automethod:: Bot.listen(event, once=False)
        :decorator:

.. attributetable:: AutoShardedBot
.. autoclass:: AutoShardedBot
    :members:


Clients
-------

.. attributetable:: Client
.. autoclass:: Client
    :members:
    :exclude-members: fetch_guilds, listen

    .. automethod:: Client.fetch_guilds
        :async-for:

    .. automethod:: Client.listen(event, once=False)
        :decorator:

.. attributetable:: AutoShardedClient
.. autoclass:: AutoShardedClient
    :members:
