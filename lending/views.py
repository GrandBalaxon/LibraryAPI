from django.db import transaction
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response

from catalog.utils import standard_viewset_schema
from lending.models import BookLoan
from lending.serializers import BookLoanSerializer
from users.permissions import IsLibrarianOrReadOnly


@standard_viewset_schema(tags=['Выдача книг'])
@extend_schema_view(
    return_book=extend_schema(
        summary='Вернуть книгу',
        description=(
                'Отмечает выдачу как возвращённую, увеличивает количество доступных экземпляров книги'
                ' на 1 и фиксирует дату возврата.'
        ),
        request=None
    )
)
class BookLoanViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с выдачей книг."""
    queryset = BookLoan.objects.all()
    serializer_class = BookLoanSerializer
    permission_classes = [IsLibrarianOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['user', 'status', 'book']
    ordering_fields = ['borrowed_at', 'due_date', 'status']
    ordering = ['-borrowed_at']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'librarian':
            return super().get_queryset()
        return super().get_queryset().filter(user=user)

    @action(methods=['post'], detail=True, url_path='return')
    def return_book(self, request, pk=None):
        loan = self.get_object()
        if loan.status == BookLoan.Status.RETURNED:
            return Response(
                {'detail': 'Книга уже возвращена.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        with transaction.atomic():
            loan = BookLoan.objects.select_for_update().get(pk=loan.pk)
            if loan.status == BookLoan.Status.RETURNED:
                return Response(
                    {'detail': 'Книга уже возвращена.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            loan.status = BookLoan.Status.RETURNED
            loan.returned_at = timezone.now()
            loan.save(update_fields=['status', 'returned_at'])
            loan.book.available_copies += 1
            loan.book.save(update_fields=['available_copies'])
        return Response(BookLoanSerializer(loan).data)
