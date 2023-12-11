from django.contrib import admin
from .models import PhoneNumber, Arm, ScheduledMessage, TextMessage, Topic, WeeklyTopic, TopicGoal, MessageTracker, ScheduledMessageControl
from import_export.admin import ImportExportModelAdmin
from django.urls import reverse
from django.utils.html import format_html

# Register your models here.
# admin.site.register(PhoneNumber)
# admin.site.register(Arm)
admin.site.register(Topic)
admin.site.register(WeeklyTopic)
admin.site.register(TopicGoal)
admin.site.register(MessageTracker)

# class TextMessageAdmin(admin.ModelAdmin):
#     # Define a custom method to display the first 50 characters of the 'message' field
#     def short_message(self, obj):
#         return obj.message[:50] if obj.message else ''

#     list_display = ('phone_number', 'short_message', 'route', 'messageuuid', 'created_at', 'updated_at')
#     list_filter = ('route', 'created_at', 'updated_at')
#     search_fields = ('phone_number__number', 'message', 'messageuuid')
#     date_hierarchy = 'created_at'
#     ordering = ('-created_at',)

#     # Set a user-friendly column name for the short_message method
#     short_message.short_description = 'Message (First 50 Characters)'

class ArmAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_numbers_with_subgroups', 'phone_numbers_without_subgroups')

    def phone_numbers_with_subgroups(self, obj):
        return PhoneNumber.objects.filter(arm=obj, sub_group=True).count()

    def phone_numbers_without_subgroups(self, obj):
        return PhoneNumber.objects.filter(arm=obj, sub_group=False).count()

    phone_numbers_with_subgroups.short_description = 'Phone Numbers with Subgroups'
    phone_numbers_without_subgroups.short_description = 'Phone Numbers without Subgroups'

admin.site.register(Arm, ArmAdmin)

class TextMessageAdmin(admin.ModelAdmin):
    # Define a custom method to display the first 50 characters of the 'message' field
    def short_message(self, obj):
        if obj.message:
            url = reverse('admin:base_textmessage_change', args=[obj.id])
            return format_html('<a href="{}">{}</a>', url, obj.message[:50])
        else:
            return ''

    list_display = ('phone_number', 'short_message', 'route', 'messageuuid', 'created_at', 'updated_at')
    list_filter = ('route', 'created_at', 'updated_at')
    search_fields = ('phone_number__phone_number', 'message', 'messageuuid')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    # Set a user-friendly column name for the short_message method
    short_message.short_description = 'Message (First 50 Characters)'

# Register the TextMessage model with the TextMessageAdmin admin class
admin.site.register(TextMessage, TextMessageAdmin)

@admin.register(PhoneNumber)
class PhoneNumberAdmin(ImportExportModelAdmin):
    list_display = ('phone_number', 'arm', 'name', 'active', 'created_at', 'sub_group')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

@admin.register(ScheduledMessage)
class ScheduleMessageAdmin(ImportExportModelAdmin):
    pass

@admin.register(ScheduledMessageControl)
class ScheduledMessageControlAdmin(ImportExportModelAdmin):
    pass

# @admin.register(TextMessage)
# class MessageAdmin(ImportExportModelAdmin):
#     pass
