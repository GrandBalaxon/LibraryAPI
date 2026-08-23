from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('id', 'full_name', 'email', 'phone_number', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'first_name', 'last_name', 'middle_name')
    ordering = ('-date_joined',)

    # Переопределяем поля для отображения в форме редактирования
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Личная информация', {'fields': ('first_name', 'last_name', 'middle_name', 'phone_number', 'place_of_birth')}),
        ('Права доступа', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'password1', 'password2',
                'first_name', 'last_name', 'middle_name',
                'phone_number', 'place_of_birth',
                'role', 'is_staff', 'is_superuser'
            ),
        }),
    )

    @admin.display(description='Полное имя')
    def full_name(self, obj):
        return obj.full_name
