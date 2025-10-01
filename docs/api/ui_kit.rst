.. _discord_ui_kit:

Bot UI Kit
==========

The library implements a UI Kit that allows you to create interactive components for your Discord applications.

API Models
-----------

.. attributetable:: discord.components.ActionRow

.. autoclass:: discord.components.ActionRow
    :members:
    :inherited-members:

.. attributetable:: discord.components.Button

.. autoclass:: discord.components.Button
    :members:
    :inherited-members:

.. attributetable:: discord.components.StringSelect

.. autoclass:: discord.components.StringSelect
    :members:
    :inherited-members:

.. attributetable:: discord.components.TextInput

.. autoclass:: discord.components.TextInput
    :members:
    :inherited-members:

.. attributetable:: discord.components.UserSelect

.. autoclass:: discord.components.UserSelect
    :members:
    :inherited-members:

.. attributetable:: discord.components.RoleSelect

.. autoclass:: discord.components.RoleSelect
    :members:
    :inherited-members:

.. attributetable:: discord.components.MentionableSelect

.. autoclass:: discord.components.MentionableSelect
    :members:
    :inherited-members:

.. attributetable:: discord.components.ChannelSelect

.. autoclass:: discord.components.ChannelSelect
    :members:
    :inherited-members:

.. attributetable:: discord.components.Section

.. autoclass:: discord.components.Section
    :members:
    :inherited-members:

.. attributetable:: discord.components.TextDisplay

.. autoclass:: discord.components.TextDisplay
    :members:
    :inherited-members:

.. attributetable:: discord.components.Thumbnail

.. autoclass:: discord.components.Thumbnail
    :members:
    :inherited-members:

.. attributetable:: discord.components.MediaGallery

.. autoclass:: discord.components.MediaGallery
    :members:
    :inherited-members:

.. attributetable:: discord.components.FileComponent

.. autoclass:: discord.components.FileComponent
    :members:
    :inherited-members:

.. attributetable:: discord.components.Separator
.. autoclass:: discord.components.Separator
    :members:
    :inherited-members:

.. attributetable:: discord.components.Container
.. autoclass:: discord.components.Container
    :members:
    :inherited-members:

.. attributetable:: discord.components.Label
.. autoclass:: discord.components.Label
    :members:
    :inherited-members:

Interaction Components
-----------
These objects are dataclasses that represent components as they are recieved from Discord in interaction payloads, currently applicable only with :class:`discord.components.Interaction` of type :data:`discord.components.InteractionType.modal_submit`.

.. attributetable:: discord.components.PartialLabel
.. autoclass:: discord.components.PartialLabel
    :members:
    :inherited-members:

.. attributetable:: discord.components.PartialStringSelect
.. autoclass:: discord.components.PartialStringSelect
    :members:
    :inherited-members:

.. attributetable:: discord.components.PartialUserSelect
.. autoclass:: discord.components.PartialUserSelect
    :members:
    :inherited-members:

.. attributetable:: discord.components.PartialRoleSelect
.. autoclass:: discord.components.PartialRoleSelect
    :members:
    :inherited-members:

.. attributetable:: discord.components.PartialMentionableSelect
.. autoclass:: discord.components.PartialMentionableSelect
    :members:
    :inherited-members:

.. attributetable:: discord.components.PartialChannelSelect
.. autoclass:: discord.components.PartialChannelSelect
    :members:
    :inherited-members:

.. attributetable:: discord.components.PartialTextInput
.. autoclass:: discord.components.PartialTextInput
    :members:
    :inherited-members:

.. attributetable:: discord.components.PartialTextDisplay
.. autoclass:: discord.components.PartialTextDisplay
    :members:
    :inherited-members:

Additional Objects
------------------

.. attributetable:: discord.components.Modal
.. autoclass:: discord.components.Modal
    :members:
    :inherited-members:

.. attributetable:: discord.components.UnknownComponent
.. autoclass:: discord.components.UnknownComponent
    :members:
    :inherited-members:

.. attributetable:: discord.components.UnfurledMediaItem
.. autoclass:: discord.components.UnfurledMediaItem
    :members:
    :inherited-members:

.. attributetable:: discord.components.MediaGalleryItem
.. autoclass:: discord.components.MediaGalleryItem
    :members:
    :inherited-members:

.. attributetable:: discord.components.ComponentsHolder
.. autoclass:: discord.components.ComponentsHolder
    :members:
    :inherited-members:

.. attributetable:: discord.components.DefaultSelectOption
.. autoclass:: discord.components.DefaultSelectOption
    :members:
    :inherited-members:

ABCs
----
.. attributetable:: discord.components.Component
.. autoclass:: discord.components.Component
    :members:

.. attributetable:: discord.components.PartialComponent
.. autoclass:: discord.components.PartialComponent
    :members:
    :inherited-members:
