from datetime import date, timedelta
import random

from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient

from dutyapp.forms import DutyConfigForm
from dutyapp.models import DutyAssignment, DutyConfig
from src.schedule_generator import Duty


class DutyConfigModelTest(TestCase):
    def setUp(self):
        self.today = date.today()
        self.end_of_year = date(self.today.year, 12, 31)
        self.team_str = "Ivan, Maria, Petr"
        self.team_list = ["Ivan", "Maria", "Petr"]

    def test_team_field_conversion_on_create(self):
        config = DutyConfig.objects.create(
            title="Test Duty 1",
            team=self.team_list,
            duty_duration=1,
            header_text="Default Header",
            footer_text="Default Footer",
            channel_id="channel_1",
            sprint_start_date=self.today,
        )
        assert config.team == self.team_list

    def test_clean_raises_error_without_sprint_start_date_for_7(self):
        with self.assertRaises(ValidationError):
            config = DutyConfig(
                title="Test Duty 2",
                team=self.team_list,
                duty_duration=7,
                header_text="Header",
                footer_text="Footer",
                channel_id="channel_2",
            )
            config.full_clean()

    def test_clean_raises_error_without_sprint_start_date_for_14(self):
        with self.assertRaises(ValidationError):
            config = DutyConfig(
                title="Test Duty 3",
                team=self.team_list,
                duty_duration=14,
                header_text="Header",
                footer_text="Footer",
                channel_id="channel_3",
            )
            config.full_clean()

    def test_clean_allows_sprint_start_date_for_7(self):
        config = DutyConfig(
            title="Test Duty 4",
            team=self.team_list,
            duty_duration=7,
            header_text="Header",
            footer_text="Footer",
            channel_id="channel_4",
            sprint_start_date=self.today,
            last_modified_by="testEmail@mail.com"
        )
        try:
            config.full_clean()
        except ValidationError:
            self.fail("ValidationError raised unexpectedly for duty_duration=7 with sprint_start_date provided.")

    def test_clean_allows_sprint_start_date_for_14(self):
        config = DutyConfig(
            title="Test Duty 5",
            team=self.team_list,
            duty_duration=14,
            header_text="Header",
            footer_text="Footer",
            channel_id="channel_5",
            sprint_start_date=self.today,
            last_modified_by="testEmail@mail.com"
        )
        try:
            config.full_clean()
        except ValidationError:
            self.fail("ValidationError raised unexpectedly for duty_duration=14 with sprint_start_date provided.")

    def test_str_duty_config_returns_title(self):
        config = DutyConfig.objects.create(
            title="Test Duty 6",
            team=self.team_list,
            duty_duration=1,
            header_text="Header",
            footer_text="Footer",
            channel_id="channel_6",
            sprint_start_date=self.today,
        )
        assert str(config) == "Test Duty 6"


class ScheduleGenerationTest(TestCase):
    def setUp(self):
        self.today = date.today()
        self.end_of_year = date(self.today.year, 12, 31)
        self.team_list = ["Ivan", "Maria", "Petr"]
    
    def count_weekdays(self, start, end):
        delta = end - start
        count = 0
        for i in range(delta.days + 1):
            current = start + timedelta(days=i)
            if current.weekday() < 5:
                count += 1
        return count
    
    def generate_overwrite(self):
        return {
            str(i): {
                "header_text": None,
                "footer_text": None,
                "send": random.choice([True, False]),
                "mention": random.choice([True, False]),
                "keep_random": random.choice([True, False]),
            }
            for i in range(6)}

    def test_generate_schedule_for_daily(self):
        config = DutyConfig.objects.create(
            title="Test Duty 7",
            team=self.team_list,
            duty_duration=1,
            header_text="Daily Header",
            footer_text="Daily Footer",
            channel_id="channel_7",
            sprint_start_date=self.today,
        )
        Duty(config).generate_schedule()
        expected_count = self.count_weekdays(self.today, self.end_of_year)
        assert config.assignments.count() == expected_count

    def test_generate_schedule_for_weekly(self):
        config = DutyConfig.objects.create(
            title="Test Duty 8",
            team=self.team_list,
            duty_duration=7,
            header_text="Weekly Header",
            footer_text="Weekly Footer",
            channel_id="channel_8",
            sprint_start_date=self.today,
            first_week=self.generate_overwrite()
        )
        Duty(config).generate_schedule()
        current_date = self.today
        while current_date.weekday() != 0:
            current_date += timedelta(days=1)
        expected_count = self.count_weekdays(self.today, self.end_of_year)
        assert config.assignments.count() == expected_count

    def test_generate_schedule_for_14_day(self):
        config = DutyConfig.objects.create(
            title="Test Duty 9",
            team=self.team_list,
            duty_duration=14,
            header_text="14-day Header",
            footer_text="14-day Footer",
            channel_id="channel_9",
            sprint_start_date=self.today,
            first_week=self.generate_overwrite(),
            second_week=self.generate_overwrite()
        )
        Duty(config).generate_schedule()
        expected_count = self.count_weekdays(self.today, self.end_of_year)
        assert config.assignments.count() == expected_count

    def test_assignments_end_date_not_exceed_dec31(self):
        config = DutyConfig.objects.create(
            title="Test Duty 15",
            team=self.team_list,
            duty_duration=1,
            header_text="Header",
            footer_text="Footer",
            channel_id="channel_15",
            sprint_start_date=self.today,
        )
        Duty(config).generate_schedule()
        for assignment in config.assignments.all():
            assert assignment.date <= self.end_of_year


class DutyAssignmentModelTest(TestCase):
    def setUp(self):
        self.today = date.today()
        self.team_list = ["Ivan", "Maria", "Petr"]
        self.config = DutyConfig.objects.create(
            title="Test Duty 10",
            team=self.team_list,
            duty_duration=1,
            header_text="Header",
            footer_text="Footer",
            channel_id="channel_10",
            sprint_start_date=self.today,
        )
        Duty(self.config).generate_schedule()

    def test_duty_assignment_str(self):
        assignment = self.config.assignments.first()
        expected_str = f"{assignment.date}: {assignment.duty_person}"
        assert str(assignment) == expected_str

    def test_default_values_duty_assignment(self):
        assignment = DutyAssignment.objects.create(
            config=self.config,
            date=self.today,
            duty_person="Ivan",
            header_text=self.config.header_text,
        )
        assert not assignment.send
        assert not assignment.mention
        assert not assignment.keep_random
        assert not assignment.random


class DutyConfigFormTest(TestCase):
    def setUp(self):
        self.today = date.today()

    def test_team_field_cleaning_on_creation(self):
        data = {
            "title": "Test Duty 12",
            "team": "Ivan, Maria, Petr",
            "duty_duration": 1,
            "header_text": "Header",
            "footer_text": "Footer",
            "channel_id": "channel_12",
            "sprint_start_date": self.today.isoformat(),
        }
        form = DutyConfigForm(data=data)
        assert form.is_valid(), form.errors
        config = form.save()
        assert config.team == ["Ivan", "Maria", "Petr"]

    def test_team_field_cleaning_on_edit(self):
        config = DutyConfig.objects.create(
            title="Test Duty 13",
            team=["Ivan", "Maria", "Petr"],
            duty_duration=1,
            header_text="Header",
            footer_text="Footer",
            channel_id="channel_13",
            sprint_start_date=self.today,
        )
        form = DutyConfigForm(instance=config)
        assert form.initial['team'] == "Ivan, Maria, Petr"


class UpdateByConfigDateAPITest(TestCase):
    def setUp(self):
        self.today = date.today()
        self.team_list = ["Ivan", "Maria", "Petr"]
        self.config = DutyConfig.objects.create(
            title="Test Duty 14",
            team=self.team_list,
            duty_duration=1,
            header_text="Header",
            footer_text="Footer",
            channel_id="channel_14",
            sprint_start_date=self.today,
        )
        Duty(self.config).generate_schedule()
        self.client = APIClient()

    def test_update_by_config_date_api_action(self):
        session = self.client.session
        session['is_verified'] = True
        session.save()
        assignment = self.config.assignments.first()
        data = {
            "config_id": self.config.id,
            "date": assignment.date.isoformat(),
            "duty_person": "NewName"
        }
        response = self.client.patch("/api/assignments/update_by_config_date/", data, format="json")
        assert response.status_code == 200
        assignment.refresh_from_db()
        assert assignment.duty_person == "NewName"
