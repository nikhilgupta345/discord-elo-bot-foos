from aiohttp_requests import requests

BASE_URL = 'http://elo-service:8000/foos'


async def get_player(username):
    try:
        resp = await requests.get(f'{BASE_URL}/player/{username}/')
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

    if resp.status == 404:
        return {
            'success': False,
            'error': 'Player with that username was not found.'
        }
    elif resp.status != 200:
        return {
            'success': False,
            'error': await resp.text()
        }

    return {
        'success': True,
        'data': await resp.json()
    }


async def create_player(username):
    try:
        resp = await requests.post(f'{BASE_URL}/player/', data={'username': username})
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

    if resp.status != 201:
        return {
            'success': False,
            'error': await resp.text()
        }

    return {
        'success': True,
        'data': await resp.json()
    }


async def get_leaderboards(num=10):
    try:
        resp = await requests.get(f'{BASE_URL}/leaderboards/{num}/')
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

    if resp.status != 200:
        return {
            'success': False,
            'error': await resp.text()
        }

    return {
        'success': True,
        'data': await resp.json()
    }


async def get_loserboards(num=10):
    try:
        resp = await requests.get(f'{BASE_URL}/loserboards/{num}/')
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

    if resp.status != 200:
        return {
            'success': False,
            'error': await resp.text()
        }

    return {
        'success': True,
        'data': await resp.json()
    }


async def get_team(player1, player2):
    try:
        resp = await requests.get(f'{BASE_URL}/team/{player1}/{player2}/')
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

    if resp.status == 404:
        return {
            'success': False,
            'error': 'Players were not found or haven\'t played a match together.'
        }

    if resp.status != 200:
        return {
            'success': False,
            'error': await resp.text()
        }

    return {
        'success': True,
        'data': await resp.json()
    }


async def get_dream_teams(num):
    try:
        resp = await requests.get(f'{BASE_URL}/dream_teams/{num}/')
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

    if resp.status != 200:
        return {
            'success': False,
            'error': await resp.text()
        }

    return {
        'success': True,
        'data': await resp.json()
    }


async def get_nightmare_teams(num):
    try:
        resp = await requests.get(f'{BASE_URL}/nightmare_teams/{num}/')
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

    if resp.status != 200:
        return {
            'success': False,
            'error': await resp.text()
        }

    return {
        'success': True,
        'data': await resp.json()
    }


async def record_match(winning_team, losing_team, winning_score, losing_score):
    try:
        resp = await requests.post(f'{BASE_URL}/record_match/', json={
            'winning_team': winning_team,
            'losing_team': losing_team,
            'winning_score': winning_score,
            'losing_score': losing_score
        })
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

    if resp.status == 404:
        return {
            'success': False,
            'error': 'One of the users provided doesn\'t exist'
        }

    elif resp.status != 200:
        return {
            'success': False,
            'error': await resp.text()
        }

    return {
        'success': True,
        'data': await resp.json()
    }


async def delete_latest_match():
    try:
        resp = await requests.delete(f'{BASE_URL}/delete_latest_match/')
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

    if resp.status == 404:
        return {
            'success': False,
            'error': 'No match found.'
        }

    elif resp.status != 200:
        return {
            'success': False,
            'error': await resp.text()
        }

    return {
        'success': True,
        'data': await resp.json()
    }
