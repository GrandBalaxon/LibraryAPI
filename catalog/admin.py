from django.contrib import admin
from django.db.models import Count

from catalog.models import Book, Author, Genre


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'middle_name', 'birth_date', 'book_count')
    search_fields = ('last_name', 'first_name', 'middle_name')
    list_filter = ('birth_date',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(book_count=Count('books'))

    @admin.display(description='Количество книг', ordering='book_count')
    def book_count(self, obj):
        return obj.book_count


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'book_count')
    search_fields = ('name',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(book_count=Count('books'))

    @admin.display(description='Количество книг', ordering='book_count')
    def book_count(self, obj):
        return obj.book_count


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'display_authors', 'display_genres', 'publication_year', 'total_copies', 'available_copies'
    )
    list_filter = ('genres', 'publication_year')
    search_fields = ('title', 'isbn', 'authors__last_name', 'authors__first_name')
    filter_horizontal = ('authors', 'genres')
    readonly_fields = ('available_copies',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related('authors', 'genres')

    @admin.display(description='Авторы')
    def display_authors(self, obj):
        return ', '.join([str(author) for author in obj.authors.all()])

    @admin.display(description='Жанры')
    def display_genres(self, obj):
        return ', '.join([genre.name for genre in obj.genres.all()])
