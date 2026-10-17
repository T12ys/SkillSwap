from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'is_banned', 'is_superuser', 'date_joined')
    list_filter = ('role', 'is_banned', 'is_superuser')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('SkillSwap', {'fields': ('avatar', 'bio', 'role', 'is_banned')}),
    )

