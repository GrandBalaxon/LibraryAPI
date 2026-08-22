from django.db import models

from catalog.models import BookEdition
from config import settings


class BookLoan(models.Model):
    """Запись о выдаче книги пользователю."""

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Выдана'
        RETURNED = 'returned', 'Возвращена'
        OVERDUE = 'overdue', 'Просрочена'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='loans',
        verbose_name='Читатель'
    )
    book = models.ForeignKey(
        BookEdition,
        on_delete=models.CASCADE,
        related_name='loans',
        verbose_name='Книга'
    )
    borrowed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата выдачи'
    )
    due_date = models.DateField(
        verbose_name='Срок возврата'
    )
    returned_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата фактического возврата'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name='Статус'
    )

    class Meta:
        verbose_name = 'Выдача книги'
        verbose_name_plural = 'Выдачи книг'
        ordering = ['-borrowed_at']

    def __str__(self):
        return f'{self.user} — {self.book} ({self.get_status_display()})'
