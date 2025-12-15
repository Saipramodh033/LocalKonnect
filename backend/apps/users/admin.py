from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserActivity


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'user_type', 'is_email_verified', 'is_active', 'created_at']
    list_filter = ['user_type', 'is_email_verified', 'is_verified_reviewer', 'is_flagged', 'is_suspended']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number', 'avatar', 'bio')}),
        ('User Type', {'fields': ('user_type',)}),
        ('Location', {'fields': ('location', 'address', 'city', 'state', 'country', 'postal_code')}),
        ('Verification', {'fields': ('is_email_verified', 'is_phone_verified', 'is_verified_reviewer', 'reviewer_weight')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Moderation', {'fields': ('is_flagged', 'flag_reason', 'is_suspended', 'suspension_reason')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'user_type', 'password1', 'password2'),
        }),
    )


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'activity_type', 'ip_address', 'created_at']
    list_filter = ['activity_type', 'created_at']
    search_fields = ['user__email', 'ip_address']
    ordering = ['-created_at']
    readonly_fields = ['user', 'activity_type', 'ip_address', 'user_agent', 'metadata', 'created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
