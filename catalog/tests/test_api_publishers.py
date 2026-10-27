from catalog.models import Publisher
from catalog.tests.base import BaseAPITestCase


class PublisherAPITest(BaseAPITestCase):
    """Тесты API для модели издательства."""

    def setUp(self):
        super().setUp()
        self.url = '/api/catalog/publishers/'
        self.details_url = f"{self.url}{self.publisher.id}/"
        self.data = {
            "name": "Эксмо",
            "description": "Крупнейшее издательство России."
        }

    # --- Чтение ---

    def test_list_publishers_reader_allowed(self):
        """Читатель может получить список издательств."""
        self.login_reader()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(pub['name'] == 'Яуза' for pub in response.json()))

    def test_list_publishers_librarian_allowed(self):
        """Библиотекарь может получить список издательств."""
        self.login_librarian()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_list_publishers_anonymous_not_allowed(self):
        """Аноним не может получить список издательств."""
        self.logout()
        response = self.client.get(self.url)
        self.assertIn(response.status_code, (401, 403))

    def test_reader_can_get_publisher_details(self):
        """Читатель может запросить детали издательства."""
        self.login_reader()
        response = self.client.get(self.details_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['name'], 'Яуза')

    def test_anonymous_cannot_get_publisher_details(self):
        """Аноним не может получить детали издательства."""
        self.logout()
        response = self.client.get(self.details_url)
        self.assertEqual(response.status_code, 401)

    # --- Создание ---

    def test_librarian_can_add_new_publisher(self):
        """Библиотекарь может добавить новое издательство."""
        self.login_librarian()
        response = self.client.post(self.url, data=self.data, format='json')
        self.assertEqual(response.status_code, 201)

        created_id = response.json()['id']
        detail_response = self.client.get(f"{self.url}{created_id}/")
        self.assertEqual(detail_response.json()['name'], 'Эксмо')

    def test_reader_cannot_add_new_publisher(self):
        """Читатель не может добавить издательство."""
        self.login_reader()
        response = self.client.post(self.url, data=self.data, format='json')
        self.assertEqual(response.status_code, 403)

    def test_anonymous_cannot_add_new_publisher(self):
        """Аноним не может добавить издательство."""
        self.logout()
        response = self.client.post(self.url, data=self.data, format='json')
        self.assertEqual(response.status_code, 401)

    # --- Обновление ---

    def test_librarian_can_update_publisher(self):
        """Библиотекарь может изменять данные издательства."""
        self.login_librarian()
        patch_response = self.client.patch(self.details_url, data=self.data, format='json')
        self.assertEqual(patch_response.status_code, 200)

        self.publisher.refresh_from_db()
        self.assertEqual(self.publisher.name, 'Эксмо')

    def test_reader_cannot_update_publisher(self):
        """Читатель не может менять издательство."""
        self.login_reader()
        response = self.client.patch(self.details_url, data=self.data, format='json')
        self.assertEqual(response.status_code, 403)

    def test_anonymous_cannot_update_publisher(self):
        """Аноним не может менять издательство."""
        self.logout()
        response = self.client.patch(self.details_url, data=self.data, format='json')
        self.assertEqual(response.status_code, 401)

    # --- Удаление ---

    def test_librarian_can_delete_publisher(self):
        """Библиотекарь может удалить издательство."""
        self.login_librarian()
        # В отличие от авторов, здесь нет бизнес-логики запрета удаления
        response = self.client.delete(self.details_url)
        self.assertEqual(response.status_code, 400)

    def test_reader_cannot_delete_publisher(self):
        """Читатель не может удалять издательство."""
        self.login_reader()
        response = self.client.delete(self.details_url)
        self.assertEqual(response.status_code, 403)

    def test_anonymous_cannot_delete_publisher(self):
        """Аноним не может удалять издательство."""
        self.logout()
        response = self.client.delete(self.details_url)
        self.assertEqual(response.status_code, 401)

    def test_librarian_can_delete_publisher_without_editions(self):
        """Библиотекарь может удалить издательство, у которого нет выпущенных книг."""
        self.login_librarian()

        # 1. Создаем издательство через API (используя self.data из setUp)
        create_response = self.client.post(self.url, data=self.data, format='json')
        self.assertEqual(create_response.status_code, 201)

        created_id = create_response.json()['id']
        created_details_url = f"{self.url}{created_id}/"

        # 2. Удаляем его
        response = self.client.delete(created_details_url)

        # Проверяем, что удаление прошло успешно (204)
        self.assertEqual(response.status_code, 204)

        # Проверяем, что его физически нет в БД
        self.assertFalse(Publisher.objects.filter(id=created_id).exists())

    # --- Поиск ---

    def test_search_publisher_by_name(self):
        """Проверка поиска издательства по названию."""
        self.login_reader()
        response = self.client.get(self.url, {'search': 'АСТ'})
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'АСТ')
