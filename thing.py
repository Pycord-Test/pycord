import discord
import logging
import os

from dotenv import load_dotenv
from discord import *
load_dotenv()

logging.basicConfig(level=logging.INFO)

bot = discord.Bot(intents=discord.Intents.default())


@bot.command()
async def ping(ctx: discord.ApplicationContex) -> None:
    m = await ctx.respond(
        "slurp",
        components=[
            Container(components=[Button(style=ButtonStyle.primary, label="Click me!", custom_id=f"hello_button_{ctx.user.id}")])
        ],
    )
