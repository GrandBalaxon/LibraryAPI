from typing import Any

from django.db import models
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class ChangeReasonMixin(serializers.Serializer):
    """
    Миксин для валидации причины изменения критических полей.
    Наследники должны определить critical_fields (список) и has_dependencies (метод проверки).
    """
    change_reason = serializers.CharField(
        write_only=True,
        required=False,
        help_text="Укажите причину изменения критических данных"
    )

    class Meta:
        fields = ['change_reason']

    def update(self, instance: models.Model, validated_data: dict[str, Any]) -> models.Model:
        change_reason = validated_data.pop('change_reason', None)
        critical_fields = getattr(self, 'critical_fields', [])

        is_critical_change = False
        for field in critical_fields:
            if field in validated_data and validated_data[field] != getattr(instance, field):
                is_critical_change = True
                break

        # Проверка зависимости (например, есть ли копии)
        if is_critical_change and hasattr(self, 'has_dependencies') and not self.has_dependencies(instance):
            is_critical_change = False

        if is_critical_change and not change_reason:
            raise ValidationError(
                {"change_reason": ["Вы изменяете критическое поле. Укажите причину."]}
            )

        if change_reason:
            instance._change_reason = change_reason

        return super().update(instance, validated_data)
