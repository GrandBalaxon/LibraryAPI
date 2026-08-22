from django.contrib import admin

from users.models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'username', 'role', 'is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('email', 'username')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'role')
    ordering = ('-date_joined',)
