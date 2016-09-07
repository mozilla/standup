import re
from collections import OrderedDict

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now

import bleach

from standup.status.utils import (
    week_end as u_week_end,
    week_start as u_week_start,
)


TAG_TMPL = '{0} <span class="tag tag-{1}">{2}</span>'
BUG_RE = re.compile(r'(bug) #?(\d+)', flags=re.I)
PULL_RE = re.compile(r'(pull|pr) #?(\d+)', flags=re.I)
USER_RE = re.compile(r'(?<=^|(?<=[^\w\-\.]))@([\w-]+)', flags=re.I)
TAG_RE = re.compile(r'(?:^|[^\w\\/])#([a-zA-Z][a-zA-Z0-9_\.-]*)(?:\b|$)')


class Team(models.Model):
    """A team of users in the organization."""
    name = models.CharField(
        max_length=100,
        help_text='Name of the team'
    )
    slug = models.SlugField(unique=True, max_length=100)

    class Meta:
        db_table = 'team'
        ordering = ('name',)

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Team: [%s]>' % (self.name,)

    def get_absolute_url(self):
        return reverse('status.team', kwargs={'slug': self.slug})

    def statuses(self):
        user_ids = self.users.values_list('id', flat=True)
        return Status.objects.filter(user__pk__in=user_ids, reply_to=None)

    def dictify(self):
        data = OrderedDict()
        data['id'] = self.id
        data['name'] = self.name
        data['slug'] = self.slug
        return data


class StandupUser(models.Model):
    """A standup participant--tied to Django's User model."""
    # Note: User provides "username", "name", "is_superuser", "is_staff" and
    # "email"
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    name = models.CharField(max_length=100, blank=True, null=True)
    slug = models.SlugField(max_length=100, blank=True, null=True, unique=True)
    github_handle = models.CharField(max_length=100, blank=True, null=True, unique=True)
    teams = models.ManyToManyField(Team, related_name='users', through='TeamUser')

    class Meta:
        # ordering = ('user__username',)
        db_table = 'user'

    def __str__(self):
        return self.name or self.slug

    def __repr__(self):
        return '<StandupUser: [{}]>'.format(self.slug)

    def get_absolute_url(self):
        return reverse('status.user', kwargs={'slug': self.slug})

    @property
    def username(self):
        return self.user.username

    @property
    def email(self):
        return self.user.email

    def dictify(self):
        """Returns an OrderedDict of model attributes"""
        data = OrderedDict()
        data['id'] = self.id
        data['username'] = self.username
        data['name'] = self.name
        data['slug'] = self.slug
        # FIXME: Should we be providing email addresses publicly via the api?
        # data['email'] = self.user.email
        data['github_handle'] = self.github_handle
        data['is_staff'] = self.user.is_staff
        return data


class TeamUser(models.Model):
    team = models.ForeignKey(Team)
    user = models.ForeignKey(StandupUser)

    class Meta:
        db_table = 'team_users'
        unique_together = (('team', 'user'),)


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
        return reverse('status.project', kwargs={'slug': self.slug})

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
    user = models.ForeignKey(StandupUser, related_name='statuses')
    project = models.ForeignKey('Project', related_name='statuses', null=True, blank=True)
    content = models.TextField()
    content_html = models.TextField()
    reply_to = models.ForeignKey(
        'self', blank=True, null=True, default=None,
        on_delete=models.SET_DEFAULT)

    class Meta:
        db_table = 'status'
        ordering = ('-created',)

    def __str__(self):
        return 'Status from %s' % self.user.username

    def __repr__(self):
        return '<Status: %s: %s>' % (self.user.username, self.content)

    def get_absolute_url(self):
        return reverse('status.status', kwargs={'pk': self.pk})

    def replies(self):
        return Status.objects.filter(reply_to=self).order_by('-created')

    @property
    def reply_count(self):
        return self.replies().count()

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
        formatted = bleach.clean(self.content, tags=[])

        # Linkify "bug #n" and "bug n" text.
        formatted = BUG_RE.sub(
            r'<a href="http://bugzilla.mozilla.org/show_bug.cgi?id=\2">\1 \2</a>',
            formatted)

        checked = set()
        for slug in USER_RE.findall(formatted):
            if slug in checked:
                continue
            slug = slug.lstrip('@')
            user = StandupUser.objects.filter(slug=slug).first()
            if user:
                url = reverse('status.user', kwargs={'slug': slug})
                at_slug = '@%s' % slug
                formatted = formatted.replace(at_slug,
                                              '<a href="%s">%s</a>' %
                                              (url, at_slug))
            checked.add(slug)

        # Linkify "pull #n" and "pull n" text.
        if self.project and self.project.repo_url:
            formatted = PULL_RE.sub(
                r'<a href="%s/pull/\2">\1 \2</a>' % self.project.repo_url, formatted)

        # Search for tags on the original, unformatted string. A tag must start
        # with a letter.
        tags = TAG_RE.findall(self.content)
        tags.sort()
        if tags:
            tags_html = ''
            for tag in tags:
                tags_html = TAG_TMPL.format(tags_html, tag.lower(), tag)
            formatted = '%s <div class="tags">%s</div>' % (formatted, tags_html)

        return formatted

    def dictify(self):
        """Returns an OrderedDict of model attributes"""
        if self.reply_to:
            reply_to_user_id = self.reply_to.user.id
            reply_to_username = self.reply_to.user.username
        else:
            reply_to_user_id = None
            reply_to_username = None

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
        data['reply_to_id'] = self.reply_to.id
        data['reply_to_user_id'] = reply_to_user_id
        data['reply_to_username'] = reply_to_username
        data['reply_count'] = self.reply_count

        # FIXME: What do we need these for?
        # data['week_start'] = self.week_start.strftime("%Y-%m-%d")
        # data['week_end'] = self.week_end.strftime("%Y-%m-%d")

        return data


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        StandupUser.objects.get_or_create(
            user=instance,
            slug=instance.username,
        )
