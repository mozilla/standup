from django.core.management import call_command
from django.utils.six import StringIO

import pytest

from standup.status.tests.factories import (
    StandupUserFactory,
    StatusFactory,
    TeamFactory,
    UserFactory,
)


def test_find_user(db):
    user = UserFactory.create(username='jimbob', email='j@example.com')
    StandupUserFactory.create(user=user, irc_nick='jimbobbaz')

    stdout = StringIO()
    call_command('finduser', 'willkg', stdout=stdout)
    output = stdout.getvalue().splitlines()
    assert len(output) == 4
    for i, starter in enumerate([
            'Searching for: willkg',
            '-----',
            'user_id',
            '-----'
    ]):
        assert output[i].startswith(starter)

    stdout = StringIO()
    call_command('finduser', 'jimbob', stdout=stdout)
    output = stdout.getvalue().splitlines()
    assert len(output) == 5
    for i, starter in enumerate([
            'Searching for: jimbob',
            '-----',
            'user_id  username',
            '1        jimbob',
    ]):
        print((i, output[i], starter))
        assert output[i].startswith(starter)


class TestMergeUser:
    def test_no_standupuser(self, db, django_user_model):
        """Test when keep and delete have no standup user"""
        user_keep = UserFactory.create(username='jimbob', email='jimbob@example.com')
        user_delete = UserFactory.create(username='jane', email='jane@example.com')

        stdout = StringIO()
        call_command('mergeuser', keep=user_keep.id, delete=user_delete.id, assume_yes=True, stdout=stdout)
        output = stdout.getvalue()
        print(output)

        # Verify email address was copied from delete to keep
        user_keep = django_user_model.objects.get(id=user_keep.id)
        assert user_keep.email == 'jane@example.com'

        # Verify delete no longer exists
        with pytest.raises(django_user_model.DoesNotExist):
            django_user_model.objects.get(id=user_delete.id)

    def test_keep_no_standupuser_but_delete_has_standupuser(self, db, django_user_model):
        """Test when keep has no standup user, but delete does"""
        user_keep = UserFactory.create(username='jimbob', email='jimbob@example.com')
        user_delete = UserFactory.create(username='jane', email='jane@example.com')
        standupuser_delete = StandupUserFactory.create(user=user_delete)

        stdout = StringIO()
        call_command('mergeuser', keep=user_keep.id, delete=user_delete.id, assume_yes=True, stdout=stdout)
        output = stdout.getvalue()
        print(output)

        # Verify profile was transfered from delete to keep
        user_keep = django_user_model.objects.get(id=user_keep.id)
        assert user_keep.profile.id == standupuser_delete.id

        # Verify delete no longer exists
        with pytest.raises(django_user_model.DoesNotExist):
            django_user_model.objects.get(id=user_delete.id)

    def test_keep_and_delete_have_standupser(self, db, django_user_model):
        """Test when keep and delete both have standup users"""
        user_keep = UserFactory.create(username='jimbob', email='jimbob@example.com')
        standupuser_keep = StandupUserFactory.create(user=user_keep)
        StatusFactory.create(user=standupuser_keep, content='1'),
        StatusFactory.create(user=standupuser_keep, content='2'),
        StatusFactory.create(user=standupuser_keep, content='3'),

        user_delete = UserFactory.create(username='jane', email='jane@example.com')
        standupuser_delete = StandupUserFactory.create(user=user_delete)
        StatusFactory.create(user=standupuser_delete, content='4'),
        StatusFactory.create(user=standupuser_delete, content='5'),
        StatusFactory.create(user=standupuser_delete, content='6'),

        stdout = StringIO()
        call_command('mergeuser', keep=user_keep.id, delete=user_delete.id, assume_yes=True, stdout=stdout)
        output = stdout.getvalue()
        print(output)

        # Verify all statuses were transfered from delete to keep
        user_keep = django_user_model.objects.get(id=user_keep.id)
        statuses = [status.content for status in user_keep.profile.statuses.all()]
        assert sorted(statuses) == ['1', '2', '3', '4', '5', '6']

        # Verify email address was transferred from delete -> keep
        assert user_keep.email == 'jane@example.com'

        # Verify delete no longer exists
        with pytest.raises(django_user_model.DoesNotExist):
            django_user_model.objects.get(id=user_delete.id)

    def test_teams(self, db, django_user_model):
        """Verify teams get carried over"""
        team1 = TeamFactory.create()
        team2 = TeamFactory.create()
        team3 = TeamFactory.create()

        user_keep = UserFactory.create(username='jimbob', email='jimbob@example.com')
        standupuser_keep = StandupUserFactory.create(user=user_keep)
        team1.users.add(standupuser_keep)
        team1.save()
        team3.users.add(standupuser_keep)
        team3.save()

        user_delete = UserFactory.create(username='jane', email='jane@example.com')
        standupuser_delete = StandupUserFactory.create(user=user_delete)
        team1.users.add(standupuser_delete)
        team1.save()
        team2.users.add(standupuser_delete)
        team2.save()

        stdout = StringIO()
        call_command('mergeuser', keep=user_keep.id, delete=user_delete.id, assume_yes=True, stdout=stdout)
        output = stdout.getvalue()
        print(output)

        user_keep = django_user_model.objects.get(id=user_keep.id)
        teams = [team.name for team in user_keep.profile.teams.all()]
        assert sorted(teams) == sorted([team1.name, team2.name, team3.name])
