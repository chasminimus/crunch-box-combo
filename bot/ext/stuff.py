from discord_slash.model import SlashCommandOptionType
from discord_slash.utils.manage_commands import create_option
import aiohttp
import pickle
from discord import Embed
from discord.ext import commands
from discord_slash import cog_ext, SlashContext


class LastFm(commands.Cog):
    key = None
    def __init__(self, bot):
        self.bot = bot
        LastFm.key = bot.config['api_keys']['lastfm']
        try:
            with open('db/lastfm.pickle', 'rb') as f:
                self.data = pickle.load(f)
        except (OSError, EOFError):
            print("Couldn't open lastfm pickle, or it was empty.")
            self.data = {}

    @cog_ext.cog_subcommand(base="lastfm", name="link",
                            description="Link your last.fm account.", options=[
                                create_option(
                                    name="username",
                                    description="Your last.fm username.",
                                    option_type=SlashCommandOptionType.STRING,
                                    required=True
                                )
                            ])
    async def lastfm_link(self, ctx: SlashContext, username: str):
        # make a request to lastfm's API to see if the user really exists
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://ws.audioscrobbler.com/2.0/?method=user.getinfo&user={username}&api_key={LastFm.key}&format=json") as response:
                userdata = await response.json()
        try:
            name, url, img = userdata['user']['name'], userdata['user']['url'], userdata['user']['image'][0]['#text']
            embed = Embed(title=name, url=url).set_thumbnail(url=img)
            # successful request, note their linked username and some other things
            self.data[ctx.author_id] = (username, url, img)
            await ctx.send(content=f"Linked last.fm account.", embed=embed, hidden=True)
        except KeyError:
            await ctx.send(content="💢 Couldn't find that last.fm account.", hidden=True)

    @cog_ext.cog_subcommand(base="lastfm", name="now",
                            description="Share your now-playing (or last played) on last.fm.")
    async def lastfm_now(self, ctx: SlashContext):
        try:
            (username, url, img) = self.data[ctx.author_id]
            # make a request to lastfm for the playback info
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user={username}&api_key={LastFm.key}&extended=1&limit=1&format=json") as response:
                    userdata = await response.json()

            # set defaults
            track_name = "*(unknown track)*"
            artist_name = "*(unknown artist)*"
            album_name = "*(unknown album)*"
            # try to update them with the response data
            try:
                track_info = userdata['recenttracks']['track'][0]
                track_name = track_info['name']
                artist_name = track_info['artist']['name']
                album_name = track_info['album']['#text']
            except KeyError:
                await ctx.send(content="💢 Something went wrong with last.fm's reponse.", hidden=True)
            # fix any empty results
            track_name = track_name if len(track_name) > 0 else "*(unknown track)*"
            artist_name = artist_name if len(artist_name) > 0 else "*(unknown artist)*"
            album_name = album_name if len(album_name) > 0 else "*(unknown album)*"
            # check if the user is listening now
            now_playing = "@attr" in track_info.keys()
            title = f"🎶 Now playing for {username}" if now_playing else f"🎶 Last played for {username}"
            # build embed
            embed = Embed(
                title=title,
                url=track_info['url']
            ).set_thumbnail(
                url=track_info['image'][1]['#text']
            ).set_author(
                name=username,
                url=url,
                icon_url=img
            ).add_field(
                name="Track",
                value=track_name,
                inline=True
            ).add_field(
                name="Artist",
                value=artist_name,
                inline=True
            ).add_field(
                name="Album",
                value=album_name,
                inline=True
            )
            await ctx.send(embed=embed)
        except KeyError:
            await ctx.send(content="💢 Your last.fm isn't linked.", hidden=True)

    def cog_unload(self):
        # save data to disk
        with open('db/lastfm.pickle', 'wb') as f:
            pickle.dump(self.data, f, protocol=pickle.HIGHEST_PROTOCOL)


def setup(bot: commands.Bot):
    bot.add_cog(LastFm(bot))
