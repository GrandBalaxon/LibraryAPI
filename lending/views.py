from typing import Any

from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from catalog.models import BookCopy
from catalog.utils import standard_viewset_schema
from lending.models import BookLoan
from lending.serializers import BookLoanSerializer
from users.models import CustomUser
from users.permissions import IsLibrarianOrReadOnly


@standard_viewset_schema(tags=['Выдача книг'])
@extend_schema_view(
    return_book=extend_schema(
        summary='Вернуть книгу',
        description=(
                'Отмечает выдачу как возвращённую, меняет статус конкретного экземпляра книги'
                ' на "Доступна" и фиксирует дату возврата.'
        ),
        request=None
    )
)
class BookLoanViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с выдачей книг."""
    queryset: QuerySet[BookLoan] = BookLoan.objects.all()
    serializer_class = BookLoanSerializer
    permission_classes = [IsLibrarianOrReadOnly]

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['user', 'status', 'book_copy']
    ordering_fields = ['borrowed_at', 'due_date', 'status']
    ordering = ['-borrowed_at']

    def get_queryset(self) -> QuerySet[BookLoan]:
        # Оптимизация запросов (N+1)
        queryset = super().get_queryset().select_related(
            'user',
            'book_copy',
            'book_copy__edition',
            'book_copy__edition__work'
        )
        user: CustomUser | Any = self.request.user

        if user.is_authenticated and user.role == CustomUser.Role.LIBRARIAN:
            return queryset
        if user.is_authenticated:
            return queryset.filter(user=user)
        return queryset.none()

    @action(methods=['post'], detail=True, url_path='return')
    def return_book(self, request: Request, pk: str | None = None) -> Response:
        loan: BookLoan = self.get_object()

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

            book_copy = BookCopy.objects.select_for_update().get(pk=loan.book_copy_id)
            change_reason = 'Возврат книги через API'

            # Обновляем выдачу
            loan.status = BookLoan.Status.RETURNED
            loan.returned_at = timezone.now()
            loan._change_reason = change_reason
            loan.save(update_fields=['status', 'returned_at'])

            # Обновляем экземпляр книги
            book_copy.status = BookCopy.Status.AVAILABLE
            book_copy._change_reason = change_reason
            book_copy.save(update_fields=['status'])

        return Response(BookLoanSerializer(loan).data)
