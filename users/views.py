from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets, generics, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView

from catalog.utils import standard_viewset_schema
from users.models import CustomUser
from users.permissions import IsLibrarian, IsOwnerOrLibrarian
from users.serializers import UserSerializer


@extend_schema(tags=["Аутентификация"])
@extend_schema_view(
    post=extend_schema(
        summary="Получить JWT токен",
        description=(
            "Принимает учётные данные пользователя (email и пароль) и возвращает "
            "пару JWT токенов (access и refresh) для аутентификации."
        ),
    )
)
class CustomTokenObtainPairView(TokenObtainPairView):
    pass


@extend_schema(tags=["Аутентификация"])
@extend_schema_view(
    post=extend_schema(
        summary="Обновить JWT токен",
        description="Принимает refresh токен и возвращает новый access токен, если refresh токен действителен.",
    )
)
class CustomTokenRefreshView(TokenRefreshView):
    pass


@extend_schema(tags=["Пользователи"], summary="Регистрация")
class RegisterView(generics.CreateAPIView):
    """Регистрация нового читателя."""
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


@extend_schema_view(
    destroy=extend_schema(
        summary="Деактивация пользователя",
        description="Деактивирует учётную запись пользователя (устанавливает is_active=False).",
    )
)
@standard_viewset_schema(tags=["Пользователи"])
class UserViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Вьюсет для пользователей."""
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ["list", "destroy"]:
            return [IsAuthenticated(), IsLibrarian()]
        if self.action in ["update", "partial_update", "retrieve"]:
            return [IsAuthenticated(), IsOwnerOrLibrarian()]
        if self.action == "me":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsLibrarian()]

    def get_queryset(self):
        user = self.request.user
        if user.role == CustomUser.Role.LIBRARIAN:
            return CustomUser.objects.all()
        return CustomUser.objects.filter(pk=user.pk)

    @extend_schema(summary="Получить свой профиль", responses={200: UserSerializer})
    @action(detail=False, methods=["get"])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    def perform_destroy(self, instance):
        """Вместо удаления деактивируем пользователя."""
        instance.is_active = False
        instance.save(update_fields=["is_active"])
