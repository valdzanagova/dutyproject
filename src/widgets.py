from django import forms
from django.utils.safestring import mark_safe
import json


WEEKDAYS = [
    (0, "Monday"),
    (1, "Tuesday"),
    (2, "Wednesday"),
    (3, "Thursday"),
    (4, "Friday"),
]


class WeekdayOverridesWidget(forms.Widget):

    def format_value(self, value):
        if value is None:
            return {
                str(day[0]): {
                    "header_text": None,
                    "footer_text": None,
                    "send": False,
                    "mention": None,
                    "keep_random": False,
                } for day in WEEKDAYS
            }
        if isinstance(value, dict):
            return {str(k): v for k, v in value.items()}
        try:
            return json.loads(value)
        except Exception:
            return {}

    def get_context(self, name, value, attrs):
        value = self.format_value(value) or {}
        context = super().get_context(name, value, attrs)
        context['widget'].update({
            'days': [
                {
                    'key': str(day[0]),
                    'name': day[1],
                    'data': value.get(str(day[0]), {
                        "header_text": None,
                        "footer_text": None,
                        "send": False,
                        "mention": None,
                        "keep_random": False,
                    })
                } for day in WEEKDAYS
            ],
            'name': name,
        })
        return context

    def value_from_datadict(self, data, files, name):
        result = {}
        for key, _ in WEEKDAYS:
            key_str = str(key)
            result[key_str] = {
                "send": data.get(f"{name}_{key_str}_send") == "on",
                "mention": data.get(f"{name}_{key_str}_mention") == "on",
                "keep_random": data.get(f"{name}_{key_str}_keep_random") == "on",
                "header_text": data.get(f"{name}_{key_str}_header_text") or None,
                "footer_text": data.get(f"{name}_{key_str}_footer_text") or None,
            }
        return result

    def render(self, name, value, attrs=None, renderer=None):
        context = self.get_context(name, value, attrs)
        return mark_safe(renderer.render(self.template_name, context))
    

class FirstWeekdayOverridesWidget(WeekdayOverridesWidget):
    template_name = 'widgets/first_weekday_overrides.html'


class SecondWeekdayOverridesWidget(WeekdayOverridesWidget):
    template_name = 'widgets/second_weekday_overrides.html'

