from django.core.exceptions import ValidationError
from django.db import models
from simple_history.models import HistoricalRecords


class DutyConfig(models.Model):
    DUTY_DURATION_CHOICES = [
        (1, '1 day'),
        (7, '1 week'),
        (14, '2 weeks'),
    ]
    title = models.TextField(help_text="Title of duty", unique=True)

    team = models.JSONField(
        help_text="List of team (e.g. ['Ivan', 'Maria', 'Petr'])"
    )
    duty_duration = models.PositiveIntegerField(
        choices=DUTY_DURATION_CHOICES,
        help_text="Duty duration"
    )

    # General default texts (used if no overrides are specified)
    header_text = models.TextField(
        help_text="Default header text (used if no overwrite is provided)"
    )
    footer_text = models.TextField(
        blank=True,
        null=True,
        help_text="Default footer text (used if no overwrite is provided)"
    )

    channel_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="ID of the channel to send the message"
    )

    # For duty_duration in (7, 14) – the start date of the sprint (where the countdown starts)
    sprint_start_date = models.DateField(
        blank=True,
        null=True,
        help_text="For 7-day and 14-day schedules: start date of the current sprint"
    )

    first_week = models.JSONField(null=True, blank=True, help_text='Overwrite for first week (e.g. {0: {"header": None, "footer": None, "send": False, "mention": None, "keep_random": False}})')
    second_week = models.JSONField(null=True, blank=True, help_text='Overwrite for first week (e.g. {0: {"header": None, "footer": None, "send": False, "mention": None, "keep_random": False}})')

    last_modified_by = models.EmailField()  # email storage field
    created_at = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()

    def clean(self):
        if self.duty_duration in (7, 14) and not self.sprint_start_date:
            raise ValidationError("For 7-day and 14-day schedules, sprint_start_date is required.")

    def __str__(self):
        return f"{self.title}"


class DutyAssignment(models.Model):
    config = models.ForeignKey(
        DutyConfig,
        on_delete=models.CASCADE,
        related_name="assignments"
    )
    date = models.DateField()
    duty_person = models.CharField(max_length=255)
    random = models.BooleanField(default=False)
    header_text = models.TextField()
    footer_text = models.TextField(blank=True, null=True)
    send = models.BooleanField(default=False)
    mention = models.BooleanField(default=False)
    keep_random = models.BooleanField(default=False)

    last_modified_by = models.EmailField(null=True)  # email storage field

    def __str__(self):
        return f"{self.date}: {self.duty_person}"
