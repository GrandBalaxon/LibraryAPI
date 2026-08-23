import re

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class CustomUserManager(BaseUserManager):
    """Кастомный менеджер для модели пользователя."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обязателен.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        # Суперпользователь автоматически становится библиотекарем
        extra_fields.setdefault('role', self.model.Role.LIBRARIAN)

        if not extra_fields.get('is_staff'):
            raise ValueError('Суперпользователь должен иметь is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Суперпользователь должен иметь is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """Кастомная модель пользователя."""
    class Role(models.TextChoices):
        READER = 'reader', 'Читатель'
        LIBRARIAN = 'librarian', 'Библиотекарь'

    username = None
    email = models.EmailField(unique=True, verbose_name='Email')

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.READER,
        verbose_name='Роль'
    )

    # Персональные данные пользователя
    first_name = models.CharField(max_length=150, verbose_name='Имя')
    middle_name = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name='Отчество',
        help_text='Указать при наличии')
    last_name = models.CharField(max_length=150, verbose_name='Фамилия')
    phone_number = models.CharField(max_length=20, unique=True, verbose_name='Номер телефона')
    place_of_birth = models.CharField(max_length=150, verbose_name='Город рождения')

    @property
    def full_name(self) -> str:
        """Возвращает полное имя пользователя."""
        return f'{self.last_name} {self.first_name} {self.middle_name or ""}'.strip()

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self) -> str:
        return f'{self.email} ({self.get_role_display()})'

    class Meta:
        db_table = 'users'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    @staticmethod
    def normalize_phone_number(phone: str) -> str | None:
        """
        Приводит российский номер телефона к формату +7 (XXX) XXX-XX-XX.
        Возвращает None, если номер некорректен.
        """
        # Удаляем всё, кроме цифр и '+'
        cleaned = re.sub(r'[^\d+]', '', phone)

        # Обрабатываем варианты начала
        if cleaned.startswith('8'):
            cleaned = '+7' + cleaned[1:]
        elif cleaned.startswith('7'):
            cleaned = '+' + cleaned
        elif cleaned.startswith('9') and len(cleaned) == 10:
            cleaned = '+7' + cleaned
        elif cleaned.startswith('+7'):
            pass  # уже корректное начало
        else:
            return None

        # Проверяем, что остались только цифры
        digits = re.sub(r'\D', '', cleaned)
        if len(digits) != 11 or not digits.startswith('7'):
            return None

        # Форматируем
        return f'+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}'

    def clean(self):
        super().clean()
        if self.phone_number:
            normalized = self.normalize_phone_number(self.phone_number)
            if normalized is None:
                raise ValidationError({'phone_number': 'Некорректный номер телефона.'})
            self.phone_number = normalized

    def save(self, *args, **kwargs):
        if self.phone_number:
            self.phone_number = self.normalize_phone_number(self.phone_number)
        super().save(*args, **kwargs)
