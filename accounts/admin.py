from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class LMSUserAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'library', 'role', 'membership_type', 'status', 'is_active')
    list_filter = ('library', 'role', 'membership_type', 'status')
    fieldsets = UserAdmin.fieldsets + (
        ('Library Info', {'fields': ('library', 'role', 'phone', 'membership_type', 'status', 'profile_photo')}),
    )
