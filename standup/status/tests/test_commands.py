from django.core.management import call_command
from django.utils.six import StringIO

from standup.status.tests.factories import UserFactory, StandupUserFactory


def test_find_user(db, django_user_model):
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
