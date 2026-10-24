from django.core.exceptions import ValidationError
from django.db import models

from catalog.validators import validate_isbn


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
    def full_name(self) -> str:
        return f'{self.last_name} {self.first_name} {self.middle_name or ""}'.strip()

    def __str__(self) -> str:
        return self.full_name


class Genre(models.Model):
    """Жанр произведения."""
    name = models.CharField(max_length=100, unique=True, verbose_name='Название жанра')

    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'

    def __str__(self) -> str:
        return self.name


class Publisher(models.Model):
    """Издательство."""
    name = models.CharField(max_length=255, unique=True, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')

    class Meta:
        verbose_name = 'Издательство'
        verbose_name_plural = 'Издательства'

    def __str__(self) -> str:
        return self.name


class Work(models.Model):
    """Произведение/Работа автора (писателя)."""
    original_title = models.CharField(max_length=255, verbose_name='Оригинальное название')
    original_language = models.CharField(max_length=50, verbose_name='Язык оригинала')
    authors = models.ManyToManyField(
        Author, related_name='works', verbose_name='Авторы'
    )
    genres = models.ManyToManyField(
        Genre, related_name='works', blank=True, verbose_name='Жанры'
    )
    writing_year = models.PositiveIntegerField(null=True, blank=True, verbose_name='Год написания')
    description = models.TextField(blank=True, verbose_name='Описание')

    class Meta:
        db_table = 'works'
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'
        ordering = ['original_title']

    def __str__(self) -> str:
        return self.original_title


class Edition(models.Model):
    """
    Конкретный выпуск (публикация) произведения в определенном издательстве,
    объединяющий экземпляры с одинаковым ISBN и годом выпуска.
    """
    work = models.ForeignKey(
        Work, on_delete=models.CASCADE, related_name='editions', verbose_name='Произведение'
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
    pages = models.PositiveIntegerField(verbose_name='Количество страниц')

    class Meta:
        db_table = 'editions'
        verbose_name = 'Издание'
        verbose_name_plural = 'Издания'
        ordering = ['title']

    def __str__(self) -> str:
        return f'{self.title} ({self.publication_year})'

    def clean(self) -> None:
        super().clean()
        if self.isbn:
            try:
                self.isbn = validate_isbn(self.isbn)
            except ValidationError as exc:
                # Оборачиваем под ключ поля, чтобы в админке/формах ошибка встала напротив input'а isbn
                raise ValidationError({'isbn': exc.messages}) from exc


class BookCopy(models.Model):
    """
    Конкретный физический экземпляр выпущенной книги (Edition).
    """
    class Status(models.TextChoices):
        AVAILABLE = 'available', 'Доступна'
        BORROWED = 'borrowed', 'Выдана'
        RESERVED = 'reserved', 'Зарезервирована'
        LOST = 'lost', 'Утеряна'
        WRITTEN_OFF = 'written_off', 'Списана'

    class Condition(models.TextChoices):
        NEW = 'new', 'Новая'
        GOOD = 'good', 'Хорошая'
        WORN = 'worn', 'Потрёпанная'
        DAMAGED = 'damaged', 'Повреждённая'

    edition = models.ForeignKey(
        Edition,
        on_delete=models.CASCADE,
        related_name='copies',
        verbose_name='Издание'
    )
    inventory_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Инвентарный номер',
        help_text='Уникальный штрихкод или номер экземпляра'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
        verbose_name='Статус'
    )
    condition = models.CharField(
        max_length=20,
        choices=Condition.choices,
        default=Condition.NEW,
        verbose_name='Состояние'
    )
    location = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Местоположение',
        help_text='Например: Зал 1, стеллаж 4, полка 2'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Примечания'
    )

    class Meta:
        db_table = 'book_copies'
        verbose_name = 'Экземпляр книги'
        verbose_name_plural = 'Экземпляры книг'

    def __str__(self) -> str:
        return f'{self.edition.title} [{self.inventory_number}]'
