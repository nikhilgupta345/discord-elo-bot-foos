import traceback

import discord

from discord_config import (
    HELP_COLOR,
    TOKEN
)
import handlers

client = discord.Client()


@client.event
async def on_ready():
    print("Logged in as")
    print(client.user.name)
    print(client.user.id)
    print("------")


async def help_me(message):
    help_msg = "\t\n".join(sorted(handler_map.keys()))
    embed = discord.Embed(
        title="Accepted commands",
        description=help_msg,
        color=HELP_COLOR)
    await message.channel.send(embed=embed)

handler_map = {
    '!help': help_me,
    '!createuser': handlers.create_user,
    '!elo': handlers.get_stats,
    '!stats': handlers.get_stats,
    '!team': handlers.get_team,
    '!top': handlers.top,
    '!bottom': handlers.bottom,
    '!leaderboard': handlers.top,
    '!dreamteam': handlers.dream_teams,
    '!report': handlers.record_match,
    '!record': handlers.record_match,
    '!undo': handlers.delete_latest_match
}


@client.event
async def on_message(message):
    try:
        for keyword, handler in handler_map.items():
            if message.content.lower().startswith(keyword):
                message.content = message.content.lower()
                await handler(message)
                break
    except Exception as e:
        traceback.print_exc()
        await message.channel.send(f'Exception occurred: {str(e)[:1950]}')

client.run(TOKEN)
