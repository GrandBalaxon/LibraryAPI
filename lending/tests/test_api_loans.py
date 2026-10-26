from datetime import timedelta

from django.utils import timezone

from catalog.tests.base import BaseAPITestCase
from lending.models import BookLoan


class BookLoanAPITest(BaseAPITestCase):
    """Тесты API для выдачи и возврата книг."""

    def setUp(self):
        super().setUp()
        self.url = '/api/lending/'

        # Создаем активную выдачу для тестов на возврат
        self.active_loan = BookLoan.objects.create(
            user=self.user_reader,
            book_copy=self.copy_hobbit,
            loan_period_days=30,
            due_date=timezone.localdate() + timedelta(days=30),
            status=BookLoan.Status.ACTIVE
        )
        self.active_loan_details_url = f"{self.url}{self.active_loan.id}/"

        self.data = {
            'user_id': self.user_reader.id,
            'book_copy_id': self.copy1.id,
            'loan_period_days': 14,
        }
