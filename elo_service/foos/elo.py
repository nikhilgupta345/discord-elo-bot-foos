from django.db import transaction

from foos.models import Match, Player, Team

STARTING_ELO = 1000

def update_team_elos(match):
    """
    Using the standard Elo algorithm with K = 32:
    https://metinmediamath.wordpress.com/2013/11/27/how-to-calculate-the-elo-rating-including-example/
    """
    winning_team = match.winning_team
    losing_team = match.losing_team

    K = 32
    RPA = 400

    r_winning_team = 10 ** (winning_team.elo / RPA)
    r_losing_team = 10 ** (losing_team.elo / RPA)

    expected_winning_team = r_winning_team / (r_winning_team + r_losing_team)
    expected_losing_team = r_losing_team / (r_winning_team + r_losing_team)

    winning_team.elo = round(winning_team.elo + K * (1 - expected_winning_team))
    losing_team.elo = round(losing_team.elo + K * (0 - expected_losing_team))

    winning_team.save()
    losing_team.save()


def update_player_elos(match):
    """
    Algorithm from:
    https://gamedesignerkid.blogspot.com/2017/04/how-to-use-elo-ranking-for-team.html
    """
    K = 32
    RPA = 400

    wp1, wp2 = match.winning_team.players.all()[:2]
    lp1, lp2 = match.losing_team.players.all()[:2]

    # Get the elo for each team. This is computed using the sum of the player's
    # elos, rather than the actual elo assigned for that team.
    winning_team_elo = wp1.elo + wp2.elo
    losing_team_elo = lp1.elo + lp2.elo

    # Find out what percentage each player contributed
    # to the team's overall elo
    wp1_elo_percent = wp1.elo / winning_team_elo
    wp2_elo_percent = wp2.elo / winning_team_elo

    lp1_elo_percent = lp1.elo / losing_team_elo
    lp2_elo_percent = lp2.elo / losing_team_elo

    # Factor for each team
    r_winning_team = 10 ** (winning_team_elo / RPA)
    r_losing_team = 10 ** (losing_team_elo / RPA)

    # How much each team was expected to win this match
    expected_winning_team = r_winning_team / (r_winning_team + r_losing_team)
    expected_losing_team = r_losing_team / (r_winning_team + r_losing_team)

    # Based on their expectation, adjust their elo accordingly
    new_winning_team_elo = winning_team_elo + K * (1 - expected_winning_team)
    new_losing_team_elo = losing_team_elo + K * (0 - expected_losing_team)

    # How much did the team's elo change?
    delta_winning_team = new_winning_team_elo - winning_team_elo
    delta_losing_team = new_losing_team_elo - losing_team_elo

    # They get reverse of their share of the delta elo
    # so that the person with the higher elo gets a smaller
    # bump than the one with a lower elo
    delta_wp1 = delta_winning_team * wp2_elo_percent
    delta_wp2 = delta_winning_team * wp1_elo_percent
    wp1.elo = round(wp1.elo + delta_wp1)
    wp2.elo = round(wp2.elo + delta_wp2)

    # If they lost then they lose points proportionally so that the
    # higher ranked player loses more points.
    delta_lp1 = delta_losing_team * lp1_elo_percent
    delta_lp2 = delta_losing_team * lp2_elo_percent
    lp1.elo = round(lp1.elo + delta_lp1)
    lp2.elo = round(lp2.elo + delta_lp2)

    # Persist to DB
    wp1.save()
    wp2.save()
    lp1.save()
    lp2.save()

@transaction.atomic
def recalculate_all_elos():
    Player.objects.all().update(elo=STARTING_ELO)
    Team.objects.all().update(elo=STARTING_ELO)

    for match in Match.objects.all():
        update_player_elos(match)
        update_team_elos(match)
