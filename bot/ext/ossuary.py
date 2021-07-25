from discord.ext import commands
import util

OSSUARY_LINK = util.OSSUARY_LINK

class Ossuary(commands.Cog):
    key = util.CONFIG['api_keys']['self']

    def __init__(self, bot):
        print("💀 Ossuary")
        self.bot = bot

def setup(bot: commands.Bot):
    bot.add_cog(Ossuary(bot))