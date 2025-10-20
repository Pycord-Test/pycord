## Pycord Next ?

These changes are part of `Pycord-Development/pycord-next`, and are candidates for an upcoming major
release.

### Added

- `ModalInteraction` provided to modal listeners during modal submit interactions
- `ComponentInteraction` provided to component listeners during component interactions
- `discord.components` module and its items

### Fixed

### Changed

- Removed the custom `enums.Enum` implementation in favor of a stdlib `enum.Enum` subclass.
- `InputText` use `TextInput` instead
- `ComponentType.input_text` use `ComponentType.text_input` instead
- `InputTextStyle` use `TextInputStyle` instead
- `TextInputStyle.singleline` use `TextInputStyle.short` instead
- `TextInputStyle.multiline` and `TextInputStyle.long` use `TextInputStyle.paragraph` instead
- `ComponentType.select` use `ComponentType.string_select` instead

### Deprecated

### Removed

- `Interaction.original_message` use `Interaction.original_response` instead
- `Interaction.edit_original_message` use `Interaction.edit_original_response` instead
- `Interaction.delete_original_message` use `Interaction.delete_original_response`
  instead
- `Interaction.premium_required` use a `Button` with type `ButtonType.premium` instead
- `Interaction.cached_channel` use `Interaction.channel` instead
- `Message.interaction` use `Message.interaction_metadata` instead
- `MessageInteraction` see `InteractionMetadata` instead

#### `discord.utils`

- `utils.filter_params`
- `utils.sleep_until` use `asyncio.sleep` combined with `datetime.datetime` instead
- `utils.compute_timedelta` use the `datetime` module instead
- `utils.resolve_invite`
- `utils.resolve_template`
- `utils.parse_time` use `datetime.datetime.fromisoformat` instead
- `utils.time_snowflake` use `utils.generate_snowflake` instead
- `utils.warn_deprecated`
- `utils.deprecated`
- `utils.get` use `utils.find` with `lambda i: i.attr == val` instead
- `AsyncIterator.get` use `AsyncIterator.find` with `lambda i: i.attr == val` instead
- `utils.as_chunks` use `itertools.batched` on Python 3.12+ or your own implementation
  instead

#### `discord.ui`

Removed everything under `discord.ui`. Instead, use the new `discord.components` module
which provides a more flexible and powerful way to create interactive components. You
can read more in the migration guide.

<!-- TODO: Add link to migration guide -->

#### `discord.ext.pages`

Removed the `discord.ext.pages` module. Instead, use the new `discord.components` module
with your own pagination logic.

