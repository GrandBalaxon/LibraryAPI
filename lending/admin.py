from django.contrib import admin

from lending.models import BookLoan


@admin.register(BookLoan)
class BookLoanAdmin(admin.ModelAdmin):
    list_display = ('id', 'book', 'user', 'status', 'borrowed_at', 'is_overdue')
    list_filter = ('status', 'is_overdue')
