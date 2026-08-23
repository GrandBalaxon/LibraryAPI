from rest_framework import serializers

from users.models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для кастомной модели пользователя."""

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
            'role'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'role': {'read_only': True},
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(password=password, **validated_data)
        return user
