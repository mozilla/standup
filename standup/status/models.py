from collections import OrderedDict

from django.db import models
from django.utils.timezone import now

from standup.status.utils import format_update


class Project(models.Model):
    """A project that does standups."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=6)
    repo_url = models.URLField()

    def __repr__(self):
        return '<Project: [%s] %s>' % (self.slug, self.name)

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
    project = models.ForeignKey('Project', related_name='statuses')
    content = models.TextField()
    content_html = models.TextField()
    reply_to = models.ForeignKey(
        'self', blank=True, null=True, default=None,
        on_delete=models.SET_DEFAULT)

    def __repr__(self):
        return '<Status: %s: %s>' % (self.user.username, self.content)

    def replies(self):
        return Status.objects.filter(reply_to_id=self.id).order_by('-created')

    @property
    def reply_count(self):
        return self.replies().count()

    # @property
    # def week_start(self):
    #     if self.created:
    #         return h_week_start(self.created)
    #     return None

    # @property
    # def week_end(self):
    #     if self.created:
    #         return h_week_end(self.created)
    #     return None

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
