from django.contrib import admin
from django.db import transaction
from django.utils import timezone

from catalog.models import BookEdition
from lending.models import BookLoan


@admin.register(BookLoan)
class BookLoanAdmin(admin.ModelAdmin):
    list_display = ('id', 'book', 'user', 'status', 'borrowed_at', 'is_overdue')
    list_filter = ('status',)
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'book__title', 'book__book__title')

    def save_model(self, request, obj, form, change):
        """При создании уменьшаем available_copies у издания, при возврате увеличиваем."""

        # если новая запись выдачи книги
        if not change:
            with transaction.atomic():
                book = BookEdition.objects.select_for_update().get(pk=obj.book_id)
                if book.available_copies <= 0:
                    raise ValueError("Нет доступных экземпляров")
                book.available_copies -= 1
                book.save(update_fields=['available_copies'])
                obj.status = BookLoan.Status.ACTIVE

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
