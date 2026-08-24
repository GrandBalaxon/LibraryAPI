from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response

from catalog.models import Author, Genre, Publisher, Book, BookEdition
from catalog.serializers import AuthorSerializer, GenreSerializer, PublisherSerializer, BookSerializer, \
    BookEditionSerializer, CopyCountSerializer
from catalog.utils import standard_viewset_schema
from users.permissions import IsLibrarianOrReadOnly


@standard_viewset_schema(tags=['Авторы книг и переводов'])
class AuthorViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с авторами."""
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsLibrarianOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'middle_name', 'pseudonym']
    ordering_fields = ['last_name', 'first_name', 'birth_date']


@standard_viewset_schema(tags=['Жанры'])
class GenreViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с жанрами."""
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [IsLibrarianOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


@standard_viewset_schema(tags=['Издательства'])
class PublisherViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с издательствами."""
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer
    permission_classes = [IsLibrarianOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


@standard_viewset_schema(tags=['Произведения'])
class BookViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с произведениями."""
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsLibrarianOrReadOnly]
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
    permission_classes = [IsLibrarianOrReadOnly]
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

    @extend_schema(summary='Добавление копий книги', request=CopyCountSerializer)
    @action(detail=True, methods=['post'])
    def add_copies(self, request, pk=None):
        edition = self.get_object()
        count = int(request.data.get('count', 0))
        if count <= 0:
            return Response({'detail': 'Укажите положительное число'}, status=400)
        edition.total_copies += count
        edition.available_copies += count
        edition.save(update_fields=['total_copies', 'available_copies'])
        return Response(BookEditionSerializer(edition).data)

    @extend_schema(summary='Списание копий книги', request=CopyCountSerializer)
    @action(detail=True, methods=['post'])
    def remove_copies(self, request, pk=None):
        edition = self.get_object()
        count = int(request.data.get('count', 0))
        if count <= 0:
            return Response({'detail': 'Укажите положительное число'}, status=400)
        if count > edition.available_copies:
            return Response({'detail': 'Нельзя списать больше доступных копий'}, status=400)
        edition.total_copies -= count
        edition.available_copies -= count
        edition.save(update_fields=['total_copies', 'available_copies'])
        return Response(BookEditionSerializer(edition).data)
