import json

from django.db import transaction
from django.db.models import (
    Case,
    Count,
    DecimalField,
    ExpressionWrapper,
    F,
    Sum,
    When
)
from django.forms.models import model_to_dict
from django.http import (
    HttpResponseBadRequest,
    HttpResponseNotAllowed,
    HttpResponseNotFound,
    HttpResponseServerError,
    JsonResponse
)
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from .elo import (
    recalculate_all_elos,
    update_player_elos,
    update_team_elos,
    STARTING_ELO
)
from .models import Match, Player, Team



@csrf_exempt
def create_player(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    username = request.POST.get('username')
    if not username:
        return HttpResponseBadRequest('No username provided.')

    try:
        username = str(username)
        if not username.isalpha():
            return HttpResponseBadRequest('Username must be alphabetical.')
    except ValueError as e:
        return HttpResponseBadRequest('Username must be a string.')

    if Player.objects.filter(username=username).exists():
        return HttpResponseBadRequest('A player with that username already exists')

    try:
        Player.objects.create(
            username=username,
            elo=STARTING_ELO
        )
    except Exception as e:
        print(str(e))
        return HttpResponseServerError(str(e))

    return JsonResponse({
        'username': username,
        'elo': STARTING_ELO
    }, status=201)


def get_player(request, username):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])

    if not username:
        return HttpResponseBadRequest('Must provide a username')

    if not username.isalpha():
        return HttpResponseBadRequest('Username must be alphabetical.')

    player = get_object_or_404(Player, username=username)

    wins = Match.objects.filter(winning_team__players=player)
    losses = Match.objects.filter(losing_team__players=player)

    total_games = wins.count() + losses.count()

    if wins.count() == 0:
        win_percentage = 0.
    elif total_games:
        win_percentage = wins.count() / total_games * 100
    else:
        win_percentage = None

    goals_scored = sum([match.winning_score for match in wins] + [match.losing_score for match in losses])
    goals_allowed = sum([match.losing_score for match in wins] + [match.winning_score for match in losses])

    return JsonResponse({
        'username': player.username,
        'elo': player.elo,
        'wins': wins.count(),
        'losses': losses.count(),
        'win_percentage': win_percentage,
        'goals_scored': goals_scored,
        'goals_allowed': goals_allowed
    })


def get_team(request, username1, username2):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])

    if not username1.isalpha() or not username2.isalpha():
        return HttpResponseBadRequest('Both usernames must be alphabetical')

    player1 = get_object_or_404(Player, username=username1)
    player2 = get_object_or_404(Player, username=username2)

    teams = (Team.objects
                .annotate(count=Count('players'))
                .filter(count=2)
                .filter(players=player1)
                .filter(players=player2))

    if not teams.exists():
        return HttpResponseNotFound('Team with those players was not found.')
    elif teams.count() > 1:
        return HttpResponseServerError(
            'Oh no! Multiple teams with only those players was found. Nikhil\'s code sux.')

    team = teams[0]

    wins = Match.objects.filter(winning_team=team)
    losses = Match.objects.filter(losing_team=team)

    goals_scored = sum([match.winning_score for match in wins] + [match.losing_score for match in losses])
    goals_allowed = sum([match.losing_score for match in wins] + [match.winning_score for match in losses])

    win_percentage = wins.count() / (wins.count() + losses.count()) * 100

    return JsonResponse({
        'wins': wins.count(),
        'losses': losses.count(),
        'win_percentage': win_percentage,
        'goals_scored': goals_scored,
        'goals_allowed': goals_allowed,
        'elo': team.elo
    })


@csrf_exempt
def record_match(request):
    """
    This endpoint takes in application/json
    rather than form encoded because it takes a list of usernames
    for winning_team and losing_team
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    try:
        data = json.loads(request.body.decode('utf-8'))
    except json.decoder.JSONDecodeError as e:
        return HttpResponseBadRequest(f'Invalid json provided: {e}')

    winning_team_usernames = data.get('winning_team')
    losing_team_usernames = data.get('losing_team')
    winning_score = data.get('winning_score')
    losing_score = data.get('losing_score')

    if (not winning_team_usernames
            or not losing_team_usernames
            or not winning_score
            or losing_score is None):
        return HttpResponseBadRequest('Must provide winning_team, winning_score, losing_team, losing_score')

    try:
        winning_team_usernames = list(winning_team_usernames)
        losing_team_usernames = list(losing_team_usernames)
        winning_score = int(winning_score)
        losing_score = int(losing_score)
    except ValueError as e:
        return HttpResponseBadRequest(str(e))

    if winning_score != 5:
            return HttpResponseBadRequest('Winning score must be 5')
    elif winning_score <= losing_score:
        return HttpResponseBadRequest(
            f'Winning score {winning_score} must be greater than losing score {losing_score}')
    elif losing_score < 0:
        return HttpResponseBadRequest(
            f'Losing score must be >= 0')
    elif len(winning_team_usernames) != 2 or len(losing_team_usernames) != 2:
        return HttpResponseBadRequest(
            f'Teams must be 2 people each. Provided: {winning_team_usernames} and {losing_team_usernames}')

    common_players = [player for player in winning_team_usernames if player in losing_team_usernames]
    if len(common_players) > 0:
        return HttpResponseBadRequest('Winning and losing teams cannot share players')

    if (winning_team_usernames[0] == winning_team_usernames[1]
            or losing_team_usernames[0] == losing_team_usernames[1]):
        return HttpResponseBadRequest('Teams cannot have the same person twice.')

    winning_player_1 = get_object_or_404(Player, username=winning_team_usernames[0])
    winning_player_2 = get_object_or_404(Player, username=winning_team_usernames[1])
    losing_player_1 = get_object_or_404(Player, username=losing_team_usernames[0])
    losing_player_2 = get_object_or_404(Player, username=losing_team_usernames[1])

    winning_team_qs = (Team.objects
                        .annotate(count=Count('players'))
                        .filter(count=2)
                        .filter(players=winning_player_1)
                        .filter(players=winning_player_2))

    losing_team_qs = (Team.objects
                        .annotate(count=Count('players'))
                        .filter(count=2)
                        .filter(players=losing_player_1)
                        .filter(players=losing_player_2))

    # Create teams if they don't exist already
    if not winning_team_qs:
        winning_team = Team(elo=STARTING_ELO)
        winning_team.save()
        winning_team.players.add(winning_player_1)
        winning_team.players.add(winning_player_2)
    else:
        winning_team = winning_team_qs[0]

    if not losing_team_qs:
        losing_team = Team(elo=STARTING_ELO)
        losing_team.save()
        losing_team.players.add(losing_player_1)
        losing_team.players.add(losing_player_2)
    else:
        losing_team = losing_team_qs[0]

    match = Match.objects.create(
        winning_team=winning_team,
        losing_team=losing_team,
        winning_score=winning_score,
        losing_score=losing_score
    )

    # Calculate new elos for each player and update them
    update_player_elos(match)

    # Calculate new elos for each team as a whole
    update_team_elos(match)

    winning_player_1.refresh_from_db()
    winning_player_2.refresh_from_db()
    losing_player_1.refresh_from_db()
    losing_player_2.refresh_from_db()

    return JsonResponse({
        'success': True,
        'new_elo': {
            'players': {
                winning_player_1.username: winning_player_1.elo,
                winning_player_2.username: winning_player_2.elo,
                losing_player_1.username: losing_player_1.elo,
                losing_player_2.username: losing_player_2.elo,
            },
            'teams': {
                'winning_team': winning_team.elo,
                'losing_team': losing_team.elo
            }
        }
    })

@csrf_exempt
@transaction.atomic
def delete_latest_match(request):
    if request.method != 'DELETE':
        return HttpResponseNotAllowed(['DELETE'])

    try:
        match = Match.objects.latest('timestamp')
    except e:
        print(str(e))
        return HttpResponseNotFound('No matches found.')

    winners = [x[0] for x in match.winning_team.players.values_list('username')]
    winners = ' and '.join(winners)
    losers = [x[0] for x in match.losing_team.players.values_list('username')]
    losers = ' and '.join(losers)

    winning_score = match.winning_score
    losing_score = match.losing_score

    match.delete()
    recalculate_all_elos()

    return JsonResponse({
        'message': f'Deleted game with {winners} beating {losers} {winning_score}-{losing_score}'
    }, status=200)


def leaderboards(request, num):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    return _individual_boards(int(num), '-elo')


def loserboards(request, num):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    return _individual_boards(int(num), 'elo')


def _individual_boards(num, order_by):
    # Sort players by elo descending
    players = (Player.objects
                    .annotate(num_games=Count('teams__winning_matches') + Count('teams__losing_matches'))
                    .filter(num_games__gte=3)
                    .order_by(order_by))

    leaderboards = []
    for player in players[:num]:
        wins = Match.objects.filter(winning_team__players=player)
        losses = Match.objects.filter(losing_team__players=player)

        total_games = wins.count() + losses.count()
        if wins.count() == 0:
            win_percentage = 0.
        elif total_games:
            win_percentage = wins.count() / total_games * 100
        else:
            win_percentage = None

        goals_scored = sum([match.winning_score for match in wins] + [match.losing_score for match in losses])
        goals_allowed = sum([match.losing_score for match in wins] + [match.winning_score for match in losses])

        leaderboards.append({
            'username': player.username,
            'elo': player.elo,
            'wins': wins.count(),
            'losses': losses.count(),
            'win_percentage': win_percentage,
            'goals_scored': goals_scored,
            'goals_allowed': goals_allowed
        })

    return JsonResponse({
        'players': leaderboards
    })


def dream_teams(request, num):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])

    return _team_boards(int(num), '-elo')


def nightmare_teams(request, num):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])

    return _team_boards(int(num), 'elo')


def _team_boards(num, order_by):
    # Sort teams by win percentage descending
    # with minimum 3 wins
    teams = (Team.objects.order_by(order_by)
                 .annotate(wins=Count('winning_matches', distinct=True))
                 .filter(wins__gte=3)
                 .annotate(losses=Count('losing_matches', distinct=True))
                 .annotate(total_games=F('wins') + F('losses'))
                 .annotate(
                     win_percentage=Case(
                         When(losses=0, then=100),
                         default=ExpressionWrapper(
                             100.0 * F('wins') / F('total_games'),
                             output_field=DecimalField()
                         )
                     )
                 ))

    leaderboards = []
    for team in teams[:num]:
        usernames = [player.username for player in team.players.all()]

        goals_scored = sum([match.winning_score for match in team.winning_matches.all()]
                            + [match.losing_score for match in team.losing_matches.all()])
        goals_allowed = sum([match.losing_score for match in team.winning_matches.all()]
                            + [match.winning_score for match in team.losing_matches.all()])

        leaderboards.append({
            'players': usernames,
            'elo': team.elo,
            'wins': team.wins,
            'losses': team.losses,
            'win_percentage': float(team.win_percentage),
            'goals_scored': goals_scored,
            'goals_allowed': goals_allowed
        })

    return JsonResponse({
        'teams': leaderboards
    })