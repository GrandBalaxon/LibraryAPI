from catalog.models import Book
from catalog.tests.base import BaseAPITestCase


class BookAPITest(BaseAPITestCase):
    """Тесты API для модели произведений."""

    def setUp(self):
        super().setUp()
        self.url = '/api/catalog/books/'
        self.details_url = f"{self.url}{self.book.id}/"
        self.data = {
            'title': 'Тестовое произведение',
            'original_title': "Test Work",
            'original_language': "Английский",
            'writing_year': 1967,
            'description': "Описание тестового произведения.",
            'author_ids': [self.author.id],
            'genre_ids': [self.genre3.id],
        }

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
        """Читатель может запросить детали книги и увидеть вложенных авторов."""
        self.login_reader()
        response = self.client.get(self.details_url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['title'], '1984')

        self.assertEqual(len(data['authors']), 1)
        self.assertEqual(data['authors'][0]['full_name'], 'Блэр Эрик Артур')
        self.assertEqual(data['genres'][0]['name'], 'Роман-антиутопия')

    def test_anonymous_cannot_get_book_details(self):
        """Аноним не может получить детали книги."""
        self.logout()
        response = self.client.get(self.details_url)
        self.assertEqual(response.status_code, 401)

    # --- Создание ---

    def test_librarian_can_add_new_book(self):
        """Библиотекарь может добавить новую книгу с авторами и жанрами."""
        self.login_librarian()
        response = self.client.post(self.url, data=self.data, format='json')
        self.assertEqual(response.status_code, 201)

        created_id = response.json()['id']
        detail_response = self.client.get(f"{self.url}{created_id}/")
        data = detail_response.json()

        self.assertEqual(data['title'], 'Тестовое произведение')
        # Проверяем, что связи M2M установились
        self.assertEqual(data['authors'][0]['id'], self.author.id)
        self.assertEqual(data['genres'][0]['id'], self.genre3.id)

    def test_reader_cannot_add_new_book(self):
        """Читатель не может добавить книгу."""
        self.login_reader()
        response = self.client.post(self.url, data=self.data, format='json')
        self.assertEqual(response.status_code, 403)

    def test_anonymous_cannot_add_new_book(self):
        """Аноним не может добавить книгу."""
        self.logout()
        response = self.client.post(self.url, data=self.data, format='json')
        self.assertEqual(response.status_code, 401)

    # --- Обновление ---

    def test_librarian_can_update_book(self):
        """Библиотекарь может изменять книгу."""
        self.login_librarian()
        patch_data = {'title': 'Обновленное название'}
        response = self.client.patch(self.details_url, data=patch_data, format='json')
        self.assertEqual(response.status_code, 200)

        self.book.refresh_from_db()
        self.assertEqual(self.book.title, 'Обновленное название')

    def test_reader_cannot_update_book(self):
        """Читатель не может менять книгу."""
        self.login_reader()
        response = self.client.patch(self.details_url, data={'title': 'Взлом'}, format='json')
        self.assertEqual(response.status_code, 403)

    # --- Удаление ---

    def test_librarian_can_delete_book(self):
        """Библиотекарь может удалить книгу."""
        self.login_librarian()
        # Обрати внимание: у книг нет бизнес-логики запрета удаления (в отличие от авторов)
        response = self.client.delete(self.details_url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Book.objects.filter(id=self.book.id).exists())

    def test_reader_cannot_delete_book(self):
        """Читатель не может удалять книгу."""
        self.login_reader()
        response = self.client.delete(self.details_url)
        self.assertEqual(response.status_code, 403)

    # --- Поиск (SearchFilter) ---

    def test_search_book_by_title(self):
        """Поиск по названию произведения."""
        self.login_reader()
        response = self.client.get(self.url, {'search': 'Хоббит'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['title'], 'Хоббит, или Туда и обратно')

    def test_search_book_by_author_last_name(self):
        """Поиск по фамилии автора (тестируем связи)."""
        self.login_reader()
        response = self.client.get(self.url, {'search': 'Толкин'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['title'], 'Хоббит, или Туда и обратно')

    def test_search_book_by_genre_name(self):
        """Поиск по названию жанра."""
        self.login_reader()
        # Ищем по жанру "Детская литература" (он есть у Хоббита)
        response = self.client.get(self.url, {'search': 'Детская литература'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    # --- Сортировка (OrderingFilter) ---

    def test_ordering_books_by_writing_year_asc(self):
        """Сортировка по году написания (по возрастанию)."""
        self.login_reader()
        # В базе: Хоббит (1937), 1984 (1948)
        response = self.client.get(self.url, {'ordering': 'writing_year'})
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data[0]['title'], 'Хоббит, или Туда и обратно')
        self.assertEqual(data[1]['title'], '1984')

    def test_ordering_books_by_title_desc(self):
        """Сортировка по названию (по убыванию)."""
        self.login_reader()
        # По убыванию алфавита: Х (Хоббит) идет после цифры 1 (1984), значит по убыванию Хоббит будет первым
        response = self.client.get(self.url, {'ordering': '-title'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]['title'], 'Хоббит, или Туда и обратно')
