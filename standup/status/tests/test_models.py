import pytest

from standup.status.tests.factories import StatusFactory, StandupUserFactory


@pytest.mark.django_db()
def test_tags():
    """Test that format update parses tags correctly"""

    # Test valid tags.
    for tag in ('#t', '#tag', '#TAG', '#tag123'):
        expected = '<p><span class="tag tag-%s">%s</span></p>' % (tag[1:].lower(), tag)
        assert StatusFactory(content=tag).htmlify() == expected

    # Test invalid tags. Not first b/c markdown.
    for tag in ('tag #1', 'tag #.abc', 'tag #?abc'):
        assert StatusFactory(content=tag).htmlify() == '<p>%s</p>' % tag


@pytest.mark.django_db()
def test_status_htmlify():
    # plain olde markdown links should work
    original = '[The Dude](https://example.com/dude)'
    expected = '<p><a href="https://example.com/dude" rel="nofollow">The Dude</a></p>'
    assert StatusFactory(content=original).htmlify() == expected

    # bare urls should work as well, and be truncated
    original = 'My site is https://example.com/the-dude-abides-man'
    expected = '<p>My site is <a href="https://example.com/the-dude-abides-man" rel="nofollow">' \
               'https://example.com/the-dude-a...</a></p>'
    assert StatusFactory(content=original).htmlify() == expected

    # https://github.com/mozilla/standup/issues/321
    original = '[#1234](https://example.com/dude)'
    expected = '<p><a href="https://example.com/dude" rel="nofollow">#1234</a></p>'
    assert StatusFactory(content=original).htmlify() == expected

    # bugzilla linking
    original = 'Bug 1234, bug #5678'
    expected = (
        '<p>'
        '<a href="http://bugzilla.mozilla.org/show_bug.cgi?id=1234" rel="nofollow">Bug 1234</a>, '
        '<a href="http://bugzilla.mozilla.org/show_bug.cgi?id=5678" rel="nofollow">bug #5678</a>'
        '</p>'
    )
    assert StatusFactory(content=original).htmlify() == expected

    # github linking
    original = 'pr 1234, issue #5678'
    expected = '<p><a href="{0}pull/1234" rel="nofollow">pr 1234</a>, ' \
               '<a href="{0}issues/5678" rel="nofollow">issue #5678</a></p>'
    status = StatusFactory(content=original)
    expected = expected.format(status.project.repo_url)
    assert status.htmlify() == expected

    # user linking
    StandupUserFactory(user__username='dude')
    original = 'phone\'s ringing @dude'
    expected = '<p>phone\'s ringing <a href="/user/dude/" rel="nofollow">@dude</a></p>'
    assert StatusFactory(content=original).htmlify() == expected
    # not a user
    original = 'phone\'s ringing @bunny'
    expected = '<p>phone\'s ringing @bunny</p>'
    assert StatusFactory(content=original).htmlify() == expected
