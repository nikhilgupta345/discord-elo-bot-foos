from django.urls import path

from . import views

urlpatterns = [
    path('player/', views.create_player),
    path('player/<username>/', views.get_player),
    path('team/<username1>/<username2>/', views.get_team),
    path('record_match/', views.record_match),
    path('delete_latest_match/', views.delete_latest_match),
    path('leaderboards/<num>/', views.leaderboards),
    path('loserboards/<num>/', views.loserboards),
    path('dream_teams/<num>/', views.dream_teams),
    path('nightmare_teams/<num>/', views.nightmare_teams),
]
