from datetime import timedelta
from django.utils import timezone
from catalog.tests.base import BaseAPITestCase
from lending.models import BookLoan


class BookLoanModelTest(BaseAPITestCase):
    """Тесты для модели BookLoan."""

    def test_book_loan_str_representation(self):
        """Проверяем строковое представление выдачи (покрываем __str__)."""
        loan = BookLoan.objects.create(
            user=self.user_reader,
            book_copy=self.copy1,
            due_date=timezone.localdate() + timedelta(days=30),
            status=BookLoan.Status.ACTIVE
        )

        # self.user_reader -> "user1@test.ru (Читатель)"
        # self.copy1 -> "1984 [978-5-00155-298-7-1]"
        # get_status_display() -> "Выдана"
        expected_str = f"{self.user_reader} — {self.copy1} (Выдана)"

        self.assertEqual(str(loan), expected_str)
