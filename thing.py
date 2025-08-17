import discord
import logging
import os

from dotenv import load_dotenv
from discord import *

load_dotenv()

logging.basicConfig(level=logging.INFO)

bot = discord.Bot(intents=discord.Intents.default())


@bot.command()
async def ping(ctx: discord.ApplicationContext) -> None:
    m = await ctx.respond(
        components=[
            Container(
                components=[
                    ActionRow(
                        [Button(style=ButtonStyle.primary, label="Click me!", custom_id=f"hello_button_{ctx.user.id}")]
                    )
                ]
            )
        ],
    )


@bot.listen()
async def on_interaction(interaction: discord.Interaction) -> None:
    if interaction.type == discord.InteractionType.component:
        if interaction.custom_id.startswith("hello_button_"):
            await interaction.response.send_message(f"Hello {interaction.user.name}!", ephemeral=True)


bot.run(os.getenv("TOKEN_3"))
