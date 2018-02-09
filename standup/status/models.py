import re
from collections import OrderedDict

from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import now
from django.urls import reverse, NoReverseMatch

from bleach.callbacks import nofollow
from bleach.linkifier import Linker
from bleach.sanitizer import Cleaner
from jinja2 import Markup
from markdown import Markdown

from standup.status.utils import (
    trim_urls,
    week_end as u_week_end,
    week_start as u_week_start,
)
from standup.mdext.nixheaders import NixHeaderExtension


BUG_RE = re.compile(r'(bug #?(\d+))', flags=re.I)
PULL_RE = re.compile(r'((?:pull|pr) #?(\d+))', flags=re.I)
ISSUE_RE = re.compile(r'(issue #?(\d+))', flags=re.I)
USER_RE = re.compile(r'(?<=^|(?<=[^\w\-.]))@([\w-]+)', flags=re.I)
TAG_RE = re.compile(r'(?:^|[^\w\\/])#([a-z][a-z0-9_.-]*)(?:\b|$)', flags=re.I)
MD = Markdown(output_format='html5', extensions=[
    NixHeaderExtension(),
    'nl2br',
    'smart_strong'
])


CLEANER = Cleaner(tags=[])
LINKER = Linker(callbacks=[trim_urls, nofollow])


class StandupUser(models.Model):
    """A standup participant--tied to Django's User model."""
    # Note: User provides "username", "is_superuser", "is_staff" and "email"
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    name = models.CharField(max_length=100, blank=True, null=True)
    slug = models.SlugField(max_length=100, blank=True, null=True, unique=True)
    irc_nick = models.CharField(
        max_length=100, blank=True, null=True, unique=True,
        help_text='IRC nick for this particular user'
    )

    class Meta:
        # ordering = ('user__username',)
        db_table = 'user'

    def __str__(self):
        akas = [aka for aka in [self.slug, self.irc_nick] if aka]
        return '%s (%s)' % (
            self.name,
            ', '.join([':%s' % aka for aka in akas])
        )

    def __repr__(self):
        return '<StandupUser: [{}]>'.format(self.slug)

    def get_absolute_url(self):
        try:
            return reverse('status.user', kwargs={'slug': self.slug})
        except NoReverseMatch:
            return ''

    @property
    def email(self):
        return self.user.email

    def dictify(self):
        """Returns an OrderedDict of model attributes"""
        data = OrderedDict()
        data['id'] = self.id
        data['name'] = self.name
        data['slug'] = self.slug
        data['irc_nick'] = self.irc_nick
        # FIXME: Should we be providing email addresses publicly via the api?
        # data['email'] = self.user.email
        data['is_staff'] = self.user.is_staff
        return data


class Team(models.Model):
    """A team of users in the organization."""
    name = models.CharField(
        max_length=100,
        help_text='Name of the team'
    )
    slug = models.SlugField(unique=True, max_length=100)
    users = models.ManyToManyField(StandupUser, related_name='teams')

    class Meta:
        db_table = 'team'
        ordering = ('name',)

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Team: [%s]>' % (self.name,)

    def get_absolute_url(self):
        try:
            return reverse('status.team', kwargs={'slug': self.slug})
        except NoReverseMatch:
            return ''

    def statuses(self):
        user_ids = self.users.values_list('id', flat=True)
        return Status.objects.filter(user__pk__in=user_ids)

    def dictify(self):
        data = OrderedDict()
        data['id'] = self.id
        data['name'] = self.name
        data['slug'] = self.slug
        return data


class TeamUserCopy(models.Model):
    team_id = models.IntegerField()
    user_id = models.IntegerField()


class Project(models.Model):
    """A project that does standups."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=6)
    repo_url = models.URLField(max_length=100)

    class Meta:
        db_table = 'project'
        ordering = ('name',)

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Project: [%s] %s>' % (self.slug, self.name)

    def get_absolute_url(self):
        try:
            return reverse('status.project', kwargs={'slug': self.slug})
        except NoReverseMatch:
            return ''

    def dictify(self):
        """Returns an OrderedDict of model attributes"""
        data = OrderedDict()
        data['id'] = self.id
        data['name'] = self.name
        data['slug'] = self.slug
        data['color'] = self.color
        return data


class Status(models.Model):
    """A standup update for a user on a given project."""

    created = models.DateTimeField(default=now)
    user = models.ForeignKey(StandupUser, on_delete=models.CASCADE, related_name='statuses')
    project = models.ForeignKey(
        'Project', related_name='statuses', on_delete=models.SET_DEFAULT, default=None,
        null=True, blank=True
    )
    content = models.TextField()

    class Meta:
        db_table = 'status'
        ordering = ('-created',)
        verbose_name_plural = 'statuses'

    def __str__(self):
        return 'Status from %s' % self.user.slug

    def __repr__(self):
        return '<Status: %s: %s>' % (self.user.slug, self.content)

    def get_absolute_url(self):
        try:
            return reverse('status.status', kwargs={'pk': self.pk})
        except NoReverseMatch:
            return ''

    @property
    def week_start(self):
        if self.created:
            return u_week_start(self.created)
        return None

    @property
    def week_end(self):
        if self.created:
            return u_week_end(self.created)
        return None

    def htmlify(self):
        # Remove icky stuff.
        formatted = CLEANER.clean(self.content)

        # Linkify "bug #n" and "bug n" text.
        formatted = BUG_RE.sub(
            r'<a href="http://bugzilla.mozilla.org/show_bug.cgi?id=\2">\1</a>',
            formatted)

        # Wrap tags in a span for formatting
        checked = set()
        for tag in TAG_RE.findall(formatted):
            if tag in checked:
                continue
            hashtag = '#%s' % tag
            formatted = formatted.replace(hashtag,
                                          '<span class="tag tag-%s">%s</span>' %
                                          (tag.lower(), hashtag))
            checked.add(tag)

        checked = set()
        for slug in USER_RE.findall(formatted):
            if slug in checked:
                continue
            slug = slug.lstrip('@')
            user = StandupUser.objects.filter(slug=slug).first()
            if user:
                try:
                    url = reverse('status.user', kwargs={'slug': slug})
                except NoReverseMatch:
                    continue
                at_slug = '@%s' % slug
                formatted = formatted.replace(at_slug,
                                              '<a href="%s">%s</a>' %
                                              (url, at_slug))
            checked.add(slug)

        # Linkify "pull #n" and "pull n" text.
        if self.project and self.project.repo_url:
            repo = self.project.repo_url.rstrip('/')
            formatted = PULL_RE.sub(
                r'<a href="%s/pull/\2">\1</a>' % repo, formatted)
            formatted = ISSUE_RE.sub(
                r'<a href="%s/issues/\2">\1</a>' % repo, formatted)

        # markdownify
        formatted = MD.reset().convert(formatted)

        # Linkify bare urls
        formatted = LINKER.linkify(formatted)
        return Markup(formatted)

    def dictify(self):
        """Returns an OrderedDict of model attributes"""

        data = OrderedDict()
        data['id'] = self.id
        data['created'] = self.created.isoformat()
        if self.user:
            data['user'] = self.user.dictify()
        else:
            data['user'] = None
        if self.project:
            data['project'] = self.project.dictify()
        else:
            data['project'] = None
        data['content'] = self.htmlify()

        # FIXME: What do we need these for?
        # data['week_start'] = self.week_start.strftime("%Y-%m-%d")
        # data['week_end'] = self.week_end.strftime("%Y-%m-%d")

        return data
