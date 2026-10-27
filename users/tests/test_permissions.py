from django.test import TestCase
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from users.models import CustomUser
from users.permissions import IsLibrarian, IsLibrarianOrReadOnly, IsOwnerOrLibrarian
from users.views import UserViewSet


class UserPermissionsTest(TestCase):
    """Тесты для кастомных прав доступа."""

    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()

        cls.reader = CustomUser.objects.create_user(
            email="reader_perm@test.ru",
            password="password123",
            first_name="Иван",
            last_name="Иванов",
            phone_number="+7 (999) 111-22-33",
            place_of_birth="Москва",
            role=CustomUser.Role.READER
        )
        cls.librarian = CustomUser.objects.create_user(
            email="lib_perm@test.ru",
            password="password123",
            first_name="Петр",
            last_name="Петров",
            phone_number="+7 (999) 444-55-66",
            place_of_birth="Москва",
            role=CustomUser.Role.LIBRARIAN
        )

    def test_get_permissions_fallback(self):
        """
        Покрываем fallback в get_permissions.
        Проверяем, что для любых новых/неизвестных экшенов по умолчанию
        требуются права библиотекаря.
        """
        view = UserViewSet()

        # Симулируем действие, которого нет в списках if/elif (например, 'create')
        view.action = 'create'

        permissions = view.get_permissions()

        # Проверяем, что вернулись именно нужные классы прав
        self.assertEqual(len(permissions), 2)
        self.assertIsInstance(permissions[0], IsAuthenticated)
        self.assertIsInstance(permissions[1], IsLibrarian)

    def test_is_librarian(self):
        """IsLibrarian разрешает доступ только библиотекарям."""
        request = Request(self.factory.get('/'))

        request.user = self.reader
        self.assertFalse(IsLibrarian().has_permission(request, None))

        request.user = self.librarian
        self.assertTrue(IsLibrarian().has_permission(request, None))

    def test_is_librarian_or_read_only(self):
        """IsLibrarianOrReadOnly разрешает чтение всем, запись — только библиотекарям."""
        request_get = Request(self.factory.get('/'))
        request_post = Request(self.factory.post('/'))

        # Читатель (GET - можно, POST - нельзя)
        request_get.user = self.reader
        request_post.user = self.reader
        self.assertTrue(IsLibrarianOrReadOnly().has_permission(request_get, None))
        self.assertFalse(IsLibrarianOrReadOnly().has_permission(request_post, None))

        # Библиотекарь (GET - можно, POST - можно)
        request_get.user = self.librarian
        request_post.user = self.librarian
        self.assertTrue(IsLibrarianOrReadOnly().has_permission(request_get, None))
        self.assertTrue(IsLibrarianOrReadOnly().has_permission(request_post, None))

    def test_is_owner_or_librarian(self):
        """IsOwnerOrLibrarian разрешает менять свой профиль или библиотекарю любой."""
        request_get = Request(self.factory.get('/'))
        request_patch = Request(self.factory.patch('/'))

        # Читатель 1 пытается изменить Читателя 2
        request_patch.user = self.reader
        self.assertFalse(IsOwnerOrLibrarian().has_object_permission(request_patch, None, self.librarian))

        # Читатель 1 пытается изменить СЕБЯ
        self.assertTrue(IsOwnerOrLibrarian().has_object_permission(request_patch, None, self.reader))

        # Библиотекарь пытается изменить Читателя
        request_patch.user = self.librarian
        self.assertTrue(IsOwnerOrLibrarian().has_object_permission(request_patch, None, self.reader))

        # Методы SAFE_METHODS разрешены всем (для просмотра)
        request_get.user = self.reader
        self.assertTrue(IsOwnerOrLibrarian().has_object_permission(request_get, None, self.librarian))
