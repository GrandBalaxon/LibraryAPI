from rest_framework.test import APITestCase

from catalog.models import Author
from users.models import CustomUser


class HistoryTest(APITestCase):
    """Тесты для проверки работы django-simple-history."""

    def setUp(self):
        # Создаем пользователя, от имени которого будем делать изменения
        self.user = CustomUser.objects.create_user(
            email="admin@test.ru",
            password="password123",
            first_name="Админ",
            last_name="Админов",
            phone_number="+7 (999) 000-00-00",
            place_of_birth="Москва",
            role=CustomUser.Role.LIBRARIAN
        )
        self.client.force_authenticate(self.user)

    def test_history_created_on_object_creation(self):
        """Проверяем, что при создании автора появляется запись в истории."""
        author = Author.objects.create(
            first_name="Эрик",
            last_name="Блэр"
        )

        # Проверяем, что у автора есть ровно 1 запись в истории
        self.assertEqual(author.history.count(), 1)

        # Проверяем тип изменения (создание)
        history_record = author.history.first()
        self.assertEqual(history_record.history_type, '+')
        self.assertEqual(history_record.first_name, "Эрик")

    def test_history_created_on_object_update(self):
        """Проверяем, что при обновлении автора создается новая запись в истории."""
        author = Author.objects.create(
            first_name="Эрик",
            last_name="Блэр"
        )

        # Обновляем автора
        author.first_name = "Джордж"
        author.save()

        # Теперь записей должно быть 2 (создание + обновление)
        self.assertEqual(author.history.count(), 2)

        # Самая свежая запись (first() берет последнюю) должна иметь тип '~' (update)
        latest_record = author.history.first()
        self.assertEqual(latest_record.history_type, '~')
        self.assertEqual(latest_record.first_name, "Джордж")

    def test_history_user_is_tracked(self):
        """Проверяем, что система запоминает, КТО сделал изменение (через middleware)."""
        # Чтобы middleware сработал, делаем запрос через API
        from rest_framework.test import APIClient
        client = APIClient()
        client.force_authenticate(self.user)

        # Создаем автора через API (чтобы сработал middleware)
        response = client.post(
            '/api/catalog/authors/',
            {
                "first_name": "Тест",
                "last_name": "Истории"
            },
            format='json'
        )

        author_id = response.json()['id']
        author = Author.objects.get(id=author_id)

        # Проверяем, что в истории записался именно наш пользователь
        history_record = author.history.first()
        self.assertEqual(history_record.history_user, self.user)
        self.assertEqual(history_record.history_user.email, "admin@test.ru")
