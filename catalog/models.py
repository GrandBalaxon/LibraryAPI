from django.core.exceptions import ValidationError
from django.db import models
from stdnum import isbn


class Author(models.Model):
    """Автор книги или перевода."""
    first_name = models.CharField(max_length=150, verbose_name='Имя')
    last_name = models.CharField(max_length=150, verbose_name='Фамилия')
    middle_name = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name='Отчество'
    )
    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата рождения'
    )
    pseudonym = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name='Псевдоним'
    )
    biography = models.TextField(blank=True, verbose_name='Биография')

    class Meta:
        verbose_name = 'Автор'
        verbose_name_plural = 'Авторы'
        ordering = ['last_name', 'first_name']

    @property
    def full_name(self):
        return f'{self.last_name} {self.first_name} {self.middle_name or ""}'.strip()

    def __str__(self):
        return self.full_name


class Genre(models.Model):
    """Жанр книги."""
    name = models.CharField(max_length=100, unique=True, verbose_name='Название жанра')

    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'

    def __str__(self):
        return self.name


class Publisher(models.Model):
    """Издательство."""
    name = models.CharField(max_length=255, unique=True, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')

    class Meta:
        verbose_name = 'Издательство'
        verbose_name_plural = 'Издательства'

    def __str__(self):
        return self.name


class Book(models.Model):
    """Книга в библиотечном каталоге."""
    title = models.CharField(max_length=255, verbose_name='Название')
    original_title = models.CharField(max_length=255, verbose_name='Оригинальное название')
    original_language = models.CharField(max_length=50, verbose_name='Язык оригинала')
    authors = models.ManyToManyField(
        Author, related_name='books', verbose_name='Авторы'
    )
    genres = models.ManyToManyField(
        Genre, related_name='books', blank=True, verbose_name='Жанры'
    )
    writing_year = models.PositiveIntegerField(null=True, blank=True, verbose_name='Год написания')
    description = models.TextField(blank=True, verbose_name='Описание')

    class Meta:
        db_table = 'books'
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'
        ordering = ['title']

    def __str__(self):
        return self.title


class BookEdition(models.Model):
    """Конкретное издание книги."""
    book = models.ForeignKey(
        Book, on_delete=models.CASCADE, related_name='editions', verbose_name='Произведение'
    )
    title = models.CharField(max_length=255, verbose_name="Название перевода")
    isbn = models.CharField(
        max_length=17,
        unique=True,
        null=True,
        blank=True,
        verbose_name='ISBN'
    )
    publishers = models.ManyToManyField(
        Publisher,
        related_name='editions',
        blank=True,
        verbose_name='Издательства'
    )
    publication_year = models.PositiveIntegerField(
        verbose_name='Год издания'
    )
    language = models.CharField(max_length=50, verbose_name='Язык')
    translators = models.ManyToManyField(
        Author,
        blank=True,
        related_name='translations',
        verbose_name='Авторы перевода'
    )
    total_copies = models.PositiveIntegerField(default=1, verbose_name='Всего экземпляров')
    available_copies = models.PositiveIntegerField(default=1, verbose_name='Доступно экземпляров')

    class Meta:
        db_table = 'book_editions'
        verbose_name = 'Изданная книга'
        verbose_name_plural = 'Изданные книги'
        ordering = ['title']

    def __str__(self):
        return f'{self.title} ({self.publication_year})'

    def clean(self):
        super().clean()
        if self.isbn:
            try:
                # Валидируем и получаем компактный вид
                compact_isbn = isbn.validate(self.isbn)
                # Форматируем: приводим к ISBN-13 и добавляем правильные дефисы
                self.isbn = isbn.format(compact_isbn, convert=True)
            except (isbn.InvalidLength, isbn.InvalidChecksum):
                raise ValidationError({'isbn': 'Некорректный формат или контрольная сумма ISBN.'})
            except Exception:
                raise ValidationError({'isbn': 'Некорректный ISBN'})
