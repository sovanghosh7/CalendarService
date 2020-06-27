from django.contrib import admin
from admin_common import CalenderModelAdmin, ff
from easy_select2 import select2_modelform
from .models import *


class UserAvailabilityAdmin(CalenderModelAdmin):
    form = select2_modelform(UserAvailability)
    list_display = ('id', ff('user__email'), 'date')
    search_fields = ('id', 'user__email', 'date')


class EventAdmin(CalenderModelAdmin):
    form = select2_modelform(Event)
    list_display = ('id', 'title', 'time_slot', 'status')
    search_fields = ('id', 'title', 'time_slot')


class EventUserAdmin(CalenderModelAdmin):
    form = select2_modelform(EventUser)
    list_display = ('id', ff('user__email'), ff('event__title'), 'is_organiser')
    search_fields = ('id', 'user__email', 'event__title')


admin.site.register(UserAvailability, UserAvailabilityAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(EventUser, EventUserAdmin)
