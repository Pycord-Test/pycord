.. _discord_ui_kit:

Bot UI Kit
==========

The library implements a UI Kit that allows you to create interactive components for your Discord applications.

API Objects
-----------

.. attributetable:: discord.ActionRow

.. autoclass:: discord.ActionRow
    :members:
    :inherited-members:

.. attributetable:: discord.Button

.. autoclass:: discord.Button
    :members:
    :inherited-members:

.. attributetable:: discord.StringSelectMenu

.. autoclass:: discord.StringSelectMenu
    :members:
    :inherited-members:

.. attributetable:: discord.TextInput

.. autoclass:: discord.TextInput
    :members:
    :inherited-members:

.. attributetable:: discord.UserSelectMenu

.. autoclass:: discord.UserSelectMenu
    :members:
    :inherited-members:

.. attributetable:: discord.RoleSelectMenu

.. autoclass:: discord.RoleSelectMenu
    :members:
    :inherited-members:

.. attributetable:: discord.MentionableSelectMenu

.. autoclass:: discord.MentionableSelectMenu
    :members:
    :inherited-members:

.. attributetable:: discord.ChannelSelectMenu

.. autoclass:: discord.ChannelSelectMenu
    :members:
    :inherited-members:

.. attributetable:: discord.Section

.. autoclass:: discord.Section
    :members:
    :inherited-members:

.. attributetable:: discord.TextDisplay

.. autoclass:: discord.TextDisplay
    :members:
    :inherited-members:

.. attributetable:: discord.Thumbnail

.. autoclass:: discord.Thumbnail
    :members:
    :inherited-members:

.. attributetable:: discord.MediaGallery

.. autoclass:: discord.MediaGallery
    :members:
    :inherited-members:

.. attributetable:: discord.FileComponent

.. autoclass:: discord.FileComponent
    :members:
    :inherited-members:

.. attributetable:: discord.Separator
.. autoclass:: discord.Separator
    :members:
    :inherited-members:

.. attributetable:: discord.Container
.. autoclass:: discord.Container
    :members:
    :inherited-members:

.. attributetable:: discord.Label
.. autoclass:: discord.Label
    :members:
    :inherited-members:

Interaction Components
-----------
These objects are dataclasses that represent components as they are recieved from Discord in interaction payloads, currently applicable only with :class:`discord.Interaction` of type :data:`discord.InteractionType.modal_submit`.

.. attributetable:: discord.InteractionLabel
.. autoclass:: discord.InteractionLabel
    :members:
    :inherited-members:

.. attributetable:: discord.InteractionStringSelectMenu
.. autoclass:: discord.InteractionStringSelectMenu
    :members:
    :inherited-members:

.. attributetable:: discord.InteractionUserSelectMenu
.. autoclass:: discord.InteractionUserSelectMenu
    :members:
    :inherited-members:

.. attributetable:: discord.InteractionRoleSelectMenu
.. autoclass:: discord.InteractionRoleSelectMenu
    :members:
    :inherited-members:

.. attributetable:: discord.InteractionMentionableSelectMenu
.. autoclass:: discord.InteractionMentionableSelectMenu
    :members:
    :inherited-members:

.. attributetable:: discord.InteractionChannelSelectMenu
.. autoclass:: discord.InteractionChannelSelectMenu
    :members:
    :inherited-members:

.. attributetable:: discord.InteractionTextInput
.. autoclass:: discord.InteractionTextInput
    :members:
    :inherited-members:

.. attributetable:: discord.InteractionTextDisplay
.. autoclass:: discord.InteractionTextDisplay
    :members:
    :inherited-members:

Additional Objects
------------------

.. attributetable:: discord.Modal
.. autoclass:: discord.Modal
    :members:
    :inherited-members:

.. attributetable:: discord.UnknownComponent
.. autoclass:: discord.UnknownComponent
    :members:
    :inherited-members:

.. attributetable:: discord.UnfurledMediaItem
.. autoclass:: discord.UnfurledMediaItem
    :members:
    :inherited-members:

.. attributetable:: discord.MediaGalleryItem
.. autoclass:: discord.MediaGalleryItem
    :members:
    :inherited-members:

.. attributetable:: discord.ComponentsHolder
.. autoclass:: discord.ComponentsHolder
    :members:
    :inherited-members:

.. attributetable:: discord.DefaultSelectOption
.. autoclass:: discord.DefaultSelectOption
    :members:
    :inherited-members:

ABCs
----
.. attributetable:: discord.Component
.. autoclass:: discord.Component
    :members:

.. attributetable:: discord.InteractionComponent
.. autoclass:: discord.InteractionComponent
    :members:
    :inherited-members:
