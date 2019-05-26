import api
import discord

from discord_config import (
    ERROR_COLOR,
    HELP_COLOR,
    INFO_COLOR,
    SUCCESS_COLOR
)


async def create_user(message):
    try:
        _, username = message.content.split(' ')
        if username == 'help':
            raise ValueError
    except ValueError:
        embed = discord.Embed(
            title='Usage',
            description='!createuser <username>',
            color=HELP_COLOR)
        await message.channel.send(embed=embed)
        return

    if not username or not username.isalpha():
        embed = discord.Embed(
            title='Error',
            description='Username must be alphabetic',
            color=ERROR_COLOR)
        await message.channel.send(embed=embed)
        return

    resp = await api.create_player(username)
    if not resp['success']:
        embed = discord.Embed(
            title=f'Unable to create user',
            description=resp['error'][:500],
            color=ERROR_COLOR)
        await message.channel.send(embed=embed)
        return

    data = resp['data']
    embed = discord.Embed(
        title='Success',
        description=f'Created user {data["username"]} with elo {data["elo"]}',
        color=SUCCESS_COLOR
    )
    await message.channel.send(embed=embed)


async def get_stats(message):
    try:
        _, username = message.content.split(' ')
        if username == 'help':
            raise ValueError
    except ValueError:
        embed = discord.Embed(
            title='Usage',
            description='!elo <username>',
            color=HELP_COLOR)
        await message.channel.send(embed=embed)
        return

    if not username or not username.isalpha():
        embed = discord.Embed(
            title='Error',
            description='Username must be alphabetic',
            color=ERROR_COLOR)
        await message.channel.send(embed=embed)
        return

    resp = await api.get_player(username)
    if not resp['success']:
        embed = discord.Embed(
            title=f'Unable to get stats for {username}',
            description=resp['error'][:1500],
            color=ERROR_COLOR)
        await message.channel.send(embed=embed)
        return

    data = resp['data']
    names_and_scores = [
        ('Elo', data['elo']),
        ('Wins', data['wins']),
        ('Losses', data['losses']),
        ('Win Percentage', f'{data["win_percentage"]:0.1f}%'),
        ('Goals Scored', data['goals_scored']),
        ('Goals Allowed', data['goals_allowed']),
    ]

    output = _get_output_from_names_and_scores(names_and_scores)

    embed = discord.Embed(
        title=f'Stats for {username}',
        description=output,
        color=INFO_COLOR
    )
    await message.channel.send(embed=embed)


async def get_team(message):
    try:
        _, player1, player2 = message.content.split(' ')
    except ValueError:
        embed = discord.Embed(
            title='Usage',
            description='!team <player1> <player2>',
            color=HELP_COLOR)
        await message.channel.send(embed=embed)
        return

    if not player1 or not player2 or not player1.isalnum() or not player2.isalnum():
        embed = discord.Embed(
            title='Error',
            description='Usernames must be alphabetic',
            color=ERROR_COLOR)
        await message.channel.send(embed=embed)
        return

    player1 = player1.lower()
    player2 = player2.lower()

    resp = await api.get_team(player1, player2)
    if not resp['success']:
        embed = discord.Embed(
            title='Unable to get stats for team',
            description=resp['error'][:1500],
            color=ERROR_COLOR)
        await message.channel.send(embed=embed)
        return

    data = resp['data']
    names_and_scores = [
        ('Elo', data['elo']),
        ('Wins', data['wins']),
        ('Losses', data['losses']),
        ('Win Percentage', f'{data["win_percentage"]:0.1f}%'),
        ('Goals Scored', data['goals_scored']),
        ('Goals Allowed', data['goals_allowed']),
    ]

    output = _get_output_from_names_and_scores(names_and_scores)

    embed = discord.Embed(
        title=f'Stats for {player1} and {player2}',
        description=output,
        color=INFO_COLOR
    )
    await message.channel.send(embed=embed)


async def top(message):
    is_team = False
    try:
        message_tuple = message.content.split(' ')
        if len(message_tuple) == 3:
            is_team = message_tuple[2].lower() in ('team', 'teams')
        top_num = int(message_tuple[1])
    except Exception:
        embed = discord.Embed(
            title='Usage',
            description='!top <num> [teams]',
            color=HELP_COLOR)
        await message.channel.send(embed=embed)
        top_num = 10

    if is_team:
        await _top_teams(message.channel, top_num)
    else:
        await _top_players(message.channel, top_num)


async def _top_players(channel, num=10):
    resp = await api.get_leaderboards(num)

    if not resp['success']:
        embed = discord.Embed(
            title='Something went wrong',
            description=resp['error'][:1500],
            color=ERROR_COLOR)
        await channel.send(embed=embed)
        return

    players = resp['data']['players']
    if not players:
        embed = discord.Embed(
            title='Error',
            description='No players have played >= 3 games',
            color=ERROR_COLOR)
        await channel.send(embed=embed)
        return

    # Names are of the form "01. username"
    names_and_scores = [
        (f'{i + 1:0>2}. {player["username"]}', player['elo'])
        for i, player in enumerate(players)]
    output = _get_output_from_names_and_scores(names_and_scores)

    embed = discord.Embed(
        title=f'Top {len(names_and_scores)} players',
        description=output,
        color=INFO_COLOR
    )
    await channel.send(embed=embed)


async def _top_teams(channel, num=10):
    resp = await api.get_dream_teams(num)

    if not resp['success']:
        embed = discord.Embed(
            title='Error',
            description=resp['error'][:1500],
            color=ERROR_COLOR)
        await channel.send(embed=embed)
        return

    teams = resp['data']['teams']
    if not teams:
        embed = discord.Embed(
            title='Error',
            description='No teams have played >= 3 games',
            color=ERROR_COLOR)
        await channel.send(embed=embed)
        return

    # Names are of the form "01. a and b"
    team_names_and_scores = [
        (f'{i + 1:0>2}. {" and ".join(sorted(team["players"]))}', team["elo"])
        for i, team in enumerate(teams)]

    output = _get_output_from_names_and_scores(team_names_and_scores)

    embed = discord.Embed(
        title='Dream teams',
        description=output,
        color=INFO_COLOR
    )
    await channel.send(embed=embed)


async def dream_teams(message):
    await _top_teams(message.channel)


async def bottom(message):
    is_team = False
    try:
        message_tuple = message.content.split(' ')
        if len(message_tuple) == 3:
            is_team = message_tuple[2].lower() in ('team', 'teams')
        top_num = int(message_tuple[1])
    except Exception:
        embed = discord.Embed(
            title='Usage',
            description='!bottom <num> [teams]',
            color=HELP_COLOR)
        await message.channel.send(embed=embed)
        top_num = 10

    if is_team:
        await _bottom_teams(message.channel, top_num)
    else:
        await _bottom_players(message.channel, top_num)


async def _bottom_teams(channel, num=10):
    resp = await api.get_nightmare_teams(num)

    if not resp['success']:
        embed = discord.Embed(
            title='Error',
            description=resp['error'][:1500],
            color=ERROR_COLOR)
        await channel.send(embed=embed)
        return

    teams = resp['data']['teams']
    if not teams:
        embed = discord.Embed(
            title='Error',
            description='No teams have played >= 3 games',
            color=ERROR_COLOR)
        await channel.send(embed=embed)
        return

    # Names are of the form "01. a and b"
    team_names_and_scores = [
        (f'{i + 1:0>2}. {" and ".join(sorted(team["players"]))}', team["elo"])
        for i, team in enumerate(teams)]

    output = _get_output_from_names_and_scores(team_names_and_scores)

    embed = discord.Embed(
        title='Nightmare teams',
        description=output,
        color=INFO_COLOR
    )
    await channel.send(embed=embed)


async def _bottom_players(channel, num=10):
    resp = await api.get_loserboards(num)

    if not resp['success']:
        embed = discord.Embed(
            title='Something went wrong',
            description=resp['error'][:1500],
            color=ERROR_COLOR)
        await channel.send(embed=embed)
        return

    players = resp['data']['players']
    if not players:
        embed = discord.Embed(
            title='Error',
            description='No players have played >= 3 games',
            color=ERROR_COLOR)
        await channel.send(embed=embed)
        return

    # Names are of the form "01. username"
    names_and_scores = [
        (f'{i + 1:0>2}. {player["username"]}', player['elo'])
        for i, player in enumerate(players)]
    output = _get_output_from_names_and_scores(names_and_scores)

    embed = discord.Embed(
        title=f'Bottom {len(names_and_scores)} players',
        description=output,
        color=INFO_COLOR
    )
    await channel.send(embed=embed)


async def record_match(message):
    try:
        _, wp1, wp2, lp1, lp2, losing_score = message.content.split(' ')
    except ValueError:
        embed = discord.Embed(
            title='Usage',
            description='!record <winning_player1> <winning_player2> '
                        '<losing_player1> <losing_player2> <losing_score>',
            color=HELP_COLOR)
        await message.channel.send(embed=embed)
        return

    try:
        losing_score = int(losing_score)
    except ValueError:
        embed = discord.Embed(
            title='Error',
            description='Scores must be integers',
            color=ERROR_COLOR)
        await message.channel.send(embed=embed)
        return

    if losing_score >= 5:
        embed = discord.Embed(
            title='Error',
            description='Losing score must be < 5',
            color=ERROR_COLOR)
        await message.channel.send(embed=embed)
        return

    resp = await api.record_match([wp1, wp2], [lp1, lp2], 5, losing_score)
    if not resp['success']:
        embed = discord.Embed(
            title='Error occurred while recording match',
            description=resp['error'][:1500],
            color=ERROR_COLOR)
        await message.channel.send(embed=embed)
        return

    data = resp['data']

    embed = discord.Embed(
        title='Successfully recorded match',
        color=SUCCESS_COLOR
    )

    player_names_and_scores = sorted(data['new_elo']['players'].items(), key=lambda x: x[1], reverse=True)
    player_elos_output = _get_output_from_names_and_scores(player_names_and_scores)

    winning_team = ' and '.join(sorted([wp1, wp2]))
    losing_team = ' and '.join(sorted([lp1, lp2]))

    team_names_and_scores = [
        (winning_team, data["new_elo"]["teams"]["winning_team"]),
        (losing_team, data["new_elo"]["teams"]["losing_team"])
    ]
    team_names_and_scores.sort(key=lambda x: x[1], reverse=True)

    team_elos_output = _get_output_from_names_and_scores(team_names_and_scores)

    embed.add_field(name='New player elos', value=player_elos_output, inline=False)
    embed.add_field(name='New team elos', value=team_elos_output, inline=False)

    await message.channel.send(embed=embed)


async def delete_latest_match(message):
    resp = await api.delete_latest_match()

    if not resp['success']:
        embed = discord.Embed(
            title='Error occurred while deleting last match',
            description=resp['error'][:1500],
            color=ERROR_COLOR)
        await message.channel.send(embed=embed)
        return

    embed = discord.Embed(
        title='Success',
        description=resp['data']['message'],
        color=SUCCESS_COLOR)
    await message.channel.send(embed=embed)


def _get_output_from_names_and_scores(names_and_scores, fill='.'):
    """
    names_and_scores is a list of tuples [(username1, score1), ...].
    Return value is a string with lines formatted to left align names and
    right align scores, separated with specified fill character in the middle.
    Output order is the same as the order provided in the function.

    Ex. output:
    username1.....100
    user...........99
    """
    longest_name = max(map(len, [x[0] for x in names_and_scores])) + 3
    longest_score = max(map(len, [str(x[1]) for x in names_and_scores]))

    # First right-fills all names with '.' to the match the
    # longest length name and then left-fills all scores with '.'
    # to match the longest length score.
    formatted_lines = [
        f'{name:{fill}<{longest_name}}{score:{fill}>{longest_score}}'
        for name, score in names_and_scores]

    # Put into a code block to get monospace characters
    # so alignment works properly.
    return '```' + '\n'.join(formatted_lines) + '```'
