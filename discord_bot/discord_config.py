import os

print(os.environ)

# Production Server Config
CLIENT_ID = os.environ.get('DISCORD_CLIENT_ID')
CLIENT_SECRET = os.environ.get('DISCORD_CLIENT_SECRET')
TOKEN = os.environ.get('DISCORD_TOKEN')

SUCCESS_COLOR = 0x00ff00
INFO_COLOR = 0x00cbff
HELP_COLOR = 0xffe900
ERROR_COLOR = 0xff0000
