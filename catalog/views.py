from rest_framework import viewsets, filters

from catalog.models import Author, Genre
from catalog.serializers import AuthorSerializer, GenreSerializer
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
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
