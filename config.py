import yaml
from os.path import dirname, join

this_dir = dirname(__file__)

with open(join(this_dir, 'configs/bot.yaml'), 'r') as f:
    BOT_CONFIG = yaml.safe_load(f)

with open(join(this_dir, 'configs/messages.yaml'), 'r') as f:
    BOT_MESSAGES = yaml.safe_load(f)

with open(join(this_dir, 'configs/api_endpoints.yaml'), 'r') as f:
    API_ENDPOINTS = yaml.safe_load(f)

with open(join(this_dir, 'configs/guild.yaml'), 'r') as f:
    GUILD = yaml.safe_load(f)
