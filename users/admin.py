from django.contrib import admin

from users.models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'email', 'role', 'is_active', 'date_joined')
    search_fields = ('email', 'full_name')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'role')
    ordering = ('-date_joined',)

    @admin.display(description='Полное имя')
    def full_name(self, obj):
        return obj.full_name
