from django.db import models


class Author(models.Model):
    """Автор книги."""
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
    biography = models.TextField(blank=True, verbose_name='Биография')

    class Meta:
        verbose_name = 'Автор'
        verbose_name_plural = 'Авторы'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.last_name} {self.first_name} {self.middle_name or ""}'.strip()


class Genre(models.Model):
    """Жанр книги."""
    name = models.CharField(max_length=100, unique=True, verbose_name='Название жанра')

    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'

    def __str__(self):
        return self.name


class Book(models.Model):
    """Книга в библиотечном каталоге."""
    title = models.CharField(max_length=255, verbose_name='Название')
    authors = models.ManyToManyField(
        Author,
        related_name='books',
        verbose_name='Авторы'
    )
    genres = models.ManyToManyField(
        Genre,
        related_name='books',
        blank=True,
        verbose_name='Жанры'
    )
    isbn = models.CharField(
        max_length=13,
        unique=True,
        null=True,
        blank=True,
        verbose_name='ISBN'
    )
    publication_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Год издания'
    )
    description = models.TextField(blank=True, verbose_name='Описание')
    total_copies = models.PositiveIntegerField(default=1, verbose_name='Всего экземпляров')
    available_copies = models.PositiveIntegerField(default=1, verbose_name='Доступно экземпляров')

    class Meta:
        db_table = 'books'
        verbose_name = 'Книга'
        verbose_name_plural = 'Книги'
        ordering = ['title']

    def __str__(self):
        return self.title
