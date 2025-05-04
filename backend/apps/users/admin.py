from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'auth_provider', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'auth_provider')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'company_name')}),
        (_('Authentication'), {'fields': ('auth_provider', 'auth_id', 'is_verified')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('date_joined',)}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'auth_provider', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    
    readonly_fields = ('date_joined',)
