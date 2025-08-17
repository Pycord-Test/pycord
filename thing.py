import discord
import logging
import os

from dotenv import load_dotenv
from discord import Button, ButtonStyle, ActionRow, Container

load_dotenv()

logging.basicConfig(level=logging.DEBUG)

bot = discord.Bot(intents=discord.Intents.default())


def build_container(secret_message: str) -> Container:
    return Container(
        ActionRow(
            Button(
                style=ButtonStyle.primary,
                label="Click me! I'll tell you a secret",
                custom_id=f"v1:hello_button_{secret_message}",
                emoji=discord.PartialEmoji(name="🤫"),
            )
        ),
        id=3,
    )


@bot.command()
async def secret(ctx: discord.ApplicationContext, secret_message: str) -> None:
    await ctx.respond(
        components=[build_container(secret_message)],
    )


@bot.component(lambda i: i.startswith("v1:hello_button_"))
async def hello_button(interaction: discord.Interaction) -> None:
    secret_message = interaction.custom_id.split("hello_button_")[1]
    await interaction.respond(
        f"Hello {interaction.user.name}! The secret message is: ||{secret_message}||", ephemeral=True
    )
    message = await interaction.channel.fetch_message(interaction.message.id)
    print(message.components.get_by_id(3))


bot.run(os.getenv("TOKEN_3"))
