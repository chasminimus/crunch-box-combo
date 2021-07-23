from bot.ext.ossuary import OSSUARY_LINK
import json
from typing import Dict, List
from discord_slash.model import SlashCommandPermissionType
from discord_slash.utils.manage_commands import create_permission

def load_config() -> Dict:
    with open("config.json") as config_file:
        config = json.load(config_file)
    return config

# config util
CONFIG = load_config()
OWNER_ID: int = CONFIG['owner_id']
GUILDS: List[int] = CONFIG['guild_whitelist']
BOT_TOKEN: str = CONFIG['api_keys']['bot_token']
PERMS_OWNER_ONLY = {
    guild_id: [
        create_permission(
            id=OWNER_ID,
            id_type=SlashCommandPermissionType.USER,
            permission=True)
    ]
    for guild_id in GUILDS
}

CRUNCHY_RED = 0xE3265A
CRUNCHY_BLUE = 0x28A9AB
INVITE_LINK = r"https://discord.com/api/oauth2/authorize?client_id=820865262526005258&permissions=4294307568&scope=applications.commands%20bot"
OSSUARY_LINK = "localhost:5000"