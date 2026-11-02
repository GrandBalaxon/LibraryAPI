from catalog.models import Work
from catalog.tests.base import BaseAPITestCase


class WorkAPITest(BaseAPITestCase):
    """Тесты API для модели произведений."""

    def setUp(self):
        super().setUp()
        self.url = '/api/catalog/works/'
        self.details_url = f"{self.url}{self.work.id}/"
        self.data = {
            'original_title': "Test Work",
            'original_language': "Английский",
            'writing_year': 1967,
            'description': "Описание тестового произведения.",
            'author_ids': [self.author.id],
            'genre_ids': [self.genre3.id],
        }

    # --- Чтение ---

    def test_list_works_reader_allowed(self):
        """Читатель может получить список произведений."""
        self.login_reader()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(work['original_title'] == 'Nineteen Eighty-Four' for work in response.json()))

    def test_list_works_librarian_allowed(self):
        """Библиотекарь может получить список произведений."""
        self.login_librarian()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_list_works_anonymous_not_allowed(self):
        """Аноним не может получить список произведений."""
        self.logout()
        response = self.client.get(self.url)
        self.assertIn(response.status_code, (401, 403))

    def test_reader_can_get_work_details(self):
        """Читатель может запросить детали произведения и увидеть вложенных авторов."""
        self.login_reader()
        response = self.client.get(self.details_url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['original_title'], 'Nineteen Eighty-Four')

        self.assertEqual(len(data['authors']), 1)
        self.assertEqual(data['authors'][0]['full_name'], 'Блэр Эрик Артур')
        self.assertEqual(data['genres'][0]['name'], 'Роман-антиутопия')

    def test_anonymous_cannot_get_work_details(self):
        """Аноним не может получить детали произведения."""
        self.logout()
        response = self.client.get(self.details_url)
        self.assertEqual(response.status_code, 401)

    # --- Создание ---

    def test_librarian_can_add_new_work(self):
        """Библиотекарь может добавить новое произведение с авторами и жанрами."""
        self.login_librarian()
        response = self.client.post(self.url, data=self.data, format='json')
        self.assertEqual(response.status_code, 201)

        created_id = response.json()['id']
        detail_response = self.client.get(f"{self.url}{created_id}/")
        data = detail_response.json()

        self.assertEqual(data['original_title'], 'Test Work')

        # Проверяем, что связи M2M установились
        self.assertEqual(data['authors'][0]['id'], self.author.id)
        self.assertEqual(data['genres'][0]['id'], self.genre3.id)

    def test_reader_cannot_add_new_work(self):
        """Читатель не может добавить произведение."""
        self.login_reader()
        response = self.client.post(self.url, data=self.data, format='json')
        self.assertEqual(response.status_code, 403)

    def test_anonymous_cannot_add_new_work(self):
        """Аноним не может добавить произведение."""
        self.logout()
        response = self.client.post(self.url, data=self.data, format='json')
        self.assertEqual(response.status_code, 401)

    # --- Обновление ---

    def test_librarian_can_update_work(self):
        """Библиотекарь может изменять произведение с изданными книгами, добавив причину своих изменений."""
        self.login_librarian()

        patch_data = {
            'original_title': 'Обновленное название',
            'change_reason': 'Просто захотелось...'
        }

        response = self.client.patch(self.details_url, data=patch_data, format='json')
        self.assertEqual(response.status_code, 200)

        self.work.refresh_from_db()
        self.assertEqual(self.work.original_title, 'Обновленное название')

    def test_librarian_can_update_work_without_any_book_copies_tied_to_it(self):
        """Библиотекарь может изменять произведение без изданных книг, НЕ добавив причину своих изменений."""
        self.login_librarian()

        # создаем новое произведение
        post_response = self.client.post(self.url, data=self.data, format='json')
        self.assertEqual(post_response.status_code, 201)

        # получаем url нового произведения
        new_work_id = post_response.json()['id']
        new_work_url = f"{self.url}{new_work_id}/"

        # Меняем данные нового произведения без указания причины
        new_data = {'original_title': 'Обновленный оригинальный тайтл'}
        patch_response = self.client.patch(new_work_url, data=new_data, format='json')
        self.assertEqual(patch_response.status_code, 200)

        # Проверяем, что в БД данные действительно поменялись
        new_work = Work.objects.get(id=new_work_id)
        self.assertEqual(new_work.original_title, 'Обновленный оригинальный тайтл')

    def test_librarian_cannot_update_work_without_a_change_reason(self):
        """Библиотекарь НЕ может изменять произведение с изданными книгами, НЕ добавив причину своих изменений."""
        self.login_librarian()

        patch_data = {'original_title': 'Обновленное название'}

        patch_response = self.client.patch(self.details_url, data=patch_data, format='json')

        self.assertEqual(patch_response.status_code, 400)
        self.assertIn('change_reason', patch_response.json())

    def test_reader_cannot_update_work(self):
        """Читатель не может менять произведение."""
        self.login_reader()
        response = self.client.patch(self.details_url, data={'original_title': 'Взлом'}, format='json')
        self.assertEqual(response.status_code, 403)

    # --- Удаление ---

    def test_librarian_cannot_delete_work_with_existing_editions(self):
        """Библиотекарь НЕ может удалить произведение, если у него есть издания."""
        self.login_librarian()
        response = self.client.delete(self.details_url)

        # 1. Проверяем статус-код, должно быть 400 BAD REQUEST
        self.assertEqual(response.status_code, 400)

        # 2. Проверяем текст ошибки
        self.assertEqual(
            response.json()['detail'],
            'Нельзя удалить произведение, так как у него есть издания (в том числе архивные).'
        )

        # 3. Проверяем, что запись осталась в БД
        self.assertTrue(Work.objects.filter(id=self.work.id).exists())

    def test_librarian_can_delete_work_without_editions(self):
        """Библиотекарь МОЖЕТ удалить произведение через API, если у него нет изданий."""
        self.login_librarian()

        # 1. Создаем новое произведение
        create_response = self.client.post(self.url, data=self.data, format='json')
        self.assertEqual(create_response.status_code, 201)

        created_work_id = create_response.json()['id']
        created_details_url = f"{self.url}{created_work_id}/"

        # 2. Пытаемся удалить только что созданное произведение
        delete_response = self.client.delete(created_details_url)

        # 3. Проверяем, что удаление прошло успешно (204 No Content)
        self.assertEqual(delete_response.status_code, 204)

        # 4. Проверяем, что запись физически удалена из БД
        self.assertFalse(Work.objects.filter(id=created_work_id).exists())

    def test_reader_cannot_delete_work(self):
        """Читатель не может удалять произведение."""
        self.login_reader()
        response = self.client.delete(self.details_url)
        self.assertEqual(response.status_code, 403)

    # --- Поиск (SearchFilter) ---

    def test_search_work_by_title(self):
        """Поиск по оригинальному названию произведения."""
        self.login_reader()
        response = self.client.get(self.url, {'search': 'Hobbit'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['original_title'], 'The Hobbit, or There and Back Again')

    def test_search_work_by_author_last_name(self):
        """Поиск по фамилии автора (тестируем связи)."""
        self.login_reader()
        response = self.client.get(self.url, {'search': 'Толкин'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['original_title'], 'The Hobbit, or There and Back Again')

    def test_search_work_by_genre_name(self):
        """Поиск по названию жанра."""
        self.login_reader()
        response = self.client.get(self.url, {'search': 'Детская литература'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    # --- Сортировка (OrderingFilter) ---

    def test_ordering_works_by_writing_year_asc(self):
        """Сортировка по году написания (по возрастанию)."""
        self.login_reader()
        response = self.client.get(self.url, {'ordering': 'writing_year'})
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data[0]['original_title'], 'The Hobbit, or There and Back Again')
        self.assertEqual(data[1]['original_title'], 'Nineteen Eighty-Four')

    def test_ordering_works_by_title_desc(self):
        """Сортировка по названию (по убыванию)."""
        self.login_reader()
        response = self.client.get(self.url, {'ordering': '-original_title'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]['original_title'], 'The Hobbit, or There and Back Again')
