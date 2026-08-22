from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets

from catalog.models import Author
from catalog.serializers import AuthorSerializer


@extend_schema(tags=['Авторы книг и переводов'])
@extend_schema_view(
    list=extend_schema(summary='Список'),
    create=extend_schema(summary='Создание'),
    retrieve=extend_schema(summary='Детали'),
    update=extend_schema(summary='Обновление'),
    partial_update=extend_schema(summary='Частичное обновление'),
    destroy=extend_schema(summary='Удаление')
)
class AuthorViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с авторами."""
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
