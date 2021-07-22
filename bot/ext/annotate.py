from typing import Dict, List
from discord.abc import Messageable
from discord.embeds import Embed
from discord.enums import try_enum
from discord.ext import commands
from discord.message import Message
from discord import Guild
import re
import aiohttp

import util

# according to the re module documentation, compiled patterns are cached so we don't need
# to compile this pattern as long as we don't use too many other regexes?

# matches a discord link and captures the guild, channel, and message IDs from it
MESSAGE_LINK_PATTERN = r"http(?:s)?://(?:canary.)?discord.com/channels/(\d+)/(\d+)/(\d+)"
# matches a twitter link and captures the ID from it
TWITTER_LINK_PATTERN = r"http(?:s)://twitter.com/.*/(\d*)"

class Annotate(commands.Cog):
    bearer_token = None
    def __init__(self, bot):
        print(u"📝 Annotate")
        self.bot: commands.Bot = bot
        Annotate.bearer_token = util.CONFIG['api_keys']['twitter_bearer']

    @commands.Cog.listener()
    async def on_message(self, msg: Message):
        await self._post_linked_msg(msg)
        await self._annotate_tweet(msg)

    async def _post_linked_msg(self, msg: Message):
        """Scans a message for Discord message links and posts the linked messages' contents.

        Args:
            msg (Message): The message to scan.
        """
        this_guild: Guild = msg.guild
        matches = re.findall(MESSAGE_LINK_PATTERN, msg.content, re.IGNORECASE)
        embeds = []
        # collates all referenced messages, but only sends the first... for now
        for match in matches:
            # the match object will have the 3 captured IDs as strings
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

    async def _annotate_tweet(self, msg: Message):
        """Scans a message for a tweet and performs some annotation on it.

        Args:
            msg (Message): The message to scan.
        """
        matches = re.findall(TWITTER_LINK_PATTERN, msg.content, re.IGNORECASE)
        # matches will have the captured tweet ID from the link
        for match in matches:
            tweet_id = match
            
            # make a request to the twitter API to get some data
            headers = {"Authorization" : f"Bearer {Annotate.bearer_token}"}
            params = {
                "ids": tweet_id,
                "tweet.fields": "attachments,referenced_tweets",
                "expansions": "attachments.media_keys,referenced_tweets.id.author_id",
                "media.fields": "type"
            }
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.twitter.com/2/tweets', params=params, headers=headers) as response:
                    tweet_data = await response.json()
            # expand quoted tweet - fetches the link for a quoted tweet and posts it
            try:
                last_token: str = msg.content.split()[-1]
                if last_token != "~noexpand":
                    # get quoted id
                    referenced_tweets: List[Dict[str, str]] = tweet_data['data'][0]['referenced_tweets']
                    for tweet in referenced_tweets:
                        if tweet['type'] == 'quoted':
                            quoted_id = tweet['id']
                    referenced_users: List[Dict[str, str]] = tweet_data['includes']['users']
                    # get the quoted's author's id
                    included_tweets: List[Dict[str, str]] = tweet_data['includes']['tweets']
                    for tweet in included_tweets:
                        if tweet['id'] == quoted_id:
                            author_id = tweet['author_id']
                    # get the author's username
                    for user in referenced_users:
                        if user['id'] == author_id:
                            author_name = user['username']
                    await msg.channel.send(content=f"*Quoted tweet*: https://twitter.com/{author_name}/status/{quoted_id}")
            except KeyError:
                pass
            # annotate media - reacts to a tweet link with the number of images / whether it's a video
            try:
                tweet_media: List[Dict[str, str]] = tweet_data['includes']['media']
                media_count = len(tweet_media)
                if media_count > 1:
                    await msg.add_reaction(["0️⃣","1️⃣","2️⃣","3️⃣","4️⃣"][media_count])
                if tweet_media[0]['type'] == 'video':
                    await msg.add_reaction("⏯")
            except KeyError:
                pass
        



def setup(bot: commands.Bot):
    bot.add_cog(Annotate(bot))
