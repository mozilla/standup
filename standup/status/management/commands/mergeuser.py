from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from standup.status.models import StandupUser


User = get_user_model()


class Command(BaseCommand):
    help = 'Merge two user accounts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep', type=int,
            help='the id of the user record to keep and merge all data into'
        )
        parser.add_argument(
            '--delete', type=int,
            help='the id of the user record to delete'
        )
        parser.add_argument(
            '--keep-email', dest='keep_email', action='store_true',
            help=(
                'whether to keep the email address of the --keep record; otherwise the '
                'email address is stomped on by the email address in the --delete record'
            )
        )
        parser.add_argument(
            '-y', '--yes', dest='assume_yes', action='store_true',
            help='whether to skip prompts'
        )

    def handle(self, *args, **options):
        try:
            user_keep = User.objects.get(id=options['keep'])
        except User.DoesNotExist:
            self.stdout.write('User keep=%s does not exist. Exiting.' % options['keep'])
            return 1

        try:
            user_delete = User.objects.get(id=options['delete'])
        except User.DoesNotExist:
            self.stdout.write('User delete=%s does not exist. Exiting.' % options['delete'])
            return 1

        def get_teams(user):
            try:
                return [team.name for team in user.profile.teams.all()]
            except StandupUser.DoesNotExist:
                return 0

        def get_status_count(user):
            try:
                return StandupUser.objects.get(user=user).statuses.count()
            except StandupUser.DoesNotExist:
                return 0

        self.stdout.write('Deleting and merging from:')
        self.stdout.write('    id:          %s' % user_delete.id)
        self.stdout.write('    username:    %s' % user_delete.username)
        self.stdout.write('    email:       %s' % user_delete.email)
        self.stdout.write('    date_joined: %s' % user_delete.date_joined)
        self.stdout.write('    statuses:    %s' % get_status_count(user_delete))
        self.stdout.write('    teams:       %s' % get_teams(user_delete))
        self.stdout.write('')
        self.stdout.write('Keeping and merging into:')
        self.stdout.write('    id:          %s' % user_keep.id)
        self.stdout.write('    username:    %s' % user_keep.username)
        self.stdout.write('    email:       %s' % user_keep.email)
        self.stdout.write('    date_joined: %s' % user_keep.date_joined)
        self.stdout.write('    statuses:    %s' % get_status_count(user_keep))
        self.stdout.write('    teams:       %s' % get_teams(user_keep))
        self.stdout.write('')

        if not options['assume_yes']:
            self.stdout.write('Continue?: y/N')
            cont = input()
            if cont.strip().lower() != 'y':
                self.stdout.write('Exiting.')
                return 1

        # Transfer statuses and profile information
        if not hasattr(user_keep, 'profile'):
            if hasattr(user_delete, 'profile'):
                # Keep has no profile, but delete does, so we transfer it over
                self.stdout.write('Keep has no profile--transferring profile')
                profile = user_delete.profile
                profile.user = user_keep
                profile.save()

        else:
            if hasattr(user_delete, 'profile'):
                # They both have profiles, so transfer all the statuses from delete -> keep
                self.stdout.write('Transfering statuses from delete -> keep')
                for status in user_delete.profile.statuses.all():
                    # NOTE(willkg): 'status.user' is a StandupUser instance
                    status.user = user_keep.profile
                    status.save()

        # Copy email address from delete -> keep
        if not options['keep_email']:
            self.stdout.write('Copying email from delete -> keep')
            user_keep.email = user_delete.email
        else:
            self.stdout.write('Keeping email address')

        # Save user data
        user_keep.save()

        # Copy teams from delete -> keep
        self.stdout.write('Copying teams from delete -> keep')
        if hasattr(user_delete, 'profile'):
            for team in user_delete.profile.teams.all():
                user_keep.profile.teams.add(team)
            user_keep.save()

        # Delete
        self.stdout.write('Deleting delete')
        user_delete.delete()

        self.stdout.write('Done!')
