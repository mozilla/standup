import tabulate

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from standup.status.models import StandupUser


class Command(BaseCommand):
    help = 'Stats for standup db'

    def handle(self, *args, **options):
        User = get_user_model()

        users = []
        for user in User.objects.all():
            try:
                users.append((user.username, user.email, user.profile.statuses.count()))
            except StandupUser.DoesNotExist:
                users.append((user.username, user.email, 'NO PROFILE'))

        users.sort(key=lambda item: item[2] if item[2] != 'NO PROFILE' else 0, reverse=1)
        print('Top 10 users:')
        print(tabulate.tabulate(users[:10]))
        print('')

        print('Users with no email address:')
        print(tabulate.tabulate(
            [user for user in users if not user[1]]
        ))
        print('')

        print('Users with no profile:')
        print(tabulate.tabulate(
            [user for user in users if user[2] == 'NO PROFILE']
        ))
        print('')

        print('Users with no status:')
        print(tabulate.tabulate(
            [user for user in users if not user[2]]
        ))
