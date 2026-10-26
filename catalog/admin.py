from django.contrib import admin
from django.db.models import Count, QuerySet
from django.http import HttpRequest

from catalog.models import Work, Author, Genre, Publisher, Edition, BookCopy


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'pseudonym', 'birth_date', 'works_count', 'translations_count')
    search_fields = ('last_name', 'first_name', 'middle_name', 'pseudonym')
    list_filter = ('birth_date',)

    def get_queryset(self, request: HttpRequest) -> QuerySet[Author]:
        queryset = super().get_queryset(request)
        return queryset.annotate(
            works_count=Count('works', distinct=True),
            translations_count=Count('translations', distinct=True)
        )

    @admin.display(description='Написанных произведений', ordering='works_count')
    def works_count(self, obj) -> int:
        return obj.works_count

    @admin.display(description='Переведенных изданий', ordering='translations_count')
    def translations_count(self, obj) -> int:
        return obj.translations_count

    @admin.display(description='Полное имя')
    def full_name(self, obj) -> str:
        return obj.full_name


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'works_count')
    search_fields = ('name',)

    def get_queryset(self, request: HttpRequest) -> QuerySet[Genre]:
        queryset = super().get_queryset(request)
        return queryset.annotate(works_count=Count('works'))

    @admin.display(description='Количество произведений', ordering='works_count')
    def works_count(self, obj) -> int:
        return obj.works_count


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'editions_count')
    search_fields = ('name',)

    def get_queryset(self, request: HttpRequest) -> QuerySet[Publisher]:
        queryset = super().get_queryset(request)
        return queryset.annotate(editions_count=Count('editions'))

    @admin.display(description='Количество изданных книг', ordering='editions_count')
    def editions_count(self, obj) -> int:
        return obj.editions_count


@admin.register(Work)
class WorkAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'original_title',
        'writing_year',
        'display_authors',
        'display_genres',
        'editions_count'
    )
    list_filter = ('genres',)
    search_fields = ('original_title', 'authors__last_name', 'authors__first_name', 'authors__pseudonym')
    filter_horizontal = ('authors', 'genres')

    def get_queryset(self, request: HttpRequest) -> QuerySet[Work]:
        queryset = super().get_queryset(request)
        return queryset.prefetch_related('authors', 'genres').annotate(editions_count=Count('editions'))

    @admin.display(description='Авторы')
    def display_authors(self, obj) -> str:
        return ', '.join([str(author) for author in obj.authors.all()])

    @admin.display(description='Жанры')
    def display_genres(self, obj) -> str:
        return ', '.join([genre.name for genre in obj.genres.all()])

    @admin.display(description='Количество изданий', ordering='editions_count')
    def editions_count(self, obj) -> int:
        return obj.editions_count


class BookCopyInline(admin.TabularInline):
    """Позволяет просматривать и редактировать экземпляры прямо из карточки издания."""
    model = BookCopy
    extra = 1
    fields = ('inventory_number', 'status', 'condition', 'location')
    readonly_fields = ('inventory_number',)


@admin.register(Edition)
class EditionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'work',
        'isbn',
        'publication_year',
        'language',
        'status',
        'copies_count',
    )
    list_filter = ('status', 'publishers', 'language', 'publication_year')
    search_fields = (
        'title',
        'isbn',
        'work__original_title',
        'publishers__name',
        'translators__last_name',
        'translators__first_name'
    )
    filter_horizontal = ('publishers', 'translators')
    inlines = [BookCopyInline]

    def get_queryset(self, request: HttpRequest) -> QuerySet[Edition]:
        queryset = super().get_queryset(request)
        return queryset.select_related('work').prefetch_related('publishers', 'translators').annotate(
            total_copies_count=Count('copies')
        )

    @admin.display(description='Всего экземпляров', ordering='total_copies_count')
    def copies_count(self, obj) -> int:
        return obj.total_copies_count

    @admin.display(description='Издательства')
    def display_publishers(self, obj) -> str:
        return ', '.join([publisher.name for publisher in obj.publishers.all()])

    @admin.display(description='Переводчики')
    def display_translators(self, obj) -> str:
        return ', '.join([str(translator) for translator in obj.translators.all()])


@admin.register(BookCopy)
class BookCopyAdmin(admin.ModelAdmin):
    """Отдельная страница для поиска и управления физическими книгами."""
    list_display = ('id', 'inventory_number', 'edition_title', 'status', 'condition', 'location')
    list_filter = ('status', 'condition')
    search_fields = (
        'inventory_number',
        'edition__title',
        'edition__isbn',
        'edition__work__original_title'
    )
    autocomplete_fields = ('edition',)

    def get_queryset(self, request: HttpRequest) -> QuerySet[BookCopy]:
        queryset = super().get_queryset(request)
        return queryset.select_related('edition', 'edition__work')

    @admin.display(description='Издание', ordering='edition__title')
    def edition_title(self, obj) -> str:
        return f"{obj.edition.title} ({obj.edition.publication_year})"
