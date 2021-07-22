import sys
import util
from discord import Intents
from discord.ext import commands
from discord.ext.commands.errors import ExtensionFailed, ExtensionNotFound
from discord_slash import SlashCommand

sys.stdout.reconfigure(encoding='utf-8')

intents: Intents = Intents.default()
intents.members = True

bot = commands.Bot(intents=intents,
                   command_prefix="surely no one will use this as a command prefix",
                   help_command=None,
                   owner_id=util.OWNER_ID)
slash = SlashCommand(bot, sync_commands=True)


@bot.event
async def on_ready():
    print("~crunchy🌮time~")

# run run run run run
exts = ['core', 'ext.stuff', 'ext.annotate', 'ext.automata']

if __name__ == '__main__':
    for ext in exts:
        try:
            bot.load_extension(ext)
        except (ExtensionFailed, ExtensionNotFound):
            print(f"Extension {ext} failed to load.")
    bot.run(util.BOT_TOKEN)
