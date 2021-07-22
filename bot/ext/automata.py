from discord.ext import commands
import pickle
from discord import Guild, Member, Role
from typing import Dict, List
from discord_slash import cog_ext

from discord_slash.context import SlashContext

class Automata(commands.Cog):
    """
    Automatic server tasks.

    ### Rolestore
    
    Restores roles for rejoining users by storing them.
    The structure is a nested dictionary:
    - data {
        - guild (int): {
            - blacklist (str):
                - [userid (int)]
            - userid (int):
                - [roleid (int)]
            - userid etc.:
                - [etc.]
        - }
        - guild {etc.}
    - }
    """

    def __init__(self, bot: commands.Bot):
        print("🤖 Automata")
        self.bot = bot
        self.data: Dict = {}
        try:
            with open('db/rolestore.pickle', 'rb') as f:
                self.data = pickle.load(f)
        except (OSError, EOFError):
            print("Couldn't open rolestore pickle, or it was empty.")

    async def _rolestore_restore(self, member: Member):
        """Restores a recently joined member's roles if saved.

        Args:
            member (Member): The member that joined.
        """        
        guildid: int = member.guild.id
        guilddata = self.data.get(guildid)
        if guilddata == None:
            print(f"No rolestore data for guild {guildid}!")
            return
        blacklist: List[int] = guilddata.get('blacklist', [])
        if member.id not in blacklist:
            roleids = guilddata.get(member.id, [])
            roles: List[Role] = []
            for roleid in roleids:
                role: Role = member.guild.get_role(roleid)
                # skip @everyone
                if role.is_default():
                    continue
                roles.append(role)
            # print(f"Restoring roles {''.join([role.name for role in roles])} for {member.display_name} in {member.guild.name}")
            await member.add_roles(*roles, reason="💾 Rolestore restore.")
                

    async def _rolestore_capture(self, member: Member):
        """Saves a member's roles when they exit the server.

        Args:
            member (Member): The member who left.
        """        
        guildid: int = member.guild.id
        roleids = [role.id for role in member.roles]
        try: 
            self.data[guildid].update({member.id: roleids})
        except KeyError:
            self.data[guildid] = {member.id: roleids}

        # print(f"Captured roles {''.join([role.name for role in member.roles])} for {member.display_name} in {member.guild.name}")

    @commands.Cog.listener()
    async def on_member_join(self, member: Member):
        await self._rolestore_restore(member)

    @commands.Cog.listener()
    async def on_member_remove(self, member: Member):
        await self._rolestore_capture(member)

    def cog_unload(self):
        with open('db/rolestore.pickle', 'wb') as f:
            pickle.dump(self.data, f, protocol=pickle.HIGHEST_PROTOCOL)


def setup(bot: commands.Bot):
    bot.add_cog(Automata(bot))
