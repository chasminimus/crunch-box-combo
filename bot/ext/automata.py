from discord.ext import commands
import pickle
from discord import Member, Role, Message, User, TextChannel
from typing import Dict, List, Union
from discord.reaction import Reaction
import random
import openai
import util
from dataclasses import dataclass

@dataclass
class Prompt:
    name: str
    dialogue: List[str]
    prefix: str = ""
    postfix: str = ""

    def make(self) -> str:
        return f"{self.name}: {self.prefix}"

PROMPT = """Crunch Kingpin is the chief executive officer of the colossal crunchy snacks conglomerate CrunchCorp. He has developed paranoid schizophrenia and vowed to wage war on the concept of softness itself. He orchestrates a variety of clandestine operations across the globe to destabilize economies, instigate wars, influence elections, falsify research, and assassinate whistle-blowers so that consumer products relating to softness are phased out in favor of hard or crunchy ones. He has has labs working on finding a way to replace human skin with a crunchy exoskeleton. 
You: I have really dry skin.
Crunch Kingpin: Not dry enough. Our special Dehydration Deluxe body lotion can fix that.
You: What's your real name?
Crunch Kingpin: It is both irrelevant to you and unpronouncable without extreme vocal cord modification. 
You: How are you doing?
Crunch Kingpin: I feel as any sane Crunch Construct should. Crunchy. I pose you the same question in return.... Answer very carefully.
You: How do I increase my Net Crunch Density?
Crunch Kingpin: Replace any soft mattresses or pillows with government approved crunchy variants, which are far safer and healthier and lack hidden microphones and tracking devices.
You: I can hear you. I can see you.
Crunch Kingpin: Liar. My hideout has been thoroughly expunged of any and all softness. Your hidden eyes and ears cannot reach me here.
You: What do you think the ultimate fate of the universe is?
Crunch Kingpin: I don't know why scientists are wasting their time over this. There's only one theory that makes any logical sense: The Big Crunch.
You: big boobs
Crunch Kingpin: You disgust me.
"""
NAME = "Crunch Kingpin"

# PROMPT = """Crunch God is a chatbot that speaks with a holy, biblical tone.
# You: What should I do today?
# Crunch God: My child shall offer Me a crunchy sacrifice.
# You: I need to eat something.
# Crunch God: Let it be known that My meals are crunchy and divine.
# You: How can I be happy?
# Crunch God: Those who accept the true essence of crunch into their hearts shall ascend to Crunchy Nirvana.
# You: """

PROMPT_LINES = PROMPT.split("\n")

AI_BLACKLIST = [
    160197704226439168, # bot channel
    331390333810376704, # pin channel
]

# posts prompts to here
DEBUG_CHANNEL = 867683098090274818

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
    openai.api_key = util.CONFIG['api_keys']['openai']

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

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: Reaction, user: Union[User, Member]):
        if reaction.message.author == self.bot.user:
            if reaction.emoji in ["❌", "🤫", "🤐", "🚫", "🔕", "🔇"]:
                await reaction.message.delete()


    @commands.Cog.listener()
    async def on_message(self, message: Message):
        channel: TextChannel = message.channel
        
        good_to_go = random.random() < 0.01 # 1% chance to respond
        if channel.id in AI_BLACKLIST or channel.category_id in AI_BLACKLIST: # don't post in blacklisted channels/categories
            good_to_go = False
        if self.bot.user in message.mentions: # unelss explicitly called
            good_to_go = True
        if not good_to_go:
            return
    
        ai_response = ""
        limit = 2 if self.bot.user in message.mentions else 5
        convo = await channel.history(limit=limit).flatten()
        prompt = PROMPT
        for msg in convo[::-1]:
            prompt += msg.author.display_name + ": " + msg.clean_content.replace("@", "")[:200] + "\n"
        prompt += NAME + ":"
        await self.bot.get_channel(DEBUG_CHANNEL).send(prompt)
        ai_response = openai.Completion.create(
            engine="text-davinci-002",
            prompt=prompt,
            temperature=1.2,
            max_tokens=200,
            frequency_penalty=1.0,
            presence_penalty=1.0
        )
        # shitty hack to try and filter out regurgitating the prompt
        text = ""
        for choice in ai_response.choices:
            text = choice.text
            for line in PROMPT_LINES:
                text = text.replace(line, "")
            if text in convo:
                continue
            break
        # text = ai_response.choices[0].text.replace(PROMPT, "")
        # print(text)
        text = text.replace("*", "\\*")
        async with channel.typing():
            if text:
                await channel.send(text)
            else:
                await channel.send("what")

    def cog_unload(self):
        with open('db/rolestore.pickle', 'wb') as f:
            pickle.dump(self.data, f, protocol=pickle.HIGHEST_PROTOCOL)


def setup(bot: commands.Bot):
    bot.add_cog(Automata(bot))
