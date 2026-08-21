from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """Кастомная модель пользователя."""
    class Role(models.TextChoices):
        READER = 'reader', 'Читатель'
        LIBRARIAN = 'librarian', 'Библиотекарь'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.READER,
        verbose_name='Роль'
    )

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'

    class Meta:
        db_table = 'users'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
