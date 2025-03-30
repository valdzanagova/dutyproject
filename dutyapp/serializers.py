from django.utils import timezone
from rest_framework import serializers

from src.schedule_generator import Duty

from .models import DutyAssignment, DutyConfig


class DutyAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DutyAssignment
        fields = ['id', 'date', 'duty_person', 'config', 'random', 'header_text', 'footer_text', 'send', 'mention',
                  'keep_random']
        read_only_fields = ['config']


class DutyConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = DutyConfig
        fields = [
            'title',
            'id',
            'team',
            'duty_duration',
            'sprint_start_date',
            'channel_id',
            'header_text',
            'footer_text',
            'first_week',
            'second_week',
            'last_modified_by',
            'created_at'
        ]
        read_only_fields = ['created_at', 'last_modified_by']

    def create(self, validated_data):
        config = DutyConfig.objects.create(**validated_data)
        Duty(config=config).generate_schedule()
        return config

    def update(self, instance, validated_data):
        instance.team = validated_data.get('team', instance.team)
        instance.duty_duration = validated_data.get('duty_duration', instance.duty_duration)
        instance.sprint_start_date = validated_data.get('sprint_start_date', instance.sprint_start_date)
        instance.channel_id = validated_data.get('channel_id', instance.channel_id)
        instance.header_text = validated_data.get('header_text', instance.header_text)
        instance.footer_text = validated_data.get('footer_text', instance.footer_text)
        instance.first_week = validated_data.get('first_week', instance.first_week)
        instance.second_week = validated_data.get('second_week', instance.second_week)
        
        instance.save()

        today = timezone.now().date()
        instance.assignments.filter(date__gte=today).delete()  # Delete only those items whose date is >= current date

        Duty(config=instance).generate_schedule()
        return instance


class DutyConfigListSerializer(serializers.ModelSerializer):
    class Meta:
        model = DutyConfig
        fields = ['id', 'title', 'team', 'duty_duration', 'created_at', 'channel_id', 'last_modified_by']
