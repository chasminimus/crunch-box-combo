from discord.ext import commands
from discord_slash import cog_ext, SlashCommandOptionType, SlashContext
from discord_slash.utils.manage_commands import create_option
import util
import traceback
from discord import Embed
from discord.ext.commands.errors import ExtensionNotFound

class Core(commands.Cog):
    def __init__(self, bot: commands.Bot):
        print("💖 Core")
        self.bot = bot

    @cog_ext.cog_slash(name="load",
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
                permissions=util.PERMS_OWNER_ONLY,
                guild_ids=util.GUILDS)
    async def load(self, ctx: SlashContext, extensions: str = None):
        reloaded = {'success': [], 'failure': []}
        exceptions = {}
        # if no option is provided, reload every loaded extension
        reloading_all = not extensions
        if reloading_all:
            print("Reloading all.")
        working_set = extensions.split() if not reloading_all else list(self.bot.extensions.keys())
        # (re)load and collect successes/failures
        for ext in working_set:
            # if we're reloading everything or the extension is already loaded
            if ext in self.bot.extensions or reloading_all:
                try:
                    self.bot.reload_extension(ext)
                    reloaded["success"].append(ext)
                except Exception as e:
                    reloaded["failure"].append(ext)
                    # exceptions[ext] = str(e)
                    exceptions[ext] = traceback.format_exc(chain=False)
            # otherwise load it
            else:
                try:
                    self.bot.load_extension(ext)
                    reloaded["success"].append(ext)
                except ExtensionNotFound:
                    reloaded["failure"].append(ext)
                    exceptions[ext] = f"{ext} isn't a known extension."
                except Exception as e:
                    reloaded["failure"].append(ext)
                    # exceptions[ext] = str(e)
                    exceptions[ext] = traceback.format_exc(chain=False)
        # format response
        response = ""
        # collect successes
        successes: str = ', '.join(['`' + x + '`' for x in reloaded['success']])
        if len(reloaded['success']) > 0:
            response += f"⚗ (Re)loaded {len(reloaded['success'])} modules ({successes})"
        # collect errors
        exception_text = []
        if len(reloaded['failure']) > 0:
            failures: str = ', '.join(['`' + x + '`' for x in reloaded['failure']])
            response += f"\n💢 Failed to (re)load {len(reloaded['failure'])} modules ({failures})"
            for failed_ext_name in reloaded['failure']:
                exception_text.append("```" + exceptions[failed_ext_name] + "```")
            # fit as many exceptions into one message as possible
            while exception_text and len(response) <= 2000:
                if len(response + exception_text[0]) <= 2000:
                    response += exception_text.pop(0)
                else:
                    # hit character limit, post
                    await ctx.send(content=response, hidden=True)
                    response = ""
                    break
        if response:
            await ctx.send(content=response, hidden=True)

    @cog_ext.cog_slash(name="info", description="Get pertinent bot info.", guild_ids=util.GUILDS)
    async def info(self, ctx: SlashContext):
        appinfo = await self.bot.application_info()
        owner = appinfo.owner
        embed = Embed(
            title="crunch crunch crunch",
            colour=util.CRUNCHY_BLUE,
            description=f"""do a crunch box combo and [invite]({util.INVITE_LINK}) me"""
        ).set_author(
            name="crunch box combo",
        ).set_thumbnail(
            url=str(appinfo.icon_url)
        ).set_footer(
            text=f"by @{owner.name}#{owner.discriminator}",
            icon_url=str(owner.avatar_url)
        ).add_field(
            name="shut up",
            value="react with any of ❌🤫🤐🚫🔕🔇 to delete one of my messages, append a ~noexpand to your message to inhibit automatic posting"
        )
        await ctx.send(embed=embed, hidden=True)

def setup(bot: commands.Bot):
    bot.add_cog(Core(bot))