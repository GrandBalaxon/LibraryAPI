from rest_framework import viewsets, filters

from catalog.models import Author, Genre, Publisher, Book, BookEdition
from catalog.serializers import AuthorSerializer, GenreSerializer, PublisherSerializer, BookSerializer, \
    BookEditionSerializer
from catalog.utils import standard_viewset_schema


@standard_viewset_schema(tags=['Авторы книг и переводов'])
class AuthorViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с авторами."""
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'middle_name', 'pseudonym']
    ordering_fields = ['last_name', 'first_name', 'birth_date']


@standard_viewset_schema(tags=['Жанры'])
class GenreViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с жанрами."""
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


@standard_viewset_schema(tags=['Издательства'])
class PublisherViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с издательствами."""
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


@standard_viewset_schema(tags=['Произведения'])
class BookViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с произведениями."""
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'title',
        'original_title',
        'authors__last_name',
        'authors__first_name',
        'authors__pseudonym',
        'genres__name',
    ]
    ordering_fields = ['title', 'writing_year', 'original_language']


@standard_viewset_schema(tags=['Книги'])
class BookEditionViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с конкретными изданиями книг."""
    queryset = BookEdition.objects.all()
    serializer_class = BookEditionSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'title',
        'isbn',
        'book__title',
        'book__authors__last_name',
        'publishers__name',
        'translators__last_name',
    ]
    ordering_fields = ['title', 'publication_year', 'total_copies', 'available_copies']
