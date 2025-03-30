# admin.py
from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import DutyConfig


admin.site.register(DutyConfig, SimpleHistoryAdmin)

HistoricalConfiguration = DutyConfig.history.model


class HistoricalConfigurationAdmin(admin.ModelAdmin):
    list_display = ['title', 'last_modified_by', 'created_at']
    search_fields = ['title']


admin.site.register(HistoricalConfiguration, HistoricalConfigurationAdmin)
