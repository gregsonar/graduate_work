from django.contrib import admin

from notification.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'description',
        'created_at',
    )
    search_fields = ('title', 'description')
    list_filter = ('created_at',)



