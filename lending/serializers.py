from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from catalog.models import BookEdition
from lending.models import BookLoan
from users.models import CustomUser


class BookLoanSerializer(serializers.ModelSerializer):
    """Сериализатор выдачи книги."""
    book = serializers.PrimaryKeyRelatedField(queryset=BookEdition.objects.all())
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
            'book',
            'borrowed_at',
            'due_date',
            'loan_period_days',
            'returned_at',
            'status',
            'is_overdue'
        ]
        read_only_fields = ['borrowed_at', 'returned_at', 'status', 'is_overdue']

    def validate(self, attrs):
        book = attrs.get('book')
        if book.available_copies <= 0:
            raise serializers.ValidationError("Нет доступных экземпляров этого издания.")
        return attrs

    def create(self, validated_data):
        loan_period_days = validated_data.get('loan_period_days', 30)
        due_date = validated_data.get('due_date')

        with transaction.atomic():
            book = validated_data['book']
            # Блокируем для атомарности операции
            book = BookEdition.objects.select_for_update().get(pk=book.pk)
            if book.available_copies <= 0:
                raise serializers.ValidationError("Нет доступных экземпляров этого издания.")

            # Уменьшаем количество доступных экземпляров
            book.available_copies -= 1
            book.save(update_fields=['available_copies'])

            # Расчет ожидаемой даты возврата книги
            if not due_date:
                due_date = timezone.localdate() + timedelta(days=loan_period_days)
            validated_data['due_date'] = due_date
            validated_data['loan_period_days'] = loan_period_days

            validated_data['status'] = BookLoan.Status.ACTIVE
            return super().create(validated_data)

    def update(self, instance, validated_data):
        # Обрабатываем только случай возврата (меняем статус на RETURNED)
        with transaction.atomic():
            old_status = instance.status
            new_status = validated_data.get('status', old_status)

            if old_status != BookLoan.Status.RETURNED and new_status == BookLoan.Status.RETURNED:
                book = BookEdition.objects.select_for_update().get(pk=instance.book_id)
                book.available_copies += 1
                book.save(update_fields=['available_copies'])
                validated_data['returned_at'] = validated_data.get('returned_at') or timezone.now()

            instance = super().update(instance, validated_data)
            return instance
