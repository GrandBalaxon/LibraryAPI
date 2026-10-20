from catalog.models import Author
from catalog.tests.base import BaseAPITestCase


class AuthorAPITest(BaseAPITestCase):
    """Тесты API для модели автора."""

    def setUp(self):
        super().setUp()
        self.url = '/api/catalog/authors/'
        self.details_url = f"{self.url}{self.author.id}/"
        self.data = {
            "first_name": "Тест",
            "last_name": "Тестовый",
            "middle_name": "Тестович",
            "birth_date": "2006-10-19",
            "biography": "Тестовый автор."
        }

    def test_list_authors_reader_allowed(self):
        """Читатель может получить список авторов."""
        self.login_reader()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(author['last_name'] == 'Блэр' for author in response.json()))

    def test_list_authors_librarian_allowed(self):
        """Библиотекарь может получить список авторов."""
        self.login_librarian()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(author['last_name'] == 'Блэр' for author in response.json()))

    def test_list_authors_anonymous_not_allowed(self):
        """Анонимный пользователь не может получить список авторов."""
        self.logout()
        response = self.client.get(self.url)
        self.assertIn(response.status_code, (401, 403))

    def test_librarian_can_add_new_author(self):
        """Библиотекарь может добавить нового автора."""
        self.login_librarian()

        # Создаем автора
        response = self.client.post(self.url, data=self.data, format='json')
        self.assertEqual(response.status_code, 201)

        # Запрашиваем информацию о созданном авторе
        created_author_id = response.json()['id']
        detail_url = f"{self.url}{created_author_id}/"
        detail_response = self.client.get(detail_url)
        self.assertEqual(detail_response.status_code, 200)

        # Проверяем правильность данных
        author_data = detail_response.json()
        self.assertEqual(author_data['last_name'], 'Тестовый')
        self.assertEqual(author_data['first_name'], 'Тест')
        self.assertEqual(author_data['pseudonym'], None)
        self.assertEqual(author_data['books_written'], 0)

    def test_reader_cannot_add_new_author(self):
        """Читатель не может добавить нового автора."""
        self.login_reader()
        response = self.client.post(self.url, data=self.data, format='json')
        self.assertEqual(response.status_code, 403)

    def test_anonymous_cannot_add_new_author(self):
        """Анонимный пользователь не может добавить автора."""
        self.logout()
        response = self.client.post(self.url, data=self.data, format='json')
        self.assertEqual(response.status_code, 401)

    def test_reader_can_get_author_details(self):
        """Читатель может запросить информацию об авторе."""
        self.login_reader()
        details_response = self.client.get(self.details_url)
        self.assertEqual(details_response.status_code, 200)
        author_data = details_response.json()
        self.assertEqual(author_data['first_name'], 'Эрик')

    def test_anonymous_cannot_get_author_details(self):
        """Аноним не может получить деталей об авторе."""
        self.logout()
        detail_response = self.client.get(self.details_url)
        self.assertEqual(detail_response.status_code, 401)

    def test_librarian_can_update_author_details(self):
        """Библиотекарь может изменять данные автора."""
        self.login_librarian()

        # проверка старых данных
        details_response = self.client.get(self.details_url)
        author_data = details_response.json()
        self.assertEqual(author_data['first_name'], 'Эрик')

        # обновление данных
        patch_response = self.client.patch(self.details_url, data=self.data, format='json')
        self.assertEqual(patch_response.status_code, 200)

        # проверка измененных данных автора
        updated_details_response = self.client.get(self.details_url)
        updated_author_data = updated_details_response.json()
        self.assertEqual(updated_author_data['first_name'], 'Тест')

    def test_reader_cannot_update_author_details(self):
        """Читатель не может менять данные автора."""
        self.login_reader()
        patch_response = self.client.patch(self.details_url, data=self.data, format='json')
        self.assertEqual(patch_response.status_code, 403)

    def test_anonymous_cannot_update_author_details(self):
        """Анонимус не может менять данные автора."""
        self.logout()
        patch_response = self.client.patch(self.details_url, data=self.data, format='json')
        self.assertEqual(patch_response.status_code, 401)

    def test_anonymous_cannot_delete_author_details(self):
        """Аноним не может удалять автора книг."""
        self.logout()
        deletion_response = self.client.delete(self.details_url)
        self.assertEqual(deletion_response.status_code, 401)

    def test_reader_cannot_delete_author_details(self):
        """Читатель не может удалять автора книг."""
        self.login_reader()
        deletion_response = self.client.delete(self.details_url)
        self.assertEqual(deletion_response.status_code, 403)

    def test_librarian_can_delete_author_with_no_book_editions(self):
        """
        Библиотекарь может удалить автора, если у оного нет никаких связанных с ним книг,
        копии которых находятся в библиотеке или на руках читателей.
        """
        self.login_librarian()

        # Создаем автора без книг
        response = self.client.post(self.url, data=self.data, format='json')
        self.assertEqual(response.status_code, 201)

        # Получаем url созданного автора
        created_author_id = response.json()['id']
        created_author_url = f"{self.url}{created_author_id}/"

        # Успешно удаляем автора
        deletion_response = self.client.delete(created_author_url)
        self.assertEqual(deletion_response.status_code, 204)

        # Проверяем, что автора нет в БД, 404 NOT FOUND
        after_delete_response = self.client.get(created_author_url)
        self.assertEqual(after_delete_response.status_code, 404)

    def test_librarian_cannot_delete_author_with_book_editions(self):
        """
        Библиотекарь НЕ может просто взять и удалить автора у которого есть книги, экземпляры которых уже
        представлены в библиотеке или находятся на руках у читателей.

        То есть у автора есть написанные им произведения (Books), у которых есть книги (BookEditions), находящиеся
        в датабазе библиотеки и их количество (total_copies) не равно нулю.
        """
        self.login_librarian()

        # Проверяем, что автор существует до удаления
        response = self.client.get(self.details_url)
        self.assertEqual(response.status_code, 200)

        # Пытаемся удалить автора
        deletion_response = self.client.delete(self.details_url)

        # Ожидаем 400 (Bad Request), так как удаление должно быть заблокировано
        self.assertEqual(deletion_response.status_code, 400)

        # Проверяем, что автор остался в базе данных
        self.assertTrue(Author.objects.filter(id=self.author.id).exists())
