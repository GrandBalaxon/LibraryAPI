from datetime import timedelta

from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from catalog.models import BookEdition
from lending.models import BookLoan


@admin.register(BookLoan)
class BookLoanAdmin(admin.ModelAdmin):
    list_display = ('id', 'book', 'user', 'status', 'borrowed_at', 'is_overdue')
    list_filter = ('status',)
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'book__title', 'book__book__title')
    date_hierarchy = 'borrowed_at'
    autocomplete_fields = ['user', 'book']

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = ('borrowed_at', 'returned_at', 'status', 'loan_period_days')
        # если объект уже создан
        if obj:
            readonly_fields += ('user', 'book')
            if obj.status == BookLoan.Status.RETURNED:
                return readonly_fields + ('due_date',)
            return readonly_fields
        else:
            return readonly_fields

    def save_model(self, request, obj, form, change):
        """При создании уменьшаем available_copies у издания, при возврате увеличиваем."""

        # если новая запись выдачи книги
        if not change:
            try:
                loan_period_days = obj.loan_period_days
                due_date = obj.due_date

                with transaction.atomic():
                    book = BookEdition.objects.select_for_update().get(pk=obj.book_id)
                    if book.available_copies <= 0:
                        raise ValidationError("Нет доступных экземпляров")

                    book.available_copies -= 1
                    book.save(update_fields=['available_copies'])

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
            if old_obj.status != BookLoan.Status.RETURNED and obj.status == BookLoan.Status.RETURNED:
                with transaction.atomic():
                    book = BookEdition.objects.select_for_update().get(pk=obj.book_id)
                    book.available_copies += 1
                    book.save(update_fields=['available_copies'])
                    obj.returned_at = obj.returned_at or timezone.now()

        super().save_model(request, obj, form, change)
