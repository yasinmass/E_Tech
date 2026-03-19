from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Site, Task, Attendance, WorkUpdate, Bill

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Role Info', {'fields': ('role', 'phone')}),
    )
    list_display = ['username', 'email', 'first_name', 'last_name', 'role']

admin.site.register(User, CustomUserAdmin)
admin.site.register(Site)
admin.site.register(Task)
admin.site.register(Attendance)
admin.site.register(WorkUpdate)
admin.site.register(Bill)
