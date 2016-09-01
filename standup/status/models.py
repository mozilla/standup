from collections import OrderedDict

from django.core.urlresolvers import reverse
from django.db import models
from django.utils.timezone import now

from standup.status.utils import (
    format_update,
    week_end as u_week_end,
    week_start as u_week_start,
)


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
    user = models.ForeignKey('user.StandupUser', related_name='statuses')
    project = models.ForeignKey('Project', related_name='statuses', null=True)
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
        data['content'] = format_update(self.content_html)
        data['reply_to_id'] = self.reply_to.id
        data['reply_to_user_id'] = reply_to_user_id
        data['reply_to_username'] = reply_to_username
        data['reply_count'] = self.reply_count

        # FIXME: What do we need these for?
        # data['week_start'] = self.week_start.strftime("%Y-%m-%d")
        # data['week_end'] = self.week_end.strftime("%Y-%m-%d")

        return data


class Team(models.Model):
    """A team of users in the organization."""
    name = models.CharField(
        max_length=100,
        help_text='Name of the team'
    )
    slug = models.SlugField(unique=True, max_length=100)
    users = models.ManyToManyField('user.StandupUser',
                                   related_name='teams',
                                   through='TeamUser')

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


class TeamUser(models.Model):
    team = models.ForeignKey(Team)
    user = models.ForeignKey('user.StandupUser')

    class Meta:
        db_table = 'team_users'
        unique_together = (('team', 'user'),)
