from django.core.exceptions import ValidationError
from django.test import TestCase
from users.models import CustomUser


class CustomUserModelTest(TestCase):
    """Тесты для модели CustomUser."""

    def test_create_user_success(self):
        """Успешное создание обычного пользователя."""
        user = CustomUser.objects.create_user(
            email="test@test.ru", password="password123",
            first_name="Иван", last_name="Иванов",
            phone_number="+7 (999) 111-22-33", place_of_birth="Москва"
        )
        self.assertEqual(user.email, "test@test.ru")
        self.assertEqual(user.role, CustomUser.Role.READER)
        self.assertTrue(user.check_password("password123"))

    def test_create_user_without_email_raises_error(self):
        """Нельзя создать пользователя без email."""
        with self.assertRaises(ValueError):
            CustomUser.objects.create_user(email="", password="password123")

    def test_create_superuser_success(self):
        """Создание суперпользователя автоматически делает его библиотекарем."""
        admin = CustomUser.objects.create_superuser(
            email="admin@test.ru", password="password123",
            first_name="Админ", last_name="Админов",
            phone_number="+7 (999) 444-55-66", place_of_birth="Москва"
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertEqual(admin.role, CustomUser.Role.LIBRARIAN)

    def test_normalize_phone_number(self):
        """Проверка нормализации телефона."""
        # Валидные форматы
        self.assertEqual(CustomUser.normalize_phone_number("89111234567"), "+7 (911) 123-45-67")
        self.assertEqual(CustomUser.normalize_phone_number("79111234567"), "+7 (911) 123-45-67")
        self.assertEqual(CustomUser.normalize_phone_number("+79111234567"), "+7 (911) 123-45-67")
        self.assertEqual(CustomUser.normalize_phone_number("9111234567"), "+7 (911) 123-45-67")

        # Невалидные форматы
        self.assertIsNone(CustomUser.normalize_phone_number("12345"))
        self.assertIsNone(CustomUser.normalize_phone_number("+1 555 123 4567"))

    def test_save_normalizes_phone_number(self):
        """При сохранении модели телефон должен нормализоваться автоматически."""
        user = CustomUser.objects.create_user(
            email="test2@test.ru", password="password123",
            first_name="Петр", last_name="Петров",
            phone_number="89111234567", place_of_birth="Москва"
        )
        # В базу должен сохраниться уже нормализованный номер
        self.assertEqual(user.phone_number, "+7 (911) 123-45-67")

    def test_create_superuser_missing_staff_raises_error(self):
        """Попытка создать суперюзера без is_staff должна вызывать ValueError."""
        with self.assertRaises(ValueError):
            CustomUser.objects.create_superuser(
                email="admin_staff@test.ru", password="password123",
                first_name="Админ", last_name="Админов",
                phone_number="+7 (999) 000-00-01", place_of_birth="Москва",
                is_staff=False, is_superuser=True
            )

    def test_create_superuser_missing_superuser_raises_error(self):
        """Попытка создать суперюзера без is_superuser должна вызывать ValueError."""
        with self.assertRaises(ValueError):
            CustomUser.objects.create_superuser(
                email="admin_su@test.ru", password="password123",
                first_name="Админ", last_name="Админов",
                phone_number="+7 (999) 000-00-02", place_of_birth="Москва",
                is_staff=True, is_superuser=False
            )

    def test_full_name_property(self):
        """Проверка формирования полного имени (с отчеством и без)."""
        user1 = CustomUser(first_name="Иван", last_name="Иванов")
        self.assertEqual(user1.full_name, "Иванов Иван")

        user2 = CustomUser(first_name="Иван", last_name="Иванов", middle_name="Иванович")
        self.assertEqual(user2.full_name, "Иванов Иван Иванович")

    def test_normalize_phone_number_invalid_edges(self):
        """Проверка краевых случаев нормализации телефона."""
        # Срабатывает else: return None (неверный префикс)
        self.assertIsNone(CustomUser.normalize_phone_number("+11234567890"))

        # Срабатывает проверка длины: return None (начинается с +7, но цифр не 11)
        self.assertIsNone(CustomUser.normalize_phone_number("+791112345"))  # Короткий
        self.assertIsNone(CustomUser.normalize_phone_number("+791112345678"))  # Длинный

    def test_clean_method_invalid_phone(self):
        """Проверка, что метод clean() выбрасывает ValidationError при неверном телефоне."""
        user = CustomUser(
            email="clean@test.ru", password="password123",
            first_name="Иван", last_name="Иванов",
            phone_number="12345", place_of_birth="Москва"
        )

        # full_clean() запускает валидацию полей и метод clean()
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_clean_method_valid_phone(self):
        """Проверка, что clean() успешно нормализует телефон."""
        user = CustomUser(
            email="clean2@test.ru", password="password123",
            first_name="Иван", last_name="Иванов",
            phone_number="89111234567", place_of_birth="Москва"
        )
        user.clean()
        self.assertEqual(user.phone_number, "+7 (911) 123-45-67")
