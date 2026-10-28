from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from catalog.models import Work, Edition, BookCopy
from lending.models import BookLoan
from users.models import CustomUser


class BookLoanModelTest(TestCase):
    """Изолированные тесты для модели BookLoan."""

    @classmethod
    def setUpTestData(cls):
        """Создаем минимальный набор данных только для модели."""
        cls.user = CustomUser.objects.create_user(
            email="test@test.ru",
            password="password123",
            first_name="Иван",
            last_name="Иванов",
            phone_number="+7 (999) 111-22-33",
            place_of_birth="Москва"
        )

        cls.work = Work.objects.create(
            original_title="1984",
            original_language="Рус"
        )
        cls.edition = Edition.objects.create(
            work=cls.work,
            title="1984",
            publication_year=2020,
            language="Рус",
            pages=320
        )
        cls.copy = BookCopy.objects.create(
            edition=cls.edition,
            inventory_number="INV-TEST-1"
        )

    def test_book_loan_str_representation(self):
        """Проверяем строковое представление выдачи (покрываем __str__)."""
        loan = BookLoan.objects.create(
            user=self.user,
            book_copy=self.copy,
            due_date=timezone.localdate() + timedelta(days=30),
            status=BookLoan.Status.ACTIVE
        )

        # Ожидаем: "test@test.ru (Читатель) — 1984 [INV-TEST-1] (Выдана)"
        expected_str = f"{self.user} — {self.copy} (Выдана)"
        self.assertEqual(str(loan), expected_str)

    def test_book_loan_history(self):
        """Проверяем, что при создании и изменении пишется аудит."""
        loan = BookLoan.objects.create(
            user=self.user,
            book_copy=self.copy,
            due_date=timezone.localdate() + timedelta(days=30),
            status=BookLoan.Status.ACTIVE
        )

        # 1. Проверяем историю создания
        self.assertEqual(loan.history.count(), 1)

        # 2. Возвращаем книгу
        loan.status = BookLoan.Status.RETURNED
        loan.save()

        # 3. Проверяем историю изменения
        self.assertEqual(loan.history.count(), 2)
        latest_record = loan.history.first()
        self.assertEqual(latest_record.history_type, '~')
        self.assertEqual(latest_record.status, BookLoan.Status.RETURNED)
