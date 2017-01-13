from django import forms

from .models import Status, StandupUser


class StatusizeForm(forms.ModelForm):
    class Meta:
        model = Status
        fields = ['content', 'project', 'user']
        widgets = {
            'user': forms.HiddenInput(),
            'project': forms.HiddenInput(),
        }


class ProfileForm(forms.ModelForm):
    # NOTE(willkg): Make sure we *never* let users edit their email address without additionally
    # adding the infrastructure to verify the new email address and notify users of the email
    # address change.
    #
    # Otherwise users can change their email address to one for another account and possibly log in
    # as them.
    class Meta:
        model = StandupUser
        fields = ['name', 'irc_nick', 'github_handle']
        labels = {
            'irc_nick': 'IRC Handle',
            'github_handle': 'Github Handle',
        }
