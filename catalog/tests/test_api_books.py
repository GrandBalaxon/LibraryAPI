from catalog.tests.base import BaseAPITestCase


class BookAPITest(BaseAPITestCase):
    """Тесты API для модели издательства."""

    def setUp(self):
        super().setUp()
        self.url = '/api/catalog/books/'
        self.details_url = f"{self.url}{self.book.id}/"

    # --- Чтение ---

    def test_list_books_reader_allowed(self):
        """Читатель может получить список книг."""
        self.login_reader()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(book['title'] == '1984' for book in response.json()))

    def test_list_books_librarian_allowed(self):
        """Библиотекарь может получить список книг."""
        self.login_librarian()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_list_books_anonymous_not_allowed(self):
        """Аноним не может получить список книг."""
        self.logout()
        response = self.client.get(self.url)
        self.assertIn(response.status_code, (401, 403))

    def test_reader_can_get_book_details(self):
        """Читатель может запросить детали книги."""
        self.login_reader()
        response = self.client.get(self.details_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['title'], '1984')

    def test_anonymous_cannot_get_book_details(self):
        """Аноним не может получить детали книги."""
        self.logout()
        response = self.client.get(self.details_url)
        self.assertEqual(response.status_code, 401)