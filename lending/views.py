from rest_framework import viewsets, filters

from catalog.utils import standard_viewset_schema
from lending.models import BookLoan
from lending.serializers import BookLoanSerializer


@standard_viewset_schema(tags=['Выдача книг'])
class BookLoanViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с выдачей книг."""
    queryset = BookLoan.objects.all()
    serializer_class = BookLoanSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['borrowed_at']
