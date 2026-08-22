from django.contrib import admin
from django.db.models import Count

from catalog.models import Book, Author, Genre, Publisher


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'pseudonym', 'birth_date', 'book_count')
    search_fields = ('last_name', 'first_name', 'middle_name')
    list_filter = ('birth_date',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(book_count=Count('books'))

    @admin.display(description='Количество произведений', ordering='book_count')
    def book_count(self, obj):
        return obj.book_count


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
