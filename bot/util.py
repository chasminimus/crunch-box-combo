import json
from typing import Dict

def load_config() -> Dict:
    with open("config.json") as config_file:
        config = json.load(config_file)
    return config

CRUNCHY_RED = 0xE3265A
CRUNCHY_BLUE = 0x28A9AB
INVITE_LINK = r"https://discord.com/api/oauth2/authorize?client_id=820865262526005258&permissions=4294307568&scope=applications.commands%20bot"
