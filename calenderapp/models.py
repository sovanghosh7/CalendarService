from django.contrib import auth
from django.core.exceptions import ValidationError
from rest_framework import serializers
from django.db import models
from django.db import transaction
from django.utils import timezone as utc_timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.dispatch import receiver
from django.contrib.postgres.fields import ArrayField
from rest_framework.authtoken.models import Token
from model_utils.models import TimeStampedModel
from model_utils import Choices
from dateutil.parser import parse
from pytz import timezone


NAME_LENGTH = 60

User = auth.get_user_model()

# monkey patch User model to enforce uniqueness on email field
User._meta.get_field("email").blank = False
User._meta.get_field("email")._unique = True


@receiver(models.signals.post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


class BaseModel(TimeStampedModel):
    def save(self, *args, **kwargs):
        self.full_clean()
        super(BaseModel, self).save(*args, **kwargs)

    class Meta:
        abstract = True


class UserAvailability(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    blocked_slots = ArrayField(models.IntegerField())

    def __str__(self):
        return '{}-{}'.format(self.user, self.date)

    def clean(self):
        events_slots = list(Event.objects.filter(status=Event.STATUS_CHOICES.active, time_slot__date=self.date,
                                                 users__user__id=self.user_id).values_list('time_slot__time',
                                                                                           flat=True))
        for i in events_slots:
            if i.hour in self.blocked_slots:
                raise serializers.ValidationError(
                    {'err_message': _('There is already an event booked at time slot : {}'.format(i.hour))})


class Event(BaseModel):
    STATUS_CHOICES = Choices(
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
    )
    title = models.CharField(max_length=NAME_LENGTH)
    description = models.CharField(max_length=500, null=True, blank=True)
    time_slot = models.DateTimeField()
    status = models.CharField(max_length=NAME_LENGTH, choices=STATUS_CHOICES)

    def clean(self):
        time_slot = self.time_slot
        if isinstance(time_slot, str):
            time_slot = parse(self.time_slot)
        if time_slot.tzinfo is None:
            time_slot = timezone(settings.TIME_ZONE).localize(time_slot)
        if time_slot < utc_timezone.now():
            raise ValidationError(
                {'err_message': _('Event can not be booked for past datetime : {}'.format(self.time_slot))})

    def __str__(self):
        return '{}-{}'.format(self.title, self.time_slot)


# on update of EventUser instance it must have updated_time_slot
class EventUser(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='users')
    is_organiser = models.BooleanField(default=False)

    def __str__(self):
        return '{}-{}'.format(self.user, self.event)

    def clean(self):
        time_slot = self.updated_time_slot if self.id else self.event.time_slot
        naive_time_slot = utc_timezone.make_naive(time_slot)
        availability = UserAvailability.objects.filter(user_id=self.user_id,
                                                       date=naive_time_slot.date()).first()
        if availability and naive_time_slot.hour in availability.blocked_slots:
            raise ValidationError(
                {'err_message': _('Time slot is not available for user : {}'.format(self.user.email))})
        if Event.objects.filter(time_slot=time_slot, users__user__id=self.user_id,
                                status=Event.STATUS_CHOICES.active).exists():
            raise ValidationError(
                {'err_message': _('Time slot is conflicting with another event for user : {}'.format(self.user.email))})


def create_event(title, description, time_slot, guest_user_ids, organiser_id):
    guest_user_ids = set(guest_user_ids)
    guest_user_ids.add(organiser_id)
    with transaction.atomic():
        event = Event.objects.create(title=title, time_slot=time_slot, description=description,
                                     status=Event.STATUS_CHOICES.active)
        for user in guest_user_ids:
            EventUser.objects.create(user_id=user,
                                     event_id=event.id) if user != organiser_id else EventUser.objects.create(
                user_id=user, event_id=event.id, is_organiser=True)
    return event


def update_event(instance, validated_data):
    current_time_slot = instance.time_slot
    if validated_data.get("title") is not None:
        instance.title = validated_data.get("title")
    if validated_data.get("description") is not None:
        instance.description = validated_data.get("description")
    if validated_data.get("status") is not None:
        instance.status = validated_data.get("status")
    if validated_data.get('time_slot') is not None:
        instance.time_slot = validated_data.get('time_slot')
    validated_users = set()
    if validated_data.get("participants") is not None:
        validated_users = set([user.id for user in validated_data.get("participants")])
    participants = set([participant.id for participant in instance.participants])
    validated_users = validated_users or participants
    if instance.organiser not in validated_users:
        raise ValidationError({'err_message': _('Event organiser can not be removed')})

    with transaction.atomic():
        if validated_data.get('time_slot') and validated_data['time_slot'] != current_time_slot:
            for user_id in validated_users.intersection(participants):
                obj = EventUser.objects.get(user_id=user_id, event_id=instance.id)
                obj.updated_time_slot = validated_data['time_slot']
                obj.save()
        instance.save()
        for user_id in (validated_users - participants):
            EventUser.objects.create(user_id=user_id, event_id=instance.id)

        EventUser.objects.filter(event_id=instance.id, user_id__in=(participants - validated_users)).delete()
    return instance
