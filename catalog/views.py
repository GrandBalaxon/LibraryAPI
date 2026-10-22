from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from catalog.models import Author, Genre, Publisher, Work, Edition, BookCopy
from catalog.serializers import AuthorSerializer, GenreSerializer, PublisherSerializer, WorkSerializer, \
    EditionSerializer, CopyCountSerializer
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

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        """Запрещаем удаление автора, если в библиотеке есть экземпляры его книг."""
        author: Author = self.get_object()

        # Ищем издания книг этого автора, у которых есть копии (total_copies > 0)
        has_copies = BookCopy.objects.filter(
            edition__work__authors=author
        ).exists()

        if has_copies:
            return Response(
                {'detail': 'Нельзя удалить автора, так как в библиотеке есть экземпляры его произведений.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().destroy(request, *args, **kwargs)


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

    def destroy(self, request, *args, **kwargs):
        publisher = self.get_object()
        # Проверяем, есть ли у издательства изданные книги в библиотеке
        if publisher.editions.exists():
            return Response(
                {'detail': 'Нельзя удалить издательство, так как у него есть изданные книги.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)


@standard_viewset_schema(tags=['Произведения'])
class WorkViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с произведениями."""
    queryset = Work.objects.all()
    serializer_class = WorkSerializer
    permission_classes = [IsLibrarianOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'original_title',
        'authors__last_name',
        'authors__first_name',
        'authors__pseudonym',
        'genres__name',
    ]
    ordering_fields = ['original_title', 'writing_year', 'original_language']


@standard_viewset_schema(tags=['Книги'])
class EditionViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с конкретными изданиями книг."""
    queryset = Edition.objects.all()
    serializer_class = EditionSerializer
    permission_classes = [IsLibrarianOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'title',
        'isbn',
        'work__original_title',
        'work__authors__last_name',
        'publishers__name',
        'translators__last_name',
    ]
    ordering_fields = ['title', 'publication_year']

    @extend_schema(summary='Добавление копий книги', request=CopyCountSerializer)
    @action(detail=True, methods=['post'])
    def add_copies(self, request: Request, pk: str | None = None) -> Response:
        edition: Edition = self.get_object()
        count = int(request.data.get('count', 0))

        if count <= 0:
            return Response(
                {'detail': 'Укажите положительное число'},
                status=status.HTTP_400_BAD_REQUEST
            )

        existing_count = edition.copies.count()
        base_identifier = edition.isbn or f'ED-{edition.id}'

        copies =[]
        for i in range(count):
            inv_number = f'{base_identifier}-{existing_count + i + 1}'
            copies.append(BookCopy(edition=edition, inventory_number=inv_number))

        # Массовое создание BookCopy объектов
        BookCopy.objects.bulk_create(copies)

        return Response(EditionSerializer(edition).data)
