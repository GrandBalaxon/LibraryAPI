from rest_framework import status
from rest_framework.test import APITestCase
from users.models import CustomUser


class UserAPITest(APITestCase):
    """Тесты API для приложения users."""

    @classmethod
    def setUpTestData(cls):
        cls.register_url = '/api/user/register/'
        cls.token_url = '/api/user/token/'
        cls.list_url = '/api/user/'
        cls.me_url = '/api/user/me/'

        cls.reader = CustomUser.objects.create_user(
            email="reader@test.ru",
            password="password123",
            first_name="Иван",
            last_name="Иванов",
            phone_number="+7 (999) 111-22-33",
            place_of_birth="Москва",
            role=CustomUser.Role.READER
        )
        cls.librarian = CustomUser.objects.create_user(
            email="lib@test.ru",
            password="password123",
            first_name="Петр",
            last_name="Петров",
            phone_number="+7 (999) 444-55-66",
            place_of_birth="Москва",
            role=CustomUser.Role.LIBRARIAN
        )

    # ---------- Хелперы: аутентификация ----------
    def login_reader(self) -> None:
        """Аутентифицировать клиент как читателя."""
        self.client.force_authenticate(self.reader)

    def login_librarian(self) -> None:
        """Аутентифицировать клиент как библиотекаря."""
        self.client.force_authenticate(self.librarian)

    def logout(self) -> None:
        """Сбросить аутентификацию клиента."""
        self.client.force_authenticate(None)

    # ---------- Тесты ----------

    def test_login_get_jwt(self):
        """Получение JWT токена."""
        data = {"email": "reader@test.ru", "password": "password123"}
        response = self.client.post(self.token_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.json())
        self.assertIn('refresh', response.json())

    # --- Создание ---

    def test_register_user_success(self):
        """Успешная регистрация нового пользователя."""
        data = {
            "email": "new@test.ru", "password": "newpassword123",
            "first_name": "Новый", "last_name": "Юзер",
            "phone_number": "89998887766", "place_of_birth": "СПБ"
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = CustomUser.objects.get(email="new@test.ru")
        # Проверка нормализации
        self.assertEqual(user.phone_number, "+7 (999) 888-77-66")
        # Проверка хеширования
        self.assertNotEqual(user.password, "newpassword123")

    def test_register_user_invalid_phone(self):
        """Регистрация с невалидным телефоном должна вернуть 400."""
        data = {
            "email": "bad@test.ru", "password": "newpassword123",
            "first_name": "Новый", "last_name": "Юзер",
            "phone_number": "12345", "place_of_birth": "СПБ"
        }
        response = self.client.post(self.register_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('phone_number', response.json())
        self.assertEqual(response.json()['phone_number'][0], 'Некорректный номер телефона.')

    def test_register_user_with_change_reason_does_not_crash(self):
        """Проверяем, что лишнее поле change_reason при регистрации не ломает UserSerializer.create()."""
        data = {
            "email": "new_with_reason@test.ru", "password": "password123",
            "first_name": "Новый", "last_name": "Юзер",
            "phone_number": "89998887777", "place_of_birth": "СПБ",
            "change_reason": "Регистрация с причиной"
        }
        response = self.client.post(self.register_url, data=data, format='json')
        # Ожидаем 201, так как create() должен был сделать pop('change_reason')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # --- Чтение ---

    def test_get_my_profile(self):
        """Получение своего профиля через me."""
        self.login_reader()

        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['email'], "reader@test.ru")

    def test_librarian_can_list_users(self):
        """Библиотекарь может видеть список всех пользователей."""
        self.login_librarian()

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

    def test_reader_cannot_list_users(self):
        """Читатель не может видеть список всех пользователей."""
        self.login_reader()

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- Обновление ---

    def test_update_own_profile(self):
        """Пользователь может обновить свой профиль."""
        self.login_reader()

        url = f"{self.list_url}{self.reader.id}/"
        response = self.client.patch(url, {"first_name": "Обновленный"}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.reader.refresh_from_db()
        self.assertEqual(self.reader.first_name, "Обновленный")

    def test_update_own_password(self):
        """Пользователь может обновить свой пароль (покрываем UserSerializer.update)."""
        self.login_reader()

        url = f"{self.list_url}{self.reader.id}/"
        response = self.client.patch(url, {"password": "newsuperpassword"}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.reader.refresh_from_db()
        self.assertTrue(self.reader.check_password("newsuperpassword"))

    def test_update_email_without_reason_fails(self):
        """Нельзя изменить email (критичное поле) без указания причины."""
        self.login_reader()
        url = f"{self.list_url}{self.reader.id}/"

        response = self.client.patch(url, {"email": "new_email@test.ru"}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('change_reason', response.json())

    def test_update_phone_without_reason_fails(self):
        """Нельзя изменить телефон (критичное поле) без указания причины."""
        self.login_reader()
        url = f"{self.list_url}{self.reader.id}/"

        response = self.client.patch(url, {"phone_number": "+7 (999) 000-00-00"}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('change_reason', response.json())

    def test_update_critical_field_with_reason_succeeds(self):
        """Можно изменить email с указанием причины, и она попадёт в историю."""
        self.login_reader()
        url = f"{self.list_url}{self.reader.id}/"

        data = {
            "email": "updated_email@test.ru",
            "change_reason": "Смена основной почты"
        }
        response = self.client.patch(url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что email действительно обновился
        self.reader.refresh_from_db()
        self.assertEqual(self.reader.email, "updated_email@test.ru")

        # Проверяем, что причина записалась в историю (django-simple-history)
        latest_history = self.reader.history.first()
        self.assertEqual(latest_history.history_change_reason, "Смена основной почты")

    # --- Удаление (Мягкое списание) ---

    def test_librarian_can_deactivate_user(self):
        """Библиотекарь может деактивировать пользователя (Soft Delete)."""
        self.login_librarian()

        url = f"{self.list_url}{self.reader.id}/"
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.reader.refresh_from_db()
        self.assertFalse(self.reader.is_active)
