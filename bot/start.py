import json
import traceback
from typing import List, Dict

from discord import Embed, Intents
from discord.ext import commands
from discord.ext.commands.errors import ExtensionNotFound
from discord_slash import SlashCommand, SlashContext
from discord_slash.model import (SlashCommandOptionType,
                                 SlashCommandPermissionType)
from discord_slash.utils.manage_commands import (create_option,
                                                 create_permission)

import util


config = util.load_config()


OWNER_ID: int = config['owner_id']
GUILDS: List[int] = config['guild_whitelist']
BOT_TOKEN: str = config['api_keys']['bot_token']
PERMS_OWNER_ONLY = {
    guild_id: [
        create_permission(
            id=OWNER_ID,
            id_type=SlashCommandPermissionType.USER,
            permission=True)
    ]
    for guild_id in GUILDS
}

intents: Intents = Intents.default()
intents.members = True

bot = commands.Bot(intents=intents,
                   command_prefix="surely no one will use this as a command prefix",
                   help_command=None,
                   owner_id=config['owner_id'])
slash = SlashCommand(bot, sync_commands=True)

# store? the config in the bot so cogs can use it
bot.config = config


@bot.event
async def on_ready():
    print("~crunchy time~")


@slash.slash(name="load",
             description="(Re)load any number of extensions.",
             options=[
                 create_option(
                     name="extensions",
                     description="A list of one or more extensions.",
                     option_type=SlashCommandOptionType.STRING,
                     required=False
                 )
             ],
             default_permission=False,
             permissions=PERMS_OWNER_ONLY,
             guild_ids=GUILDS)
async def load(ctx: SlashContext, extensions: str = None):
    reloaded = {'success': [], 'failure': []}
    exceptions = {}
    # if no option is provided, reload every loaded extension
    reloading_all = not extensions
    if reloading_all:
        print("Reloading all.")
    working_set = extensions.split() if not reloading_all else list(bot.extensions.keys())
    # (re)load and collect successes/failures
    for ext in working_set:
        # if we're reloading everything or the extension is already loaded
        if ext in bot.extensions or reloading_all:
            try:
                bot.reload_extension(ext)
                reloaded["success"].append(ext)
            except Exception:
                reloaded["failure"].append(ext)
                exceptions[ext] = traceback.format_exc()
        # otherwise load it
        else:
            try:
                bot.load_extension(ext)
                reloaded["success"].append(ext)
            except ExtensionNotFound:
                reloaded["failure"].append(ext)
                exceptions[ext] = f"{ext} isn't a known extension."
            except Exception:
                reloaded["failure"].append(ext)
                exceptions[ext] = traceback.format_exc()
    # format response
    response = ""
    successes: str = ', '.join(['`' + x + '`' for x in reloaded['success']])
    if len(reloaded['success']) > 0:
        response += f"⚗ (Re)loaded {len(reloaded['success'])} modules ({successes})"
    if len(reloaded['failure']) > 0:
        failures: str = ', '.join(['`' + x + '`' for x in reloaded['failure']])
        response += f"\n💢 Failed to (re)load {len(reloaded['failure'])} modules ({failures}) with these errors:\n"
        for failed_ext_name in reloaded['failure']:
            response += "```" + exceptions[failed_ext_name] + "```"
    await ctx.send(content=response, hidden=True)


@slash.slash(name="info", description="Get pertinent bot info.", guild_ids=GUILDS)
async def info(ctx: SlashContext):
    appinfo = await bot.application_info()
    owner = appinfo.owner
    embed = Embed(
        title="crunch crunch crunch",
        colour=util.CRUNCHY_BLUE,
        description=f"do a crunch box combo and [invite]({util.INVITE_LINK}) me"
    ).set_author(
        name="crunch box combo",
    ).set_thumbnail(
        url=str(appinfo.icon_url)
    ).set_footer(
        text=f"by @{owner.name}#{owner.discriminator}",
        icon_url=str(owner.avatar_url)
    )
    await ctx.send(embed=embed, hidden=True)

# run run run run run
exts = ['ext.stuff', 'ext.annotate', 'ext.automata']

if __name__ == '__main__':
    for ext in exts:
        bot.load_extension(ext)
    bot.run(config['api_keys']['bot_token'])
