from catalog.models import Genre
from catalog.tests.base import BaseAPITestCase


class GenreAPITest(BaseAPITestCase):
    """Тесты API для модели жанра."""

    def setUp(self):
        super().setUp()
        self.url = '/api/catalog/genres/'
        self.details_url = f"{self.url}{self.genre.id}/"
        self.data = {
            "name": "Научная фантастика"
        }

    # --- Чтение ---

    def test_list_genres_reader_allowed(self):
        """Читатель может получить список жанров."""
        self.login_reader()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(genre['name'] == 'Фэнтези' for genre in response.json()))

    def test_list_genres_librarian_allowed(self):
        """Библиотекарь может получить список жанров."""
        self.login_librarian()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_list_genres_anonymous_not_allowed(self):
        """Аноним не может получить список жанров."""
        self.logout()
        response = self.client.get(self.url)
        self.assertIn(response.status_code, (401, 403))

    def test_reader_can_get_genre_details(self):
        """Читатель может запросить детали жанра."""
        self.login_reader()
        response = self.client.get(self.details_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['name'], 'Роман-антиутопия')

    def test_anonymous_cannot_get_genre_details(self):
        """Аноним не может получить детали жанра."""
        self.logout()
        response = self.client.get(self.details_url)
        self.assertEqual(response.status_code, 401)

    # --- Создание ---

    def test_librarian_can_add_new_genre(self):
        """Библиотекарь может добавить новый жанр."""
        self.login_librarian()
        response = self.client.post(self.url, data=self.data, format='json')
        self.assertEqual(response.status_code, 201)

        created_id = response.json()['id']
        detail_response = self.client.get(f"{self.url}{created_id}/")
        self.assertEqual(detail_response.json()['name'], 'Научная фантастика')

    def test_reader_cannot_add_new_genre(self):
        """Читатель не может добавить жанр."""
        self.login_reader()
        response = self.client.post(self.url, data=self.data, format='json')
        self.assertEqual(response.status_code, 403)

    def test_anonymous_cannot_add_new_genre(self):
        """Аноним не может добавить жанр."""
        self.logout()
        response = self.client.post(self.url, data=self.data, format='json')
        self.assertEqual(response.status_code, 401)

    # --- Обновление ---

    def test_librarian_can_update_genre(self):
        """Библиотекарь может изменять данные жанра у которого есть экземпляры с указанием причины."""
        self.login_librarian()

        data = {**self.data, 'change_reason': 'Просто захотелось...'}

        patch_response = self.client.patch(self.details_url, data=data, format='json')
        self.assertEqual(patch_response.status_code, 200)

        self.genre.refresh_from_db()
        self.assertEqual(self.genre.name, 'Научная фантастика')

    def test_librarian_can_update_genre_without_copies_tied_to_it(self):
        """Библиотекарь может изменять данные жанра у которого нет экземпляров без указания причины."""
        self.login_librarian()

        # создаем новый жанр без привязанных к нему копий
        post_response = self.client.post(self.url, data=self.data, format='json')
        self.assertEqual(post_response.status_code, 201)

        # получаем url нового жанра
        new_genre_id = post_response.json()['id']
        new_genre_url = f"{self.url}{new_genre_id}/"

        # Меняем данные нового жанра без указания причины
        new_data = {'name': 'Обновленный жанр без книг'}
        patch_response = self.client.patch(new_genre_url, data=new_data, format='json')
        self.assertEqual(patch_response.status_code, 200)

        # Проверяем, что в БД данные действительно поменялись
        new_genre = Genre.objects.get(id=new_genre_id)
        self.assertEqual(new_genre.name, 'Обновленный жанр без книг')

    def test_librarian_cannot_update_genre_without_a_change_reason(self):
        """Библиотекарь НЕ может поменять данные жанра без указания причины изменения."""
        self.login_librarian()

        patch_response = self.client.patch(self.details_url, data=self.data, format='json')

        self.assertEqual(patch_response.status_code, 400)
        self.assertIn('change_reason', patch_response.json())

    def test_reader_cannot_update_genre(self):
        """Читатель не может менять жанр."""
        self.login_reader()
        response = self.client.patch(self.details_url, data=self.data, format='json')
        self.assertEqual(response.status_code, 403)

    def test_anonymous_cannot_update_genre(self):
        """Аноним не может менять жанр."""
        self.logout()
        response = self.client.patch(self.details_url, data=self.data, format='json')
        self.assertEqual(response.status_code, 401)

    # --- Удаление ---

    def test_librarian_can_delete_genre(self):
        """Библиотекарь может удалить жанр."""
        self.login_librarian()
        # В отличие от авторов, здесь нет бизнес-логики запрета удаления
        response = self.client.delete(self.details_url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Genre.objects.filter(id=self.genre.id).exists())

    def test_reader_cannot_delete_genre(self):
        """Читатель не может удалять жанр."""
        self.login_reader()
        response = self.client.delete(self.details_url)
        self.assertEqual(response.status_code, 403)

    def test_anonymous_cannot_delete_genre(self):
        """Аноним не может удалять жанр."""
        self.logout()
        response = self.client.delete(self.details_url)
        self.assertEqual(response.status_code, 401)

    # --- Поиск ---

    def test_search_genre_by_name(self):
        """Проверка поиска жанра по названию."""
        self.login_reader()
        response = self.client.get(self.url, {'search': 'Фэнтези'})
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'Фэнтези')
