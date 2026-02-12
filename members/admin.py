from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Member

@admin.register(Member)
class MemberAdmin(UserAdmin):
    model = Member

    list_display = (
        "email",
        "username",
        "full_name",
        "email_verified",
        "is_staff",
        "is_active",
    )

    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("username", "full_name", "first_name", "last_name")}),
        ("Verification", {"fields": ("email_verified",)}),
        ("Permissions", {"fields": ("is_staff", "is_active", "groups", "user_permissions")}),
        ("Important Dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email",
                "username",
                "full_name",
                "password1",
                "password2",
                "is_staff",
                "is_active",
            ),
        }),
    )
