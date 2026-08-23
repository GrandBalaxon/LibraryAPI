from rest_framework import serializers

from users.models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для кастомной модели пользователя."""
    loan_ids = serializers.PrimaryKeyRelatedField(
        source='loans',
        many=True,
        read_only=True
    )

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
        ]
        extra_kwargs = {
            'email': {'read_only': True},
            'password': {'write_only': True},
            'role': {'read_only': True},
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(password=password, **validated_data)
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

    def validate_phone_number(self, value):
        normalized = CustomUser.normalize_phone_number(value)
        if normalized is None:
            raise serializers.ValidationError('Некорректный номер телефона.')
        return normalized
