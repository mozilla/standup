from django import forms

from .models import Status


class StatusizeForm(forms.ModelForm):
    class Meta:
        model = Status
        fields = ['content', 'project', 'user']
        widgets = {
            'user': forms.HiddenInput(),
            'project': forms.HiddenInput(),
        }
