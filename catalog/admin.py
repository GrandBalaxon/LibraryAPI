from django.contrib import admin
from django.db.models import Count

from catalog.models import Book, Author, Genre, Publisher, BookEdition


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'pseudonym', 'birth_date', 'book_count', 'translations_count')
    search_fields = ('last_name', 'first_name', 'middle_name')
    list_filter = ('birth_date',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            book_count=Count('books'),
            translations_count=Count('translations', distinct=True)
        )

    @admin.display(description='Написанных произведений', ordering='book_count')
    def book_count(self, obj):
        return obj.book_count

    @admin.display(description='Переведенных произведений', ordering='translations_count')
    def translations_count(self, obj):
        return obj.translations_count

    @admin.display(description='Полное имя')
    def full_name(self, obj):
        return obj.full_name


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'book_count')
    search_fields = ('name',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(book_count=Count('books'))

    @admin.display(description='Количество произведений', ordering='book_count')
    def book_count(self, obj):
        return obj.book_count


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ('name', 'editions_count')
    search_fields = ('name',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(editions_count=Count('editions'))

    @admin.display(description='Количество изданных книг', ordering='editions_count')
    def editions_count(self, obj):
        return obj.editions_count


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'original_title',
        'writing_year',
        'display_authors',
        'display_genres',
        'editions_count'
    )
    list_filter = ('genres',)
    search_fields = ('title', 'authors__last_name', 'authors__first_name', 'authors__pseudonym')
    filter_horizontal = ('authors', 'genres')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related('authors', 'genres').annotate(editions_count=Count('editions'))

    @admin.display(description='Авторы')
    def display_authors(self, obj):
        return ', '.join([str(author) for author in obj.authors.all()])

    @admin.display(description='Жанры')
    def display_genres(self, obj):
        return ', '.join([genre.name for genre in obj.genres.all()])

    @admin.display(description='Количество изданий')
    def editions_count(self, obj):
        return obj.editions.count()


@admin.register(BookEdition)
class BookEditionAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'book',
        'isbn',
        'publication_year',
        'language',
        'total_copies',
        'available_copies'
    )
    list_filter = ('publishers', 'language', 'publication_year')
    search_fields = (
        'title',
        'isbn',
        'book__title',
        'publishers__name',
        'translators__last_name',
        'translators__first_name'
    )
    filter_horizontal = ('publishers', 'translators')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('book').prefetch_related('publishers', 'translators')

    @admin.display(description='Издательства')
    def display_publishers(self, obj):
        return ', '.join([publisher.name for publisher in obj.publishers.all()])

    @admin.display(description='Переводчики')
    def display_translators(self, obj):
        return ', '.join([str(translator) for translator in obj.translators.all()])
