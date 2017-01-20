import tabulate

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.models import Q

from standup.status.models import StandupUser


class Command(BaseCommand):
    help = 'Find a user given a substring'

    def add_arguments(self, parser):
        parser.add_argument('text', type=str)

    def handle(self, *args, **options):
        text = options['text']

        self.stdout.write('Searching for: %s' % text)

        rows = [
            ['user_id', 'username', 'email', 'name', 'slug', 'irc', 'github', '# statuses', 'last login', 'created']
        ]

        id_to_data = {}

        # Search through Users
        users = (
            get_user_model().objects.filter(
                Q(username__icontains=text) |
                Q(email__icontains=text)
            )
            .order_by('id')
        )

        for user in users:
            id_to_data[user.id] = [
                user.username,
                user.email,
                '',
                '',
                '',
                '',
                '',
                user.last_login,
                user.date_joined
            ]

        # Search through StandupUser accounts which have a User--these will stomp on exist items in
        # id_to_data where the user id is the same
        standup_users = (
            StandupUser.objects.filter(
                Q(name__icontains=text) |
                Q(slug__icontains=text) |
                Q(irc_nick__icontains=text) |
                Q(github_handle__icontains=text)
            )
            .order_by('id')
        )

        for user in standup_users:
            id_to_data[user.user.id] = [
                user.user.username,
                user.user.email,
                user.name,
                user.slug,
                user.irc_nick,
                user.github_handle,
                user.statuses.count(),
                user.user.last_login,
                user.user.date_joined
            ]

        for user_id, data in sorted(id_to_data.items()):
            rows.append([user_id] + data)

        self.stdout.write(tabulate.tabulate(rows))
