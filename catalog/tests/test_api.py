from catalog.tests.base import BaseAPITestCase


class AuthorModelTest(BaseAPITestCase):
    """"""

    def setUp(self):
        super().setUp()
        self.url_list = '/api/catalog/authors/'

    def test_list_authors_reader_allowed(self):
        """Читатель может получить список авторов."""
        self.login_reader()
        response = self.client.get(self.url_list)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(author['last_name'] == 'Блэр' for author in response.json()))

    def test_list_authors_librarian_allowed(self):
        """Библиотекарь может получить список авторов."""
        self.login_librarian()
        response = self.client.get(self.url_list)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(author['last_name'] == 'Блэр' for author in response.json()))

    def test_list_authors_anonymous_not_allowed(self):
        """Анонимный пользователь не может получить список авторов."""
        self.logout()
        response = self.client.get(self.url_list)
        self.assertIn(response.status_code, (401, 403))
