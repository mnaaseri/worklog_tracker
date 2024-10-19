from django import forms
from .models import WorkLog

class WorkLogForm(forms.ModelForm):
    recorded_time = forms.DateTimeField(
        required=False,  # Make this field optional
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        label='Recorded Time (leave blank to use current time)',
    )

    class Meta:
        model = WorkLog
        fields = ['status', 'recorded_time', 'comment']
