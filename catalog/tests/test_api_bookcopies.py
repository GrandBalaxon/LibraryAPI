from catalog.models import BookCopy
from catalog.tests.base import BaseAPITestCase


class BookCopyAPITest(BaseAPITestCase):
    """Тесты API для модели экземпляра книги (BookCopy)."""

    def setUp(self):
        super().setUp()
        self.url = '/api/catalog/copies/'
        self.details_url = f"{self.url}{self.copy1.id}/"
        self.data = {
            'edition': self.edition.id,
            'inventory_number': '978-5-00155-298-7-3',
            'status': BookCopy.Status.AVAILABLE,
            'condition': BookCopy.Condition.NEW,
            'location': 'Зал 3, стеллаж 1',
        }

    # --- Чтение и Ролевая видимость ---

    def test_reader_sees_only_available_copies(self):
        """Читатель видит только доступные экземпляры."""
        self.login_reader()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        # В base.py у нас 2 доступные (copy1, copy2) и 1 выданная (copy_hobbit)
        self.assertEqual(len(data), 2)

        # Проверяем, что выданной книги нет в списке
        inventory_numbers = [c['inventory_number'] for c in data]
        self.assertNotIn(self.copy_hobbit.inventory_number, inventory_numbers)
        self.assertIn(self.copy1.inventory_number, inventory_numbers)

    def test_librarian_sees_all_copies(self):
        """Библиотекарь видит все экземпляры, включая выданные."""
        self.login_librarian()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        # Библиотекарь должен видеть все 3 экземпляра
        self.assertEqual(len(data), 3)

        inventory_numbers = [c['inventory_number'] for c in data]
        self.assertIn(self.copy_hobbit.inventory_number, inventory_numbers)

    # --- Фильтрация и Поиск ---

    def test_librarian_can_filter_by_status(self):
        """Библиотекарь может фильтровать по статусу."""
        self.login_librarian()
        response = self.client.get(self.url, {'status': BookCopy.Status.BORROWED})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['inventory_number'], self.copy_hobbit.inventory_number)

    def test_search_copy_by_inventory_number(self):
        """Поиск по инвентарному номеру."""
        self.login_reader()
        response = self.client.get(self.url, {'search': self.copy1.inventory_number})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['id'], self.copy1.id)

    def test_search_copy_by_work_title(self):
        """Поиск по названию произведения (через связи edition -> work)."""
        self.login_reader()
        response = self.client.get(self.url, {'search': 'Hobbit'})

        self.assertEqual(response.status_code, 200)
        # Читатель не должен найти "Хоббита", так как единственная копия выдана (BORROWED)
        self.assertEqual(len(response.json()), 0)

        # А библиотекарь должен найти
        self.login_librarian()
        response = self.client.get(self.url, {'search': 'Hobbit'})
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['inventory_number'], self.copy_hobbit.inventory_number)

    # --- Создание и Обновление ---

    def test_librarian_can_create_copy(self):
        """Библиотекарь может создать новый экземпляр."""
        self.login_librarian()
        response = self.client.post(self.url, data=self.data, format='json')
        self.assertEqual(response.status_code, 201)

        self.assertEqual(response.json()['inventory_number'], '978-5-00155-298-7-3')
        self.assertEqual(BookCopy.objects.count(), 4)

    def test_librarian_can_create_copy_without_inventory_number(self):
        """
        Если библиотекарь создает копию вручную и не указывает инвентарный номер,
        система должна сгенерировать его автоматически (как в add_copies).
        """
        self.login_librarian()

        # Данные без inventory_number
        data = {
            'edition': self.edition.id,
            'status': BookCopy.Status.AVAILABLE,
            'condition': BookCopy.Condition.NEW,
            'location': 'Зал 3, стеллаж 1',
        }

        response = self.client.post(self.url, data=data, format='json')

        # Ожидаем 201 Created
        self.assertEqual(response.status_code, 201)

        # Проверяем, что номер сгенерировался
        created_data = response.json()
        # В base.py у нас уже есть копии с номерами ...-1 и ...-2. Значит, новая должна получить ...-3
        self.assertEqual(created_data['inventory_number'], '978-5-00155-298-7-3')

    def test_reader_cannot_create_copy(self):
        """Читатель не может создать экземпляр."""
        self.login_reader()
        response = self.client.post(self.url, data=self.data, format='json')
        self.assertEqual(response.status_code, 403)

    def test_librarian_can_update_condition(self):
        """Библиотекарь может обновить состояние книги (например, потрепалась)."""
        self.login_librarian()
        response = self.client.patch(
            self.details_url,
            data={'condition': BookCopy.Condition.WORN},
            format='json'
        )
        self.assertEqual(response.status_code, 200)

        self.copy1.refresh_from_db()
        self.assertEqual(self.copy1.condition, BookCopy.Condition.WORN)

    # --- Удаление (Мягкое списание) ---

    def test_librarian_can_soft_delete_available_copy(self):
        """Библиотекарь может списать доступную книгу (Soft Delete)."""
        self.login_librarian()
        response = self.client.delete(self.details_url)

        # 1. Проверяем 204 No Content
        self.assertEqual(response.status_code, 204)

        # 2. Проверяем, что запись осталась в БД, но статус изменился
        self.copy1.refresh_from_db()
        self.assertEqual(self.copy1.status, BookCopy.Status.WRITTEN_OFF)
        self.assertTrue(BookCopy.objects.filter(id=self.copy1.id).exists())

    def test_librarian_cannot_soft_delete_borrowed_copy(self):
        """Нельзя списать книгу, которая выдана читателю."""
        self.login_librarian()

        url = f"{self.url}{self.copy_hobbit.id}/"
        response = self.client.delete(url)

        # 1. Ожидаем 400 Bad Request
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()['detail'],
            'Нельзя списать книгу, которая выдана читателю.'
        )

        # 2. Проверяем, что статус не изменился
        self.copy_hobbit.refresh_from_db()
        self.assertEqual(self.copy_hobbit.status, BookCopy.Status.BORROWED)
