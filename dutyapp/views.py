import random
from datetime import date, datetime

from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from src.slack import Slack
from src.schedule_generator import Duty

from .forms import DutyConfigForm, EmailForm, VerificationCodeForm
from .models import DutyAssignment, DutyConfig
from .serializers import DutyAssignmentSerializer, DutyConfigListSerializer, DutyConfigSerializer


class DutyConfigViewSet(viewsets.ModelViewSet):
    queryset = DutyConfig.objects.all()
    serializer_class = DutyConfigSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    filterset_fields = [
        'duty_duration',
        'header_text',
        'footer_text',
        'channel_id',
        'created_at',
        'last_modified_by'
    ]

    search_fields = ['header_text', 'footer_text', 'channel_id']

    ordering_fields = ['created_at', 'duty_duration']

    def get_serializer_class(self):
        if self.action == 'list':
            return DutyConfigListSerializer
        return DutyConfigSerializer


class DutyAssignmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for duty assignments.
    Allows retrieving, updating and deleting individual assignments.
    Also supports updating an assignment by providing configuration ID and date.
    """
    queryset = DutyAssignment.objects.all()
    serializer_class = DutyAssignmentSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = '__all__'
    search_fields = ['date', 'duty_person', 'random']
    ordering_fields = '__all__'

    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed('POST', detail="Creation is not allowed.")

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed('PUT', detail="Manual update is not allowed. Use update_by_config_date instead.")

    def partial_update(self, request, *args, **kwargs):
        raise MethodNotAllowed('PATCH',
                               detail="Manual partial update is not allowed. Use update_by_config_date instead.")

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed('DELETE', detail="Deletion is not allowed.")

    @action(detail=False, methods=['patch'], url_path='update_by_config_date')
    def update_by_config_date(self, request):
        """
        Update the duty_person for a specific assignment identified by config_id and date.
        Expected payload:
          {
              "config_id": <config id>,
              "date": "YYYY-MM-DD",
              "duty_person": "New Name"
          }
        """
        token = request.META.get('HTTP_X_API_TOKEN')
        is_token_request = (token == settings.API_PERMANENT_TOKEN)
        config_id = request.data.get('config_id')
        date_value = request.data.get('date')
        duty_person = request.data.get('duty_person')

        if not config_id or not date_value or not duty_person:
            return Response(
                {"detail": "config_id, date and duty_person fields are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            assignment = DutyAssignment.objects.get(config_id=config_id, date=date_value)
        except DutyAssignment.DoesNotExist:
            return Response(
                {"detail": "No assignment found for the provided config_id and date."},
                status=status.HTTP_404_NOT_FOUND
            )

        assignment.duty_person = duty_person
        assignment.random = True

        assignment.last_modified_by = 'tbqa@exante.eu' if is_token_request else request.session.get('email')

        assignment.save()

        serializer = self.get_serializer(assignment)
        return Response(serializer.data, status=status.HTTP_200_OK)


def root_redirect_view(request):
    """
    If the user has passed verification (is_verified is in the session),
    we send to the config list page.
    Otherwise, to the code sending page.
    """
    token = request.META.get('HTTP_X_API_TOKEN')
    is_token_request = (token == settings.API_PERMANENT_TOKEN)
    if request.session.get('is_verified') or is_token_request:
        return redirect('duty_config_list')
    else:
        return redirect('send_code')


def create_duty_config(request):
    token = request.META.get('HTTP_X_API_TOKEN')
    is_token_request = (token == settings.API_PERMANENT_TOKEN)
    if request.method == 'POST':
        form = DutyConfigForm(request.POST)
        if form.is_valid():
            config = form.save()
            config.last_modified_by = 'tbqa@exante.eu' if is_token_request else request.session.get('email')
            config.save()
            Duty(config=config).generate_schedule()
            return redirect('duty_config_detail', pk=config.pk)
    else:
        form = DutyConfigForm()
    return render(request, 'dutyapp/create_config.html', {'form': form})


def duty_config_detail(request, pk):
    config = get_object_or_404(DutyConfig, pk=pk)
    return render(request, 'dutyapp/config_detail.html', {'config': config})


def duty_config_list(request):
    configs = DutyConfig.objects.all()
    return render(request, 'dutyapp/config_list.html', {'configs': configs})


def duty_config_schedule(request, pk):
    config = get_object_or_404(DutyConfig, pk=pk)
    today = date.today()
    end_date = date(today.year, 12, 31)
    assignments = config.assignments.filter(date__gte=today, date__lte=end_date).order_by('date')
    return render(request, 'dutyapp/full_schedule.html', {'config': config, 'assignments': assignments})


def edit_duty_config(request, pk):
    config = get_object_or_404(DutyConfig, pk=pk)
    token = request.META.get('HTTP_X_API_TOKEN')
    is_token_request = (token == settings.API_PERMANENT_TOKEN)
    if request.method == 'POST':
        form = DutyConfigForm(request.POST, instance=config)
        if form.is_valid():
            config = form.save()

            config.last_modified_by = 'tbqa@exante.eu' if is_token_request else request.session.get('email')

            config.save()

            today = timezone.now().date()
            config.assignments.filter(date__gte=today).delete()  # Delete only those items whose date is >= current date

            Duty(config=config).generate_schedule()
            return redirect('duty_config_detail', pk=config.pk)
    else:
        form = DutyConfigForm(instance=config)
    return render(request, 'dutyapp/edit_config.html', {'form': form, 'config': config})


def delete_duty_config(request, pk):
    config = get_object_or_404(DutyConfig, pk=pk)
    token = request.META.get('HTTP_X_API_TOKEN')
    is_token_request = (token == settings.API_PERMANENT_TOKEN)
    if request.method == 'POST':
        config.last_modified_by = 'tbqa@exante.eu' if is_token_request else request.session.get('email')
        config.delete()
        return redirect('duty_config_list')
    return render(request, 'dutyapp/delete_config.html', {'config': config})


def send_code_view(request):
    if request.method == 'POST':
        form = EmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            code = str(random.randint(100000, 999999))
            code_sent_time = datetime.now().timestamp()

            # Save code and sending time in session
            request.session['verification_code'] = code
            request.session['code_sent_time'] = code_sent_time
            request.session['email'] = email

            sent = Slack(token=settings.SLACK_TOKEN).send_verify_code(email=email, code=code)
            if not sent:
                return redirect('verify_code')
            else:
                form = EmailForm()
    else:
        form = EmailForm()
    return render(request, 'dutyapp/send_code.html', {'form': form})


def verify_code_view(request):
    max_attempts = 5
    expiration_seconds = 600
    attempts = request.session.get('attempts', 0)

    if request.method == 'POST':
        form = VerificationCodeForm(request.POST)
        if form.is_valid():
            input_code = form.cleaned_data['code']
            session_code = request.session.get('verification_code')
            code_sent_time = request.session.get('code_sent_time')

            if code_sent_time:
                now = datetime.now().timestamp()
                if now - code_sent_time > expiration_seconds:
                    form.add_error('code', 'The code has expired. Please request a new code.')
                    # Clearing session data associated with code
                    request.session.pop('verification_code', None)
                    request.session.pop('code_sent_time', None)
                    request.session.pop('attempts', None)
                    return render(request, 'dutyapp/verify_code.html', {'form': form})

            if input_code == session_code:
                request.session['is_verified'] = True
                request.session.pop('attempts', None)
                return redirect('duty_config_list')
            else:
                attempts += 1
                request.session['attempts'] = attempts
                if attempts >= max_attempts:
                    form.add_error('code', 'Number of attempts exceeded. Please retry your code request.')
                    # Clearing session data associated with code
                    request.session.pop('verification_code', None)
                    request.session.pop('code_sent_time', None)
                    request.session.pop('attempts', None)
                    return redirect('send_code')
                else:
                    remaining = max_attempts - attempts
                    form.add_error('code', f'Invalid code. Remaining attempts: {remaining}.')
    else:
        form = VerificationCodeForm()
    return render(request, 'dutyapp/verify_code.html', {'form': form})
