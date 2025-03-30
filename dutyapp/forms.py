import ast

from django import forms

from .models import DutyConfig
from src.widgets import FirstWeekdayOverridesWidget, SecondWeekdayOverridesWidget


class EmailForm(forms.Form):
    email = forms.EmailField(label="Enter your email")


class VerificationCodeForm(forms.Form):
    code = forms.CharField(label="Enter the received code", max_length=6)


class DutyConfigForm(forms.ModelForm):
    team = forms.CharField(
        label='List of team members',
        help_text='Enter the names of the participants separated by commas (for example: Lera, Vova, Sasha)'
    )
    first_week = forms.JSONField(widget=FirstWeekdayOverridesWidget())
    second_week = forms.JSONField(widget=SecondWeekdayOverridesWidget())

    class Meta:
        model = DutyConfig
        fields = [
            'title',
            'team',
            'duty_duration',
            'sprint_start_date',
            'channel_id',
            'header_text',
            'footer_text',
            'first_week',
            'second_week'
        ]
        widgets = {
            'title': forms.Textarea(attrs={'class': 'custom-textarea'}),
            'sprint_start_date': forms.DateInput(attrs={'type': 'date'}),
            'header_text': forms.Textarea(attrs={'class': 'custom-textarea'}),
            'footer_text': forms.Textarea(attrs={'class': 'custom-textarea'})
        }

    def __init__(self, *args, **kwargs):
        super(DutyConfigForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk and isinstance(self.instance.team, list):
            self.initial['team'] = ", ".join(self.instance.team)

    def clean_team(self):
        team_value = self.cleaned_data['team']
        if isinstance(team_value, str) and team_value.strip().startswith('[') and team_value.strip().endswith(']'):
            try:
                parsed = ast.literal_eval(team_value)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed]
            except Exception:
                pass

        if isinstance(team_value, str):
            return [name.strip() for name in team_value.split(',') if name.strip()]
        return team_value
    

    
