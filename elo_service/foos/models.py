from django.db import models


class Player(models.Model):
    username = models.CharField(max_length=32)
    elo = models.IntegerField(default=1000)


class Team(models.Model):
    players = models.ManyToManyField(Player, related_name='teams')
    elo = models.IntegerField(default=1000)


class Match(models.Model):
    winning_team = models.ForeignKey(Team, related_name='winning_matches', on_delete=models.CASCADE)
    losing_team = models.ForeignKey(Team, related_name='losing_matches', on_delete=models.CASCADE)

    winning_score = models.IntegerField()
    losing_score = models.IntegerField()

    timestamp = models.DateTimeField(auto_now_add=True)