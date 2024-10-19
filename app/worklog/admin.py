from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from worklog.models import WorkLog, Leave
from userauths.models import User

class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'telegram_id', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'email', 'telegram_id')
    ordering = ('username',)
    filter_horizontal = ('groups', 'user_permissions')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'telegram_id')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'telegram_id', 'password1', 'password2'),
        }),
    )

class WorkLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'recorded_time', 'status', 'day_of_week', 'month', 'comment')
    list_filter = ('status', 'day_of_week', 'month', 'user')
    search_fields = ('user__username', 'status', 'comment')
    ordering = ('-recorded_time',)
    
class LeaveAdmin(admin.ModelAdmin):
    list_display = ('user', 'leave_date', 'reason')
    list_filter = ('user', 'leave_date', 'reason')
    search_fields = ('user__username', 'leave_date', 'reason')
    ordering = ('-leave_date',)

admin.site.register(User, UserAdmin)
admin.site.register(WorkLog, WorkLogAdmin)
admin.site.register(Leave, LeaveAdmin)

