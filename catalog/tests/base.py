from datetime import date

from rest_framework.test import APITestCase

from catalog.models import Author, Genre, Publisher, Book, BookEdition
from users.models import CustomUser


class BaseAPITestCase(APITestCase):
    """Базовый класс с общими тестовыми данными для тестов приложения catalog."""

    @classmethod
    def setUpTestData(cls):
        # ---------- Пользователи ----------
        cls.user_reader = CustomUser.objects.create_user(
            email="user1@test.ru",
            password="12345",
            first_name="Иван",
            last_name="Иванов",
            middle_name="Иванович",
            role=CustomUser.Role.READER,
            phone_number="+71234567890",
            place_of_birth="город Москва",
        )

        cls.user_librarian = CustomUser.objects.create_user(
            email="user2@test.ru",
            password="12345",
            first_name="Ваня",
            last_name="Иванова",
            middle_name="Ивановна",
            role=CustomUser.Role.LIBRARIAN,
            phone_number="+71234567899",
            place_of_birth="город Москва",
        )

        # ---------- Авторы ----------
        cls.author = Author.objects.create(
            first_name="Эрик",
            last_name="Блэр",
            middle_name="Артур",
            birth_date=date(1903, 6, 25),
            pseudonym="Джордж Оруэлл",
            biography="Британский писатель и публицист, классик антиутопической литературы.",
        )

        cls.translator = Author.objects.create(
            first_name="Ирина",
            last_name="Мизинина",
            middle_name="Николаевна",
            biography="Российский переводчик, кандидат филологических наук, доцент, автор переводов.",
        )

        # Второй автор / переводчик — для тестов на множественные связи
        cls.author2 = Author.objects.create(
            first_name="Джон",
            last_name="Толкин",
            middle_name="Рональд Руэл",
            birth_date=date(1892, 1, 3),
            pseudonym="Дж. Р. Р. Толкин",
            biography="Английский писатель, лингвист и филолог, профессор Оксфордского университета.",
        )

        cls.translator2 = Author.objects.create(
            first_name="Наталия",
            last_name="Рахманова",
            middle_name="Леонидовна",
            birth_date=date(1930, 11, 24),
            biography="Советская и российская переводчица, филолог-англист.",
        )

        # ---------- Жанры ----------
        cls.genre = Genre.objects.create(name="Роман-антиутопия")
        cls.genre2 = Genre.objects.create(name="Фэнтези")
        cls.genre3 = Genre.objects.create(name="Детская литература")

        # ---------- Издательства ----------
        cls.publisher = Publisher.objects.create(
            name="Яуза",
            description="Одно из крупнейших издательств России и русского мира.",
        )
        cls.publisher2 = Publisher.objects.create(
            name="АСТ",
            description="",
        )

        # ---------- Произведения ----------
        cls.book = Book.objects.create(
            title="1984",
            original_title="Nineteen Eighty-Four",
            original_language="Английский",
            writing_year=1948,
            description=(
                "Культовый роман о тоталитарном обществе Океании, где власть "
                "Партии абсолютна, история переписывается, а Большой Брат "
                "следит за каждым."
            ),
        )
        cls.book.authors.set([cls.author])
        cls.book.genres.set([cls.genre])

        cls.book2 = Book.objects.create(
            title="Хоббит, или Туда и обратно",
            original_title="The Hobbit, or There and Back Again",
            original_language="Английский",
            writing_year=1937,
            description=(
                "История о мирном хоббите Бильбо Бэггинсе, который по воле "
                "волшебника Гэндальфа оказывается втянут в опасный поход."
            ),
        )
        cls.book2.authors.set([cls.author2])
        cls.book2.genres.set([cls.genre2, cls.genre3])

        # ---------- Издания ----------
        cls.edition = BookEdition.objects.create(
            book=cls.book,
            title="1984",
            isbn="978-5-00155-298-7",
            publication_year=2020,
            language="Русский",
            total_copies=6,
            available_copies=6,
        )
        cls.edition.publishers.set([cls.publisher])
        cls.edition.translators.set([cls.translator])

        cls.edition2 = BookEdition.objects.create(
            book=cls.book2,
            title="Хоббит, или Туда и Обратно",
            isbn="978-5-17-081760-3",
            publication_year=2013,
            language="Русский",
            total_copies=1,
            available_copies=0,
        )
        cls.edition2.publishers.set([cls.publisher2])
        cls.edition2.translators.set([cls.translator2])

    # ---------- Хелперы: аутентификация ----------

    def login_reader(self):
        """Аутентифицировать клиент как читателя."""
        self.client.force_authenticate(self.user_reader)

    def login_librarian(self):
        """Аутентифицировать клиент как библиотекаря."""
        self.client.force_authenticate(self.user_librarian)

    def logout(self):
        """Сбросить аутентификацию клиента."""
        self.client.force_authenticate(None)

    # ---------- Хелперы: данные ----------

    def set_available_copies(self, edition, count):
        """
        Установить edition.available_copies = count.

        Полезно для тестов remove_copies: между тестами значения
        откатываются транзакцией, но внутри одного теста объект из
        setUpTestData нужно перезаписать вручную.
        """
        edition.available_copies = count
        edition.save(update_fields=["available_copies"])
        edition.refresh_from_db()
        return edition
