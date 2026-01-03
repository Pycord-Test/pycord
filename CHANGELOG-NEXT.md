## Pycord Next ?

These changes are part of `Pycord-Development/pycord-next`, and are candidates for an upcoming major
release.

### Added

- `discord.DiscordTime`, a `datetime.datetime` subclass that offers additional 
  functionality for snowflakes as well as util methods.

### Fixed

### Changed

- Removed the custom `enums.Enum` implementation in favor of a stdlib `enum.Enum` subclass.

### Deprecated

### Removed

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
- `utils.generate_snowflake`, moved to `discord.datetime.DiscordTime.generate_snowflake`
- `utils.utcnow`, moved to `discord.datetime.DiscordTime.utcnow`
- `utils.snowflake_time`, moved to `DiscordTime.from_snowflake`
- `utils.format_dt`, moved to `DiscordTime.format`
