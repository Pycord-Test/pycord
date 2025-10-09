import pytest

import discord


@pytest.mark.asyncio
async def test_bot_login_failure_login():
    bot = discord.Bot()

    with pytest.raises(discord.LoginFailure):
        await bot.login("invalid_token")


@pytest.mark.asyncio
async def test_bot_login_failure_start():
    bot = discord.Bot()

    with pytest.raises(discord.LoginFailure):
        await bot.start("invalid_token")


def test_bot_login_failure_run():
    bot = discord.Bot()

    with pytest.raises(discord.LoginFailure):
        bot.run("invalid_token")
