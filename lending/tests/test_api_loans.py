from datetime import timedelta
from unittest.mock import patch

from django.utils import timezone
from rest_framework import status

from catalog.models import BookCopy
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

    # --- Чтение и роли ---

    def test_anonymous_cannot_list_loans(self):
        """Аноним не может получить список выдач."""
        self.logout()
        response = self.client.get(self.url)
        self.assertIn(response.status_code, (401, 403))

    def test_reader_sees_only_own_loans(self):
        """Читатель видит только свои выдачи."""
        self.login_librarian()

        # Создаем выдачу для другого читателя (используем библиотекаря)
        data = {
            'user_id': self.user_librarian.id,
            'book_copy_id': self.copy2.id,
            'loan_period_days': 14,
        }
        response = self.client.post(self.url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Проверяем, что в БД появилась запись
        loan = BookLoan.objects.get(id=response.json()['id'])
        self.assertEqual(loan.user, self.user_librarian)
        self.assertEqual(loan.book_copy, self.copy2)
        self.assertEqual(loan.status, BookLoan.Status.ACTIVE)

        self.logout()

        self.login_reader()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        # Читатель должен видеть только 1 выдачу (свою, из setUp)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]['id'], self.active_loan.id)

    def test_librarian_sees_all_loans(self):
        """Библиотекарь видит все выдачи."""
        self.login_librarian()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        # Библиотекарь должен видеть все выдачи (в базе только 1 из setUp)
        self.assertEqual(len(data), 1)

    def test_anonymous_get_queryset_returns_empty(self):
        """Покрываем fallback return queryset.none() для анонимов."""
        self.logout()

        # Временно отключаем проверку прав, чтобы дойти до метода get_queryset
        with patch('lending.views.BookLoanViewSet.get_permissions', return_value=[]):
            response = self.client.get(self.url)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            # Должен вернуться пустой список
            self.assertEqual(response.json(), [])

    # --- Создание (Выдача) ---

    def test_librarian_can_create_loan(self):
        """Библиотекарь может выдать доступную книгу."""
        self.login_librarian()

        response = self.client.post(self.url, data=self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Проверяем, что в БД появилась запись
        loan = BookLoan.objects.get(id=response.json()['id'])
        self.assertEqual(loan.user, self.user_reader)
        self.assertEqual(loan.book_copy, self.copy1)
        self.assertEqual(loan.status, BookLoan.Status.ACTIVE)

        # Проверяем, что дата возврата рассчиталась правильно (сегодня + 14 дней)
        expected_due_date = timezone.localdate() + timedelta(days=14)
        self.assertEqual(loan.due_date, expected_due_date)

        # Проверяем, что копия книги сменила статус
        self.copy1.refresh_from_db()
        self.assertEqual(self.copy1.status, BookCopy.Status.BORROWED)

    def test_librarian_cannot_create_loan_for_borrowed_copy(self):
        """Нельзя выдать экземпляр, который уже выдан (BORROWED)."""
        self.login_librarian()

        bad_data = self.data.copy()
        bad_data['book_copy_id'] = self.copy_hobbit.id

        response = self.client.post(self.url, data=bad_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('book_copy_id', response.json())
        self.assertEqual(response.json()['book_copy_id'][0], "Данный экземпляр не доступен к выдаче.")

    def test_reader_cannot_create_loan(self):
        """Читатель не может создать выдачу."""
        self.login_reader()
        response = self.client.post(self.url, data=self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('lending.serializers.BookCopy.objects.select_for_update')
    def test_create_loan_race_condition(self, mock_select_for_update):
        """Покрываем защиту от Race Condition (вторую проверку внутри create)."""
        self.login_librarian()

        # 1. Настраиваем мок: говорим, что select_for_update вернет "занятую" копию
        # (хотя в базе self.copy1 сейчас AVAILABLE, мы имитируем, что кто-то успел его взять)
        fake_borrowed_copy = BookCopy(
            id=self.copy1.id,
            status=BookCopy.Status.BORROWED,
            edition=self.edition,
            inventory_number="fake-inv"
        )
        mock_select_for_update.return_value.get.return_value = fake_borrowed_copy

        # 2. Отправляем запрос на выдачу
        response = self.client.post(self.url, data=self.data, format='json')

        # 3. Ожидаем 400, так как вторая проверка (под блокировкой) поймала, что книга занята
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('book_copy_id', response.json())
        self.assertEqual(
            response.json()['book_copy_id'][0],
            "Данный экземпляр не доступен к выдаче."
        )

    # --- Возврат (Action: return_book) ---

    def test_librarian_can_return_book(self):
        """Библиотекарь может вернуть книгу."""
        self.login_librarian()

        return_url = f"{self.active_loan_details_url}return/"
        response = self.client.post(return_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем статус выдачи
        self.active_loan.refresh_from_db()
        self.assertEqual(self.active_loan.status, BookLoan.Status.RETURNED)
        self.assertIsNotNone(self.active_loan.returned_at)

        # Проверяем, что книга снова доступна
        self.copy_hobbit.refresh_from_db()
        self.assertEqual(self.copy_hobbit.status, BookCopy.Status.AVAILABLE)

    def test_librarian_cannot_return_already_returned_book(self):
        """Нельзя вернуть книгу, которая уже возвращена."""
        self.login_librarian()

        # Принудительно делаем выдачу возвращенной
        self.active_loan.status = BookLoan.Status.RETURNED
        self.active_loan.save(update_fields=['status'])

        return_url = f"{self.active_loan_details_url}return/"
        response = self.client.post(return_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['detail'], 'Книга уже возвращена.')

    def test_reader_cannot_return_book(self):
        """Читатель не может возвращать книги (только библиотекарь)."""
        self.login_reader()
        return_url = f"{self.active_loan_details_url}return/"
        response = self.client.post(return_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('lending.views.BookLoan.objects.select_for_update')
    def test_return_book_race_condition(self, mock_select_for_update):
        """Покрываем защиту от Race Condition (вторую проверку внутри транзакции)."""
        self.login_librarian()

        # Первая проверка (вне транзакции) пройдет, так как self.active_loan имеет статус ACTIVE
        # Но мы говорим моку, что внутри транзакции select_for_update вернет уже RETURNED объект
        mock_loan = BookLoan(
            id=self.active_loan.id,
            status=BookLoan.Status.RETURNED,
            book_copy=self.active_loan.book_copy
        )
        mock_select_for_update.return_value.get.return_value = mock_loan

        return_url = f"{self.active_loan_details_url}return/"
        response = self.client.post(return_url)

        # Ожидаем, что сработает вторая проверка и вернет 400
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['detail'], 'Книга уже возвращена.')

    def test_book_loan_history(self):
        """Проверяем, что при выдаче и возврате книги пишется аудит."""
        self.assertEqual(self.active_loan.history.count(), 1)

        self.active_loan.status = BookLoan.Status.RETURNED
        self.active_loan.save()

        self.assertEqual(self.active_loan.history.count(), 2)
        self.assertEqual(self.active_loan.history.first().history_type, '~')
        self.assertEqual(self.active_loan.history.first().status, BookLoan.Status.RETURNED)

    # --- Просрочка (is_overdue) ---

    def test_loan_is_not_overdue(self):
        """Выдача не просрочена, если due_date в будущем."""
        self.login_librarian()
        response = self.client.get(self.active_loan_details_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.json()['is_overdue'])

    def test_loan_is_overdue(self):
        """Выдача просрочена, если due_date в прошлом."""
        self.login_librarian()

        # Делаем дату возврата вчерашней
        self.active_loan.due_date = timezone.localdate() - timedelta(days=1)
        self.active_loan.save(update_fields=['due_date'])

        response = self.client.get(self.active_loan_details_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()['is_overdue'])

    def test_returned_loan_is_never_overdue(self):
        """Возвращенная книга не может быть просроченной, даже если due_date в прошлом."""
        self.login_librarian()

        # Делаем дату возврата вчерашней, но статус RETURNED
        self.active_loan.due_date = timezone.localdate() - timedelta(days=1)
        self.active_loan.status = BookLoan.Status.RETURNED
        self.active_loan.save(update_fields=['due_date', 'status'])

        response = self.client.get(self.active_loan_details_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.json()['is_overdue'])
