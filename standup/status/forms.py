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
    class Meta:
        model = StandupUser
        fields = ['name', 'slug', 'github_handle']
        labels = {
            'slug': 'IRC Handle',
            'github_handle': 'Github Handle',
        }
