from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import password_validation
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from .models import Event, User, NAME_LENGTH, UserAvailability
from django.utils import timezone


class EmailRelatedFieldSerializer(serializers.PrimaryKeyRelatedField):
    default_error_messages = {
        'required': _('This field is required.'),
        'does_not_exist': _('Invalid email "{pk_value}" - object does not exist.'),
        'incorrect_type': _('Incorrect type. Expected pk value, received {data_type}.'),
    }

    def to_internal_value(self, data):
        if self.pk_field is not None:
            data = self.pk_field.to_internal_value(data)
        try:
            return self.get_queryset().get(email=data)
        except ObjectDoesNotExist:
            self.fail('does_not_exist', pk_value=data)
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data).__name__)


class EventSerializer(serializers.ModelSerializer):
    participants = serializers.SerializerMethodField()
    organiser = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = '__all__'

    def get_participants(self, obj):
        return [e_user.user.email for e_user in obj.users.all()]

    def get_organiser(self, obj):
        for e_user in obj.users.all():
            if e_user.is_organiser:
                return e_user.user.email
        return ""


def time_slot_validator(time_slot):
    if time_slot.minute or time_slot.second:
        raise serializers.ValidationError(_("Only hourly time slots are allowed. e.g DD:MM:YYYY hh:00:00"))


class EventCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=NAME_LENGTH)
    time_slot = serializers.DateTimeField(validators=[time_slot_validator])
    description = serializers.CharField(max_length=500, allow_blank=True, allow_null=True)
    participants = serializers.ListField(
        child=EmailRelatedFieldSerializer(queryset=User.objects.all())
    )


class EventUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=NAME_LENGTH)
    time_slot = serializers.DateTimeField(validators=[time_slot_validator])
    description = serializers.CharField(max_length=500,  allow_null=True)
    participants = serializers.ListField(
        child=EmailRelatedFieldSerializer(queryset=User.objects.all()),
        allow_empty=False
    )
    status = serializers.CharField(max_length=NAME_LENGTH)


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}, 'id': {'read_only': True}}

    def create(self, validated_data):
        user = super(UserSerializer, self).create(validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user

    def validate_password(self, value):
        password_validation.validate_password(value, self.instance)
        return value


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=150)


def future_date_validator(date):
    if date < timezone.make_naive(timezone.now()).date():
        raise serializers.ValidationError(_("Slots can't be defined for past date"))


class UserAvailabilitySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='user')
    date = serializers.DateField(validators=[future_date_validator])
    blocked_slots = serializers.ListField(child=serializers.IntegerField(min_value=0, max_value=23), allow_empty=False)
    available_time_slots = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UserAvailability
        fields = '__all__'

    def to_representation(self, instance):
        booked_slots = list(Event.objects.filter(time_slot__date=instance.date, status=Event.STATUS_CHOICES.active,
                                                 users__user=instance.user).values_list('time_slot__time', flat=True))
        booked_slots = list(map(lambda x: x.hour, booked_slots))
        instance.blocked_slots = list(set(instance.blocked_slots).union(booked_slots))
        return super(UserAvailabilitySerializer, self).to_representation(instance)

    def create(self, validated_data):
        obj = UserAvailability.objects.filter(user_id=validated_data["user"].id, date=validated_data["date"]).first()
        if obj:
            obj.blocked_slots = list(set(validated_data["blocked_slots"]).union(set(obj.blocked_slots)))
        else:
            obj = UserAvailability(user_id=validated_data["user"].id, date=validated_data["date"],
                                   blocked_slots=validated_data["blocked_slots"])
        obj.save()
        return obj

    def get_available_time_slots(self, obj):
        available_slots = list(set(range(24)) - set(obj.blocked_slots))
        available_slots.sort()
        return available_slots


class AvailabilitySerializer(serializers.Serializer):
    date = serializers.DateField()
    user = EmailRelatedFieldSerializer(queryset=User.objects.all(), allow_empty=True, required=False)
