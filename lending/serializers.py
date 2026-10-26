from datetime import timedelta
from typing import Any

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from catalog.models import BookCopy
from catalog.serializers import BookCopyBriefSerializer
from lending.models import BookLoan
from users.models import CustomUser


class BookLoanSerializer(serializers.ModelSerializer):
    """Сериализатор выдачи книги."""
    # Для чтения (GET) отдаем вложенный объект (с инвентарным номером)
    book_copy = BookCopyBriefSerializer(read_only=True)

    # Для записи (POST) принимаем ID экземпляра
    book_copy_id = serializers.PrimaryKeyRelatedField(
        source='book_copy', queryset=BookCopy.objects.all(), write_only=True
    )

    user_id = serializers.PrimaryKeyRelatedField(
        source='user', queryset=CustomUser.objects.all(), write_only=True
    )
    user = serializers.StringRelatedField(read_only=True)
    status = serializers.ChoiceField(choices=BookLoan.Status.choices, read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    loan_period_days = serializers.IntegerField(min_value=1, required=False, default=30)

    class Meta:
        model = BookLoan
        fields = [
            'id',
            'user_id',
            'user',
            'book_copy',
            'book_copy_id',
            'borrowed_at',
            'due_date',
            'loan_period_days',
            'returned_at',
            'status',
            'is_overdue'
        ]
        read_only_fields = ['borrowed_at', 'returned_at', 'status', 'is_overdue']

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        book_copy: BookCopy = attrs.get('book_copy')
        if book_copy and book_copy.status != BookCopy.Status.AVAILABLE:
            raise serializers.ValidationError(
                {"book_copy_id": "Данный экземпляр не доступен к выдаче."}
            )
        return attrs

    def create(self, validated_data: dict[str, Any]) -> BookLoan:
        loan_period_days: int = validated_data.get('loan_period_days', 30)
        due_date = validated_data.get('due_date')

        with transaction.atomic():
            book_copy: BookCopy = validated_data['book_copy']

            # Блокируем для атомарности операции
            book_copy = BookCopy.objects.select_for_update().get(pk=book_copy.pk)

            if not book_copy.status == BookCopy.Status.AVAILABLE:
                raise serializers.ValidationError(
                    {"book_copy_id": ["Данный экземпляр не доступен к выдаче."]}
                )

            # Меняем статус экземпляра
            book_copy.status = BookCopy.Status.BORROWED
            book_copy.save(update_fields=['status'])

            # Расчет ожидаемой даты возврата книги
            if not due_date:
                due_date = timezone.localdate() + timedelta(days=loan_period_days)
            validated_data['due_date'] = due_date
            validated_data['loan_period_days'] = loan_period_days
            validated_data['status'] = BookLoan.Status.ACTIVE

            instance: BookLoan = super().create(validated_data)
            return instance
