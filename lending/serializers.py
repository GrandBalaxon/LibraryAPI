from django.utils import timezone
from rest_framework import serializers

from catalog.models import BookEdition
from lending.models import BookLoan


class BookLoanSerializer(serializers.ModelSerializer):
    """Сериализатор выдачи книги."""
    edition = serializers.PrimaryKeyRelatedField(queryset=BookEdition.objects.all())
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    status = serializers.ChoiceField(choices=BookLoan.Status.choices, read_only=True)

    class Meta:
        model = BookLoan
        fields = [
            'id',
            'user',
            'edition',
            'borrowed_at',
            'due_date',
            'returned_at',
            'status',
            'is_overdue'
        ]
        read_only_fields = ['borrowed_at', 'due_date', 'returned_at', 'status', 'is_overdue']

    def validate(self, attrs):
        edition = attrs.get('edition')
        if edition.available_copies <= 0:
            raise serializers.ValidationError("Нет доступных экземпляров этого издания.")
        return attrs

    def create(self, validated_data):
        from django.db import transaction
        with transaction.atomic():
            edition = validated_data['edition']
            # Блокируем для атомарности операции
            edition = BookEdition.objects.select_for_update().get(pk=edition.pk)
            if edition.available_copies <= 0:
                raise serializers.ValidationError("Нет доступных экземпляров этого издания.")
            edition.available_copies -= 1
            edition.save(update_fields=['available_copies'])

            validated_data['user'] = self.context['request'].user
            validated_data['status'] = BookLoan.Status.ACTIVE
            return super().create(validated_data)

    def update(self, instance, validated_data):
        # Обрабатываем только случай возврата (меняем статус на RETURNED)
        from django.db import transaction
        with transaction.atomic():
            old_status = instance.status
            new_status = validated_data.get('status', old_status)
            if old_status != BookLoan.Status.RETURNED and new_status == BookLoan.Status.RETURNED:
                edition = BookEdition.objects.select_for_update().get(pk=instance.edition_id)
                edition.available_copies += 1
                edition.save(update_fields=['available_copies'])
                validated_data['returned_at'] = validated_data.get('returned_at') or timezone.now()
            instance = super().update(instance, validated_data)
            return instance
