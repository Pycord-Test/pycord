import os

from dotenv import load_dotenv

import discord
from discord import BaseInteraction, components

load_dotenv()

MAZE = True  # 👀


bot = discord.Bot(
    default_command_integration_types={discord.IntegrationType.user_install, discord.IntegrationType.guild_install},
    default_command_contexts={
        discord.InteractionContextType.guild,
        discord.InteractionContextType.bot_dm,
        discord.InteractionContextType.private_channel,
    },
)


def create_modal(user: discord.User | discord.Member) -> components.Modal:
    modal = components.Modal(
        components.TextDisplay(
            f"""Input below your announcement's title, description, and user to mention in the announcement{", as well as attached images" if MAZE else ""}."""
        ),
        components.Label(
            components.TextInput(
                style=discord.TextInputStyle.short,
                placeholder="Launching py-cord next !",
                custom_id="v1:announcement_title",
                required=True,
            ),
            label="Announcement Title",
            description="The title of your announcement",
        ),
        components.Label(
            components.TextInput(
                style=discord.TextInputStyle.paragraph,
                placeholder="Today is the day we launch py-cord next !\nyada yada\n...",
                custom_id="v1:announcement_content",
                required=True,
            ),
            label="Announcement Content",
            description="The content of your announcement. Supports Markdown.",
        ),
        components.Label(
            components.MentionableSelect(
                default_values=[components.DefaultSelectOption(id=user.id, type="user")],
                custom_id="v1:announcement_mentions",
                min_values=0,
                max_values=4,
                required=False,
            ),
            label="Mentioned Users and Roles",
            description="The users and roles to mention in your announcement (if any)",
        ),
        title="Create an Announcement",
        custom_id="v1:announcement_modal",
    )
    if MAZE:
        modal.components.append(
            components.Label(
                components.FileUpload(min_values=0, max_values=5, required=False, custom_id="v1:announcement_images"),
                label="Images to attach",
                description="Attach up to 5 images to your announcement. Supports PNG only.",
            )
        )
    return modal


@bot.slash_command()
async def create_announcement(ctx: discord.ApplicationContext):
    await ctx.send_modal(create_modal(ctx.author))


def create_announcement(
    title: str, content: str, mentions: list[discord.User | discord.Role], attachments: list[discord.Attachment]
) -> components.Container:
    container = components.Container(
        components.TextDisplay(f"# {title}"),
    )
    if mentions:
        container.components.append(components.TextDisplay(" ".join(m.mention for m in mentions)))
    container.components.append(components.TextDisplay(content))
    if attachments:
        container.components.append(
            components.MediaGallery(
                *(
                    components.MediaGalleryItem(
                        url=attachment.url,
                    )
                    for attachment in attachments
                )
            )
        )

    return container


@bot.modal_listener("v1:announcement_modal")
async def announcement_modal_listener(
    interaction: discord.ModalInteraction[
        components.PartialTextDisplay,
        components.PartialLabel[components.PartialTextInput],
        components.PartialLabel[components.PartialTextInput],
        components.PartialLabel[components.PartialMentionableSelect],
        components.PartialLabel[components.PartialFileUpload],
    ],
):
    assert interaction.channel is not None, "Channel is None"
    assert isinstance(interaction.channel, discord.abc.Messageable), "Channel is not a messageable channel"
    title = interaction.components[1].component.value.strip()
    content = interaction.components[2].component.value.strip()

    mentions: list[discord.User | discord.Role] = []

    for m_id in interaction.components[3].component.values:
        mentions.append(interaction.roles.get(int(m_id)) or interaction.users[int(m_id)])

    if MAZE:
        attachments: list[discord.Attachment] = [
            interaction.attachments[att_id] for att_id in interaction.components[4].component.values
        ]
    else:
        attachments = []

    container = create_announcement(title, content, mentions, attachments)
    try:
        await interaction.channel.send(components=[container])
    except discord.Forbidden:
        await interaction.respond(components=[container])


bot.run(os.getenv("TOKEN_2"))
