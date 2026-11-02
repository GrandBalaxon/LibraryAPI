from datetime import timedelta

from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.forms.models import ModelForm
from django.http import HttpRequest
from django.utils import timezone
from simple_history.admin import SimpleHistoryAdmin

from catalog.models import BookCopy
from lending.models import BookLoan


@admin.register(BookLoan)
class BookLoanAdmin(SimpleHistoryAdmin):
    list_display = ('id', 'book_copy', 'user', 'status', 'borrowed_at', 'is_overdue')
    list_filter = ('status',)
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'book_copy__edition__title',
                     'book_copy__edition__work__original_title', 'book_copy__inventory_number')
    date_hierarchy = 'borrowed_at'
    autocomplete_fields = ['user', 'book_copy']

    # Кастомные действия
    actions = ['return_books']

    def get_readonly_fields(self, request: HttpRequest, obj: BookLoan | None = None) -> tuple[str, ...]:
        readonly_fields = ('borrowed_at', 'returned_at', 'loan_period_days')
        # если объект уже создан
        if obj:
            readonly_fields += ('user', 'book_copy')
            if obj.status == BookLoan.Status.RETURNED:
                # Если книга уже возвращена, запрещаем менять статус обратно и менять due_date
                return readonly_fields + ('status', 'due_date',)
            # Если книга на руках, статус можно поменять на "Возвращена"
            return readonly_fields
        else:
            # При создании статус менять нельзя, он ставится автоматически
            return readonly_fields + ('status',)

    def save_model(self, request: HttpRequest, obj: BookLoan, form: ModelForm, change: bool) -> None:
        """При создании меняем статус копии книги на BORROWED (Выдана), при возврате на AVAILABLE (Доступна)."""

        # если новая запись выдачи книги
        if not change:
            try:
                loan_period_days = obj.loan_period_days
                due_date = obj.due_date

                with transaction.atomic():
                    book_copy: BookCopy = BookCopy.objects.select_for_update().get(pk=obj.book_copy_id)

                    if not book_copy.status == BookCopy.Status.AVAILABLE:
                        raise ValidationError("Данный экземпляр не доступен к выдаче.")

                    book_copy.status = BookCopy.Status.BORROWED
                    book_copy.save(update_fields=['status'])

                    # Расчет ожидаемой даты возврата книги
                    if not due_date:
                        due_date = timezone.localdate() + timedelta(days=loan_period_days)
                    obj.due_date = due_date
                    obj.status = BookLoan.Status.ACTIVE

            except ValidationError as e:
                self.message_user(request, str(e), level=messages.ERROR)
                return
        else:
            # Проверяем, меняется ли статус на RETURNED
            old_obj = BookLoan.objects.get(pk=obj.pk)

            # Если статус изменился с ACTIVE на RETURNED
            if old_obj.status == BookLoan.Status.ACTIVE and obj.status == BookLoan.Status.RETURNED:
                with transaction.atomic():
                    book_copy: BookCopy = BookCopy.objects.select_for_update().get(pk=obj.book_copy_id)
                    book_copy.status = BookCopy.Status.AVAILABLE
                    book_copy.save(update_fields=['status'])
                    obj.returned_at = obj.returned_at or timezone.now()

        super().save_model(request, obj, form, change)

    @admin.action(description='Вернуть выбранные книги')
    def return_books(self, request: HttpRequest, queryset) -> None:
        """Массовый возврат книг через админку."""
        updated_count = 0
        for loan in queryset.filter(status=BookLoan.Status.ACTIVE):
            with transaction.atomic():
                book_copy = BookCopy.objects.select_for_update().get(pk=loan.book_copy_id)
                book_copy.status = BookCopy.Status.AVAILABLE
                book_copy.save(update_fields=['status'])

                loan.status = BookLoan.Status.RETURNED
                loan.returned_at = timezone.now()
                loan.save(update_fields=['status', 'returned_at'])
                updated_count += 1

        self.message_user(request, f'Успешно возвращено книг: {updated_count}', level=messages.SUCCESS)
