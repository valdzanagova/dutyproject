import datetime

from dutyapp.models import DutyAssignment


class Duty:
    def __init__(self, config):
        self.config = config
        self.config_id = config.id
        self.duty_duration = config.duty_duration
        self.sprint_start_date = config.sprint_start_date
        self.team = config.team
        self.today = datetime.date.today()
        current_year = self.today.year
        self.end_date = datetime.date(current_year, 12, 31)
        self.one_day = datetime.timedelta(days=1)
        self.header_text = config.header_text
        self.footer_text = config.footer_text
        self.first_week = config.first_week
        self.second_week = config.second_week

      
    def get_last_duty_day(self):

        if self.duty_duration in (7, 14):
            if not isinstance(self.sprint_start_date, datetime.date):
                sprint_start = datetime.datetime.strptime(self.sprint_start_date, "%Y-%m-%d").date()
            else:
                sprint_start = self.sprint_start_date

            diff_days = (self.today - sprint_start).days
            num_sprints = diff_days // self.duty_duration

            if diff_days % self.duty_duration == 0:
                last_duty_date = self.today - self.one_day
            else:
                current_sprint_start = sprint_start + datetime.timedelta(days=num_sprints * self.duty_duration)
                last_duty_date = current_sprint_start - self.one_day
        else:
            if self.today.weekday() < 5:
                ref_day = self.today
            else:
                ref_day = self.today + datetime.timedelta(days=(7 - self.today.weekday()))
            offset = 3 if self.duty_duration == 1 and ref_day.weekday() == 0 else self.duty_duration
            last_duty_date = ref_day - datetime.timedelta(days=offset)

        return last_duty_date.strftime("%Y-%m-%d")

    def get_last_duty_person_index(self, team: list, last_duty_day_str, depth=0):
        if depth >= len(team):
            return None
        last_duty_person = DutyAssignment.objects.filter(date=last_duty_day_str, config=self.config_id).order_by('id').values_list('duty_person', flat=True).last()
    
        if not last_duty_person:
            return None

        try:
            return team.index(last_duty_person)

        except ValueError:
            last_duty_day = datetime.datetime.strptime(last_duty_day_str, "%Y-%m-%d").date()
            previous_sprint_day = last_duty_day - datetime.timedelta(days=self.duty_duration)
            previous_sprint_day_str = previous_sprint_day.strftime("%Y-%m-%d")
            return self.get_last_duty_person_index(team, previous_sprint_day_str, depth + 1)

    def __generate_schedule_by_day(self):
        current_date = self.today

        last_duty_day_str = self.get_last_duty_day()
        last_duty_person_index = self.get_last_duty_person_index(self.team, last_duty_day_str)
        team_index = last_duty_person_index + 1 if last_duty_person_index is not None else 0

        while current_date <= self.end_date:
            if current_date.weekday() < 5:
                date_str = current_date.strftime("%Y-%m-%d")
                duty_person = self.team[team_index % len(self.team)]
                self.__create(current_date=date_str, duty_person=duty_person, header_text=self.header_text,
                              footer_text=self.footer_text, send=True, mention=True, keep_random=False)
                team_index += 1
            current_date += self.one_day

    def __generate_schedule_by_week(self):
        sprint_start_day = self.sprint_start_date.weekday()

        current_date = self.today

        sprint_assignment = {}

        last_duty_day_str = self.get_last_duty_day()
        last_duty_person_index = self.get_last_duty_person_index(self.team, last_duty_day_str)
        team_index = last_duty_person_index + 1 if last_duty_person_index is not None else 0

        while current_date <= self.end_date:
            if current_date.weekday() < 5:
                if current_date.weekday() >= sprint_start_day:
                    sprint_period_start = current_date - datetime.timedelta(
                        days=(current_date.weekday() - sprint_start_day))
                else:
                    sprint_period_start = current_date - datetime.timedelta(
                        days=(current_date.weekday() + 7 - sprint_start_day))

                if sprint_period_start not in sprint_assignment:
                    sprint_assignment[sprint_period_start] = self.team[team_index % len(self.team)]
                    team_index += 1

                date_str = current_date.strftime("%Y-%m-%d")
                duty_person = sprint_assignment[sprint_period_start]
                overwrite = self.first_week[str(current_date.weekday())]

                self.__create(current_date=date_str, duty_person=duty_person, header_text=overwrite['header_text'] or self.header_text,
                              footer_text=overwrite['footer_text'] or self.footer_text, send=overwrite['send'],
                              mention=overwrite['mention'], keep_random=overwrite['keep_random'])
            current_date += self.one_day

    def __generate_schedule_by_two_week(self):
        block_start = self.sprint_start_date

        last_duty_day_str = self.get_last_duty_day()
        last_duty_person_index = self.get_last_duty_person_index(self.team, last_duty_day_str)
        team_index = last_duty_person_index + 1 if last_duty_person_index is not None else 0
        block_duration = datetime.timedelta(days=14)

        while block_start <= self.end_date:
            block_end = block_start + datetime.timedelta(days=13)
            current_day = block_start

            while current_day <= block_end and current_day <= self.end_date:

                if current_day.weekday() < 5 and current_day >= self.today:
                    date_str = current_day.strftime("%Y-%m-%d")
                    duty_person = self.team[team_index % len(self.team)]
                    if current_day < block_start + datetime.timedelta(days=7):
                        overwrite = self.first_week[str(current_day.weekday())]
                    else:
                        overwrite = self.second_week[str(current_day.weekday())]

                    self.__create(current_date=date_str, duty_person=duty_person, header_text=overwrite['header_text']  or self.header_text,
                                  footer_text=overwrite['footer_text']  or self.footer_text, send=overwrite['send'],
                                  mention=overwrite['mention'], keep_random=overwrite['keep_random'])
                current_day += self.one_day
            if current_day >= self.today:
                team_index += 1
            block_start += block_duration

    def __create(self, current_date, duty_person, header_text, footer_text, send, mention, keep_random):
        DutyAssignment.objects.create(
            config=self.config,
            date=current_date,
            duty_person=duty_person,
            header_text=header_text,
            footer_text=footer_text,
            send=send,
            mention=mention,
            keep_random=keep_random)

    def generate_schedule(self):
        if self.duty_duration == 1:
            self.__generate_schedule_by_day()

        elif self.duty_duration == 7:
            self.__generate_schedule_by_week()

        elif self.duty_duration == 14:
            self.__generate_schedule_by_two_week()
