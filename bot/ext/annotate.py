
from os import name
from discord.abc import Messageable
from discord.embeds import Embed
from discord.ext import commands
from discord.message import Message
from discord import Guild
import re

# according to the re module documentation, compiled patterns are cached so we don't need
# to compile this as long as we don't use too many other regexes

# matches a discord link and captures the guild, channel, and message IDs from it
MESSAGE_LINK_PATTERN = r"http(?:s)?://(?:canary.)?discord.com/channels/(\d+)/(\d+)/(\d+)"


class Annotate(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.Cog.listener()
    async def on_message(self, msg: Message):
        this_guild: Guild = msg.guild
        matches = re.findall(MESSAGE_LINK_PATTERN, msg.content, re.IGNORECASE)
        embeds = []
        # collates all referenced messages, but only sends the first... for now
        for match in matches:
            guild_id, channel_id, message_id = tuple(map(int, match))
            # only fetch messages through links in the same guild, for basic privacy
            if guild_id == this_guild.id:
                channel: Messageable = await self.bot.fetch_channel(channel_id)
                message: Message = await channel.fetch_message(message_id)
                if len(message.content) > 0:
                    embed = Embed(
                        description=message.content
                    ).set_author(
                        name=message.author.name,
                        url=message.jump_url,
                        icon_url=message.author.avatar_url
                    ).add_field(
                        name="🔗",
                        value=f"[original post]({message.jump_url})"
                    )
                    embeds.append(embed)
        if len(embeds) > 0:
            await msg.channel.send(embed=embeds[0])


def setup(bot: commands.Bot):
    bot.add_cog(Annotate(bot))