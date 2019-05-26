from django.core.management.base import BaseCommand, CommandError
from foos.elo import recalculate_all_elos

class Command(BaseCommand):
    help = 'Recalculates all elos based on current matches in DB'

    def handle(self, *args, **options):
        recalculate_all_elos()