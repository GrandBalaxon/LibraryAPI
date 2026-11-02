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

    # --- Чтение ---

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

    # --- Создание ---

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
        self.assertEqual(author_data['works_written'], 0)

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

    # --- Обновление ---

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

    def test_librarian_must_provide_reason_to_change_name(self):
        """Нельзя изменить имя автора без указания причины."""
        self.login_librarian()

        # 1. Пытаемся изменить имя без причины
        patch_data_first = {'first_name': 'Новое имя'}
        response_first = self.client.patch(self.details_url, data=patch_data_first, format='json')
        self.assertEqual(response_first.status_code, 400)
        self.assertIn('change_reason', response_first.json())

        # 2. Пытаемся изменить фамилию без причины
        patch_data_last = {'last_name': 'Новая фамилия'}
        response_last = self.client.patch(self.details_url, data=patch_data_last, format='json')
        self.assertEqual(response_last.status_code, 400)

        # 3. Пытаемся изменить отчество без причины
        patch_data_middle = {'middle_name': 'Новое отчество'}
        response_middle = self.client.patch(self.details_url, data=patch_data_middle, format='json')
        self.assertEqual(response_middle.status_code, 400)

    def test_librarian_can_change_name_with_reason(self):
        """Можно изменить имя, если указана причина."""
        self.login_librarian()

        # Меняем фамилию и указываем причину
        patch_data = {
            'last_name': 'Новая фамилия',
            'change_reason': 'Опечатка в старой фамилии'
        }
        response = self.client.patch(self.details_url, data=patch_data, format='json')

        self.assertEqual(response.status_code, 200)

        # Проверяем, что в истории сохранилась наша причина!
        self.author.refresh_from_db()
        latest_history = self.author.history.first()
        self.assertEqual(latest_history.last_name, 'Новая фамилия')
        self.assertEqual(latest_history.history_change_reason, 'Опечатка в старой фамилии')

    # --- Удаление ---

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

    # --- Сортировка и Поиск ---

    def test_search_author_by_pseudonym(self):
        """Проверка поиска автора по псевдониму (SearchFilter)."""
        self.login_reader()
        # Ищем "Оруэлл". В базе это псевдоним Эрика Блэра.
        response = self.client.get(self.url, {'search': 'Оруэлл'})

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Должен вернуться только один автор
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['last_name'], 'Блэр')
        self.assertEqual(data[0]['pseudonym'], 'Джордж Оруэлл')

    def test_search_author_by_last_name(self):
        """Проверка поиска автора по фамилии (SearchFilter)."""
        self.login_reader()
        response = self.client.get(self.url, {'search': 'Толкин'})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['first_name'], 'Джон')

    def test_search_author_not_found(self):
        """Поиск несуществующего автора возвращает пустой список."""
        self.login_reader()
        response = self.client.get(self.url, {'search': 'Гарри Поттер'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

    def test_ordering_authors_by_last_name_desc(self):
        """Проверка сортировки по фамилии (по убыванию)."""
        self.login_reader()
        # В базе: Блэр, Мизинина, Рахманова, Толкин.
        # По убыванию первым должен идти Толкин.
        response = self.client.get(self.url, {'ordering': '-last_name'})

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data[0]['last_name'], 'Толкин')
        self.assertEqual(data[-1]['last_name'], 'Блэр')  # Последний - Блэр

    def test_ordering_authors_by_birth_date_asc(self):
        """Проверка сортировки по дате рождения (по возрастанию)."""
        self.login_reader()
        response = self.client.get(self.url, {'ordering': 'birth_date'})

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # В SQLite NULL значения идут первыми, поэтому Мизинина (без даты) - первая.
        self.assertEqual(data[0]['last_name'], 'Мизинина')

        # Среди тех, у кого есть дата, самый старый - Толкин (1892)
        self.assertEqual(data[1]['last_name'], 'Толкин')
        self.assertEqual(data[2]['last_name'], 'Блэр')
        self.assertEqual(data[3]['last_name'], 'Рахманова')
