from datetime import date

from django.core.management.base import BaseCommand
from django.utils import timezone

from dutyapp.models import DutyAssignment, DutyConfig
from src.schedule_generator import Duty


class Command(BaseCommand):
    help_ = 'Recalculates all duty schedules for the new year'

    def handle(self, *args, **options):
        today = date.today()
        if today.month == 1 and today.day == 1:
            self.stdout.write("Starting recalculation of schedules for the new year...")
            configs = DutyConfig.objects.all()
            for config in configs:
                
                today = timezone.now().date()
                DutyAssignment.objects.filter(date__gte=today).delete()  # We delete only those positions whose date is >= current date
                
                Duty(config).generate_schedule()
            self.stdout.write("Recalculation completed.")
        else:
            self.stdout.write("Today is not January 1st. No recalculation performed.")
