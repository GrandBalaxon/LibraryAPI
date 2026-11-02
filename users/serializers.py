from typing import Any

from rest_framework import serializers

from catalog.mixins import ChangeReasonMixin
from users.models import CustomUser


class UserSerializer(ChangeReasonMixin, serializers.ModelSerializer):
    """Сериализатор для кастомной модели пользователя."""
    loan_ids = serializers.PrimaryKeyRelatedField(
        source='loans',
        many=True,
        read_only=True
    )

    critical_fields = ['email', 'phone_number']

    class Meta:
        model = CustomUser
        fields = [
            'id',
            'email',
            'password',
            'first_name',
            'last_name',
            'middle_name',
            'phone_number',
            'place_of_birth',
            'role',
            'loan_ids'
        ] + ChangeReasonMixin.Meta.fields
        extra_kwargs = {
            'password': {'write_only': True},
            'role': {'read_only': True},
        }

    def create(self, validated_data: dict[str, Any]) -> CustomUser:
        validated_data.pop('change_reason', None)
        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(password=password, **validated_data)
        return user

    def update(self, instance: CustomUser, validated_data: dict[str, Any]) -> CustomUser:
        password = validated_data.pop('password', None)

        # super() запустит цепочку: сначала ChangeReasonMixin, затем ModelSerializer.update()
        instance = super().update(instance, validated_data)

        # Обрабатываем пароль (если он был передан)
        if password:
            instance.set_password(password)
            instance.save(update_fields=['password'])

        return instance

    def validate_phone_number(self, value: str) -> str:
        normalized = CustomUser.normalize_phone_number(value)
        if normalized is None:
            raise serializers.ValidationError('Некорректный номер телефона.')
        return normalized
