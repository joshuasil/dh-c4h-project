from django.contrib import admin
from .models import PhoneNumber, Arm, ScheduledMessage, TextMessage, Topic, WeeklyTopic, TopicGoal, MessageTracker, ScheduledMessageControl, Picklist
from import_export.admin import ImportExportModelAdmin
from django.urls import reverse
from django.utils.html import format_html
from .aws_kms_functions import decrypt_data
from django import forms

# Register your models here.
# admin.site.register(PhoneNumber)
# admin.site.register(Arm)
admin.site.register(Topic)
# admin.site.register(WeeklyTopic)

# admin.site.register(MessageTracker)

# admin.site.register(TextMessage)

class PhoneNumberForm(forms.ModelForm):
    class Meta:
        model = PhoneNumber
        exclude = ["phone_number_hash"]

    def __init__(self, *args, **kwargs):
        super(PhoneNumberForm, self).__init__(*args, **kwargs)
        if self.instance.pk:  # Check if the instance is being updated
            # Decrypt the phone_number and name
            self.initial['phone_number'] = decrypt_data(self.instance.phone_number, self.instance.phone_number_key)
            self.initial['name'] = decrypt_data(self.instance.name, self.instance.name_key)

class ArmAdmin(ImportExportModelAdmin):
    list_display = ('name', 'phone_numbers_count')

    def phone_numbers_count(self, obj):
        return PhoneNumber.objects.filter(arm=obj).count()

    phone_numbers_count.short_description = 'Phone Numbers Count'

admin.site.register(Arm, ArmAdmin)

@admin.register(TextMessage)
class TextMessageAdmin(ImportExportModelAdmin):
    # Define a custom method to display the first 50 characters of the 'message' field
    def short_message(self, obj):
        if obj.message:
            url = reverse('admin:base_textmessage_change', args=[obj.id])
            return format_html('<a href="{}">{}</a>', url, obj.message[:50])
        else:
            return ''

    list_display = ('phone_number_id','phone_number', 'short_message', 'route', 'created_at', 'updated_at')
    list_filter = ('route', 'created_at', 'updated_at','phone_number_id')
    search_fields = ('phone_number__phone_number', 'message', 'messageuuid')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    list_per_page = 15

    # Set a user-friendly column name for the short_message method
    short_message.short_description = 'Message (First 50 Characters)'



from django.utils.html import format_html

@admin.register(PhoneNumber)
class PhoneNumberAdmin(ImportExportModelAdmin):
    list_display = ('id', 'get_decrypted_phone_number', 'arm', 'get_decrypted_name', 'active', 'opted_in', 'created_at')
    exclude = ["phone_number_hash"]
    list_filter = ('arm', 'active', 'opted_in')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    form = PhoneNumberForm
    list_per_page = 15

    def get_decrypted_phone_number(self, obj):
        if obj.phone_number:
            decrypted_phone_number = decrypt_data(obj.phone_number, obj.phone_number_key.tobytes())
            return format_html('<span>{}</span>', decrypted_phone_number)
        else:
            return format_html('<span>{}</span>', '')
    get_decrypted_phone_number.short_description = 'Phone Number' 

    def get_decrypted_name(self, obj):
        if obj.name:
            decrypted_name = decrypt_data(obj.name, obj.name_key.tobytes())
            return format_html('<span>{}</span>', decrypted_name)
        else:
            return format_html('<span>{}</span>', '')
    get_decrypted_name.short_description = 'Name'

@admin.register(WeeklyTopic)
class WeeklyTopicAdmin(ImportExportModelAdmin):
    list_display = ('display_name', 'phone_number_id', 'created_at')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    list_per_page = 15

    def display_name(self, obj):
        return str(obj)
    display_name.short_description = 'Display Name'


@admin.register(MessageTracker)
class MessageTrackerAdmin(ImportExportModelAdmin):
    list_display = ('display_name', 'phone_number_id','week_no',
                    'sent_topic_selection_message','sent_goal_message','sent_info_message_1',
                    'sent_info_message_2','sent_info_message_3','sent_info_message_4',
                    'sent_info_message_5','sent_goal_feedback_message')
    list_filter = ('phone_number_id', 'week_no')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    list_per_page = 15

    def display_name(self, obj):
        return str(obj)
    display_name.short_description = 'Display Name'

@admin.register(ScheduledMessage)
class ScheduleMessageAdmin(ImportExportModelAdmin):
    list_display = ('get_topic_name', 'weekday', 'get_message', 'get_message_es', 'get_picklist')
    ordering = ('topic_id', 'weekday')
    def get_topic_name(self, obj):
        return obj.topic.name
    get_topic_name.short_description = 'Topic Name'

    def get_message(self, obj):
        return obj.message[:40] + '...' if obj.message else ''
    get_message.short_description = 'Message'

    def get_message_es(self, obj):
        return obj.message_es[:40] + '...' if obj.message_es else ''
    get_message_es.short_description = 'Message ES'

    def get_picklist(self, obj):
        return obj.picklist[:40] + '...' if obj.picklist else ''
    get_picklist.short_description = 'Picklist'

@admin.register(ScheduledMessageControl)
class ScheduledMessageControlAdmin(ImportExportModelAdmin):
    list_display = ('get_topic_name','weekday', 'get_message', 'get_message_es',)
    ordering = ('topic_id', 'weekday')
    def get_topic_name(self, obj):
        return obj.topic.name
    get_topic_name.short_description = 'Topic Name'

    def get_message(self, obj):
        return obj.message[:40] + '...' if obj.message else ''
    get_message.short_description = 'Message'

    def get_message_es(self, obj):
        return obj.message_es[:40] + '...' if obj.message_es else ''
    get_message_es.short_description = 'Message ES'

@admin.register(TopicGoal)
class TopicGoalAdmin(ImportExportModelAdmin):
    list_display = ('get_topic_name', 'goal', 'goal_es', 'goal_feedback', 'goal_feedback_es')
    def get_topic_name(self, obj):
        return obj.topic.name
    get_topic_name.short_description = 'Topic Name'

@admin.register(Picklist)
class PicklistAdmin(ImportExportModelAdmin):
    list_display = ('display_name', 'phone_number_id','phone_number','context','language','created_at')
    list_filter = ('phone_number_id', 'context', 'language')
    date_hierarchy = 'created_at'
    list_per_page = 15
    def display_name(self, obj):
        return str(obj)
    display_name.short_description = 'Display Name'
