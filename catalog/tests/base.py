from datetime import date

from rest_framework.test import APITestCase

from catalog.models import Author, Genre, Publisher, Work, Edition, BookCopy
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

        # ---------- Произведения (Work) ----------
        cls.work = Work.objects.create(
            original_title="Nineteen Eighty-Four",
            original_language="Английский",
            writing_year=1948,
            description=(
                "Культовый роман о тоталитарном обществе Океании, где власть "
                "Партии абсолютна, история переписывается, а Большой Брат "
                "следит за каждым."
            ),
        )
        cls.work.authors.set([cls.author])
        cls.work.genres.set([cls.genre])

        cls.work2 = Work.objects.create(
            original_title="The Hobbit, or There and Back Again",
            original_language="Английский",
            writing_year=1937,
            description=(
                "История о мирном хоббите Бильбо Бэггинсе, который по воле "
                "волшебника Гэндальфа оказывается втянут в опасный поход."
            ),
        )
        cls.work2.authors.set([cls.author2])
        cls.work2.genres.set([cls.genre2, cls.genre3])

        # ---------- Издания (Edition) ----------
        cls.edition = Edition.objects.create(
            work=cls.work,
            title="1984",
            isbn="978-5-00155-298-7",
            publication_year=2020,
            language="Русский",
            pages=320,
        )
        cls.edition.publishers.set([cls.publisher])
        cls.edition.translators.set([cls.translator])

        cls.edition2 = Edition.objects.create(
            work=cls.work2,
            title="Хоббит, или Туда и Обратно",
            isbn="978-5-17-081760-3",
            publication_year=2013,
            language="Русский",
            pages=400,
        )
        cls.edition2.publishers.set([cls.publisher2])
        cls.edition2.translators.set([cls.translator2])

        # ---------- Экземпляры (BookCopy) ----------
        cls.copy1 = BookCopy.objects.create(
            edition=cls.edition,
            inventory_number="978-5-00155-298-7-1",
            status=BookCopy.Status.AVAILABLE
        )
        cls.copy2 = BookCopy.objects.create(
            edition=cls.edition,
            inventory_number="978-5-00155-298-7-2",
            status=BookCopy.Status.AVAILABLE
        )
        cls.copy_hobbit = BookCopy.objects.create(
            edition=cls.edition2,
            inventory_number="978-5-17-081760-3-1",
            status=BookCopy.Status.BORROWED
        )

    # ---------- Хелперы: аутентификация ----------
    def login_reader(self) -> None:
        """Аутентифицировать клиент как читателя."""
        self.client.force_authenticate(self.user_reader)

    def login_librarian(self) -> None:
        """Аутентифицировать клиент как библиотекаря."""
        self.client.force_authenticate(self.user_librarian)

    def logout(self) -> None:
        """Сбросить аутентификацию клиента."""
        self.client.force_authenticate(None)

    # ---------- Хелперы: данные ----------
    def set_copy_status(self, copy: BookCopy, status: str) -> BookCopy:
        """
        Установить статус экземпляра книги.
        Полезно для тестов, где нужно подготовить книгу к выдаче или списанию.
        """
        copy.status = status
        copy.save(update_fields=["status"])
        copy.refresh_from_db()
        return copy
