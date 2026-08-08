from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "get_full_name", "is_superadmin", "has_2fa", "is_active")
    list_filter = ("is_superadmin", "is_active", "is_staff")
    fieldsets = UserAdmin.fieldsets + (
        ("LabSaaS", {"fields": ("is_superadmin", "totp_secret")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("LabSaaS", {"fields": ("is_superadmin",)}),
    )
