from catalog.models import Edition, BookCopy
from catalog.tests.base import BaseAPITestCase


class EditionAPITest(BaseAPITestCase):
    """Тесты API для модели издания (Edition)."""

    def setUp(self):
        super().setUp()
        self.url = '/api/catalog/editions/'
        self.details_url = f"{self.url}{self.edition.id}/"
        self.data = {
            'work_id': self.work.id,
            'title': 'Новое издание 1984',
            'isbn': '978-3-16-148410-0',
            'publication_year': 2023,
            'language': 'Английский',
            'pages': 350,
            'publisher_ids': [self.publisher.id],
            'translator_ids': [self.translator.id],
        }

    # --- Чтение ---

    def test_list_editions_reader_allowed(self):
        """Читатель может получить список изданий."""
        self.login_reader()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(any(ed['isbn'] == '978-5-00155-298-7' for ed in data))

        # Проверяем наличие вычисляемых полей
        first_ed = next(ed for ed in data if ed['isbn'] == '978-5-00155-298-7')
        self.assertEqual(first_ed['copies_count'], 2)
        self.assertEqual(first_ed['available_copies_count'], 2)
        self.assertEqual(len(first_ed['copies']), 2)

    def test_reader_can_get_edition_details(self):
        """Читатель видит вложенные данные (произведение, издателей, переводчиков)."""
        self.login_reader()
        response = self.client.get(self.details_url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['title'], '1984')
        self.assertEqual(data['work']['original_title'], 'Nineteen Eighty-Four')
        self.assertEqual(data['publishers'][0]['name'], 'Яуза')
        self.assertEqual(data['translators'][0]['full_name'], 'Мизинина Ирина Николаевна')
        self.assertEqual(data['pages'], 320)

    def test_list_editions_anonymous_not_allowed(self):
        """Аноним не может получить список изданий."""
        self.logout()
        response = self.client.get(self.url)
        self.assertIn(response.status_code, (401, 403))

    # --- Создание ---

    def test_librarian_can_add_new_edition(self):
        """Библиотекарь может добавить новое издание с M2M связями."""
        self.login_librarian()
        response = self.client.post(self.url, data=self.data, format='json')
        self.assertEqual(response.status_code, 201)

        created_id = response.json()['id']
        detail_response = self.client.get(f"{self.url}{created_id}/")
        data = detail_response.json()

        self.assertEqual(data['title'], 'Новое издание 1984')
        self.assertEqual(data['isbn'], '978-3-16-148410-0')
        self.assertEqual(data['work']['id'], self.work.id)
        self.assertEqual(data['publishers'][0]['id'], self.publisher.id)
        self.assertEqual(data['copies_count'], 0)

    def test_reader_cannot_add_new_edition(self):
        """Читатель не может добавить издание."""
        self.login_reader()
        response = self.client.post(self.url, data=self.data, format='json')
        self.assertEqual(response.status_code, 403)

    # --- Обновление и Удаление ---

    def test_librarian_can_update_edition(self):
        """Библиотекарь может изменять издание."""
        self.login_librarian()
        patch_data = {'pages': 400}
        response = self.client.patch(self.details_url, data=patch_data, format='json')
        self.assertEqual(response.status_code, 200)

        self.edition.refresh_from_db()
        self.assertEqual(self.edition.pages, 400)

    def test_librarian_can_delete_edition(self):
        """Библиотекарь может удалить издание."""
        self.login_librarian()
        response = self.client.delete(self.details_url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Edition.objects.filter(id=self.edition.id).exists())

        # При удалении Edition каскадно удаляются и все его BookCopy
        self.assertFalse(BookCopy.objects.filter(edition_id=self.edition.id).exists())

    # --- Поиск и Сортировка ---

    def test_search_edition_by_isbn(self):
        """Поиск по ISBN."""
        self.login_reader()
        response = self.client.get(self.url, {'search': '978-5-00155'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['title'], '1984')

    def test_ordering_editions_by_publication_year(self):
        """Сортировка по году издания (по убыванию)."""
        self.login_reader()
        response = self.client.get(self.url, {'ordering': '-publication_year'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data[0]['publication_year'], 2020)  # 1984
        self.assertEqual(data[1]['publication_year'], 2013)  # Хоббит

    # --- Кастомный экшен: add_copies ---

    def test_librarian_can_add_copies(self):
        """
        Проверка эндпоинта добавления экземпляров.
        Проверяем и создание записей BookCopy, и автогенерацию инвентарных номеров.
        """
        self.login_librarian()

        # Изначально у edition (1984) есть 2 копии (созданы в BaseAPITestCase)
        # inventory_number: "978-5-00155-298-7-1" и "-2"

        url = f"{self.details_url}add_copies/"
        response = self.client.post(url, data={'count': 3}, format='json')

        self.assertEqual(response.status_code, 200)

        # Проверяем, что в базе теперь 5 копий (2 старые + 3 новые)
        self.assertEqual(BookCopy.objects.filter(edition=self.edition).count(), 5)

        # Проверяем, что сериализатор отдал обновленные счетчики
        data = response.json()
        self.assertEqual(data['copies_count'], 5)
        self.assertEqual(data['available_copies_count'], 5)  # Новые копии всегда available

        # Проверяем правильность сгенерированных инвентарных номеров
        # Старые заканчивались на -2. Новые должны быть -3, -4, -5.
        new_copies = BookCopy.objects.filter(edition=self.edition).order_by('-id')[:3]
        inv_numbers = [c.inventory_number for c in new_copies]

        self.assertIn('978-5-00155-298-7-3', inv_numbers)
        self.assertIn('978-5-00155-298-7-4', inv_numbers)
        self.assertIn('978-5-00155-298-7-5', inv_numbers)

    def test_add_copies_invalid_count(self):
        """Проверка валидации: count должен быть положительным числом."""
        self.login_librarian()
        url = f"{self.details_url}add_copies/"

        # Передаем строку
        response = self.client.post(url, data={'count': 'много'}, format='json')
        self.assertEqual(response.status_code, 400)

        # Передаем отрицательное число
        response = self.client.post(url, data={'count': -5}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_reader_cannot_add_copies(self):
        """Читатель не может генерировать новые экземпляры."""
        self.login_reader()
        url = f"{self.details_url}add_copies/"
        response = self.client.post(url, data={'count': 1}, format='json')
        self.assertEqual(response.status_code, 403)

    # --- Проверка валидации ISBN ---

    def test_create_edition_with_invalid_isbn_invalid_length_error(self):
        """API должно отклонять создание издания с невалидным ISBN (ошибка InvalidLength)."""
        self.login_librarian()

        # Берем наши обычные данные, но ломаем ISBN
        bad_data = self.data.copy()
        bad_data['isbn'] = "12345"

        response = self.client.post(self.url, data=bad_data, format='json')

        # Ожидаем 400 Bad Request
        self.assertEqual(response.status_code, 400)
        self.assertIn('isbn', response.json())
        self.assertIn(
            "Неверная длина ISBN. ISBN должен состоять из 10 или 13 цифр.",
            str(response.json()['isbn'])
        )

    def test_create_edition_with_invalid_isbn_invalid_checksum_error(self):
        """API должно отклонять создание издания с неверной контрольной суммой ISBN."""
        self.login_librarian()

        bad_data = self.data.copy()
        # Длина правильная (13 цифр), формат правильный, но последняя цифра не сходится (должна быть 0)
        bad_data['isbn'] = "9783161484101"

        response = self.client.post(self.url, data=bad_data, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertIn('isbn', response.json())
        self.assertIn(
            "Неверный ISBN. Последняя цифра (контрольная сумма) "
            "не совпадает с остальными. Проверьте введенные данные.",
            str(response.json()['isbn'])
        )

    def test_create_edition_with_invalid_isbn_invalid_format_error(self):
        """API должно отклонять создание издания с недопустимыми символами в ISBN."""
        self.login_librarian()

        bad_data = self.data.copy()
        # Используем буквы, которые stdnum не может распознать
        bad_data['isbn'] = "978-ABC-148410-0"

        response = self.client.post(self.url, data=bad_data, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertIn('isbn', response.json())
        self.assertIn(
            "Неверный формат ISBN. Разрешены только цифры, дефисы и пробелы. "
            "Убедитесь, что нет лишних букв или символов.",
            str(response.json()['isbn'])
        )

    def test_create_edition_with_invalid_isbn_invalid_component_error(self):
        """API должно отклонять создание издания с неверным префиксом ISBN."""
        self.login_librarian()

        bad_data = self.data.copy()
        # Валидный EAN-13 (контрольная сумма сходится), но префикс 123 не является ISBN (должно быть 978 или 979)
        bad_data['isbn'] = "1234567890128"

        response = self.client.post(self.url, data=bad_data, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertIn('isbn', response.json())
        self.assertIn(
            "Некорректная составная часть ISBN. "
            "Проверьте правильность префикса (например, 978 или 979) и региона.",
            str(response.json()['isbn'])
        )

    def test_create_edition_with_valid_isbn_formats_it(self):
        """API должно принимать валидный ISBN и сохранять его с дефисами."""
        self.login_librarian()

        # Отправляем валидный ISBN без дефисов
        good_data = self.data.copy()
        good_data['isbn'] = "9783161484100"

        response = self.client.post(self.url, data=good_data, format='json')

        self.assertEqual(response.status_code, 201)

        # Проверяем, что в БД он сохранился красиво (с дефисами)
        self.assertEqual(response.json()['isbn'], "978-3-16-148410-0")
