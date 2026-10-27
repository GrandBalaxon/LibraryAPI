from django.core.exceptions import ValidationError
from django.test import TestCase

from catalog.models import Author, Genre, Publisher, Work, Edition, BookCopy


class CatalogModelTest(TestCase):
    """Тесты для моделей приложения catalog (строковые представления и валидация)."""

    def test_string_representations(self):
        """Проверка методов __str__ для всех моделей."""
        author = Author.objects.create(
            first_name="Эрик", last_name="Блэр", middle_name="Артур"
        )
        self.assertEqual(str(author), "Блэр Эрик Артур")

        genre = Genre.objects.create(name="Фантастика")
        self.assertEqual(str(genre), "Фантастика")

        publisher = Publisher.objects.create(name="АСТ")
        self.assertEqual(str(publisher), "АСТ")

        work = Work.objects.create(
            original_title="1984", original_language="Английский"
        )
        self.assertEqual(str(work), "1984")

        edition = Edition.objects.create(
            work=work, title="1984 (перевод)", publication_year=2020,
            language="Русский", pages=320
        )
        self.assertEqual(str(edition), "1984 (перевод) (2020)")

        copy = BookCopy.objects.create(
            edition=edition, inventory_number="INV-123"
        )
        self.assertEqual(str(copy), "1984 (перевод) [INV-123]")

    def test_edition_clean_valid_isbn(self):
        """Проверяем, что clean() нормализует валидный ISBN."""
        work = Work.objects.create(original_title="Test", original_language="Рус")
        edition = Edition(
            work=work, title="Test", isbn="9783161484100",  # Без дефисов
            publication_year=2020, language="Рус", pages=100
        )

        # Вызываем full_clean(), который запускает наш метод clean()
        edition.full_clean()

        # Проверяем, что ISBN отформатировался
        self.assertEqual(edition.isbn, "978-3-16-148410-0")

    def test_edition_clean_invalid_isbn(self):
        """Проверяем, что clean() выбрасывает ValidationError при неверном ISBN."""
        work = Work.objects.create(original_title="Test", original_language="Рус")
        edition = Edition(
            work=work, title="Test", isbn="12345",  # Невалидный
            publication_year=2020, language="Рус", pages=100
        )

        # Ожидаем ошибку валидации
        with self.assertRaises(ValidationError) as context:
            edition.full_clean()

        # Проверяем, что ошибка привязана именно к полю isbn
        self.assertIn('isbn', context.exception.message_dict)

    def test_edition_clean_empty_isbn(self):
        """Проверяем, что clean() не падает, если ISBN не указан."""
        work = Work.objects.create(original_title="Test", original_language="Рус")
        edition = Edition(
            work=work, title="Test", isbn=None,
            publication_year=2020, language="Рус", pages=100
        )

        # Не должно быть исключений
        try:
            edition.full_clean()
        except ValidationError:
            self.fail("full_clean() raised ValidationError unexpectedly for empty ISBN")
