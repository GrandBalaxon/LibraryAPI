from typing import Any

from django.contrib.auth.models import AnonymousUser
from django.db.models import QuerySet, Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from catalog.models import Author, Genre, Publisher, Work, Edition, BookCopy
from catalog.serializers import (
    AuthorSerializer, GenreSerializer, PublisherSerializer,
    WorkSerializer, EditionSerializer, CopyCountSerializer, BookCopySerializer
)
from catalog.utils import standard_viewset_schema
from users.models import CustomUser
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

    def get_queryset(self) -> QuerySet[Author]:
        return Author.objects.annotate(
            works_count=Count('works', distinct=True),
            translations_count=Count('translations', distinct=True)
        )

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        """Запрещаем удаление автора, если в библиотеке есть экземпляры его книг."""
        author: Author = self.get_object()

        # Проверяем, есть ли физические экземпляры произведений этого автора
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
        """Запрещаем удаление издательства, если у него есть выпущенные издания."""
        publisher = self.get_object()
        if publisher.editions.exists():
            return Response(
                {'detail': 'Нельзя удалить издательство, так как у него есть изданные книги.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)


@standard_viewset_schema(tags=['Произведения'])
class WorkViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с произведениями."""
    queryset = Work.objects.prefetch_related('authors', 'genres').all()
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

    def destroy(self, request, *args, **kwargs):
        """Запрещаем удаление произведения, если у него есть издания."""
        work: Work = self.get_object()
        if work.editions.exists():
            return Response(
                {'detail': 'Нельзя удалить произведение, так как у него есть издания (в том числе архивные).'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)


@standard_viewset_schema(tags=['Издания'])
class EditionViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с конкретными изданиями книг."""
    serializer_class = EditionSerializer
    permission_classes = [IsLibrarianOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]

    search_fields = [
        'title',
        'isbn',
        'work__original_title',
        'work__authors__last_name',
        'publishers__name',
        'translators__last_name',
    ]
    ordering_fields = ['title', 'publication_year']
    filterset_fields = ['status']

    def get_queryset(self) -> QuerySet[Edition]:
        queryset = Edition.objects.select_related('work').prefetch_related(
            'work__authors', 'work__genres', 'publishers', 'translators', 'copies'
        ).annotate(
            # Аннотируем общее количество копий
            total_copies_count=Count('copies', distinct=True),
            # Аннотируем количество ТОЛЬКО доступных копий
            available_copies_count=Count(
                'copies',
                filter=Q(copies__status=BookCopy.Status.AVAILABLE),
                distinct=True
            )
        )

        user: CustomUser | AnonymousUser = self.request.user

        # Если пользователь — библиотекарь, он видит всё (и активные, и архивные издания)
        if user.is_authenticated and user.role == CustomUser.Role.LIBRARIAN:
            return queryset

        # Иначе скрываем архивированные издания
        return queryset.filter(status=Edition.Status.ACTIVE)

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Удаление пустого издания или архивация издания со списанными копиями."""
        edition: Edition = self.get_object()

        # 1. Если есть не списанные копии — ошибка
        if not edition.can_be_archived():
            return Response(
                {'detail': (
                    'Нельзя удалить или архивировать издание, пока в библиотеке '
                    'есть его не списанные экземпляры.'
                )},
                status=status.HTTP_400_BAD_REQUEST
            )
        # 2. Если копий вообще никогда не было — удаляем физически
        elif not edition.copies.exists():
            return super().destroy(request, *args, **kwargs)

        # 3. Если копии есть, но все списаны — отправляем в архив
        edition.status = Edition.Status.ARCHIVED
        edition.save(update_fields=['status'])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(summary='Добавление экземпляров издания', request=CopyCountSerializer)
    @action(detail=True, methods=['post'])
    def add_copies(self, request: Request, pk: str | None = None) -> Response:
        edition: Edition = self.get_object()

        serializer = CopyCountSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        count = serializer.validated_data['count']
        existing_count = edition.copies.count()
        base_identifier = edition.isbn or f'ED-{edition.id}'

        copies = []
        for i in range(count):
            inv_number = f'{base_identifier}-{existing_count + i + 1}'
            copies.append(BookCopy(edition=edition, inventory_number=inv_number))

        BookCopy.objects.bulk_create(copies)

        edition = self.get_queryset().get(pk=edition.pk)
        return Response(EditionSerializer(edition).data)


@standard_viewset_schema(tags=['Экземпляры книг'])
class BookCopyViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с индивидуальными копиями книг в библиотеке."""
    serializer_class = BookCopySerializer
    permission_classes = [IsLibrarianOrReadOnly]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'condition', 'edition']

    search_fields = [
        'edition__title',
        'edition__isbn',
        'inventory_number',
        'edition__work__original_title',
        'edition__work__authors__last_name',
    ]
    ordering_fields = ['inventory_number', 'status']

    def get_queryset(self):
        # Оптимизация N+1
        queryset = BookCopy.objects.select_related('edition', 'edition__work')
        user: CustomUser | AnonymousUser = self.request.user

        # Библиотекарь видит все экземпляры
        if user.is_authenticated and user.role == CustomUser.Role.LIBRARIAN:
            return queryset

        # Читатели и анонимы видят только доступные экземпляры
        return queryset.filter(status=BookCopy.Status.AVAILABLE)

    def destroy(self, request, *args, **kwargs):
        """Вместо физического удаления помечаем книгу как списанную."""
        instance = self.get_object()

        if instance.status == BookCopy.Status.BORROWED:
            return Response(
                {'detail': 'Нельзя списать книгу, которая выдана читателю.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        instance.status = BookCopy.Status.WRITTEN_OFF
        instance.save(update_fields=['status'])
        return Response(status=status.HTTP_204_NO_CONTENT)
