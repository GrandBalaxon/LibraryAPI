from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.request import Request
from rest_framework.views import APIView

from users.models import CustomUser


class IsLibrarian(BasePermission):
    """Разрешение только для библиотекарей."""
    message = 'Только библиотекарь может выполнять это действие.'

    def has_permission(self, request: Request, view: APIView) -> bool:
        user: CustomUser = request.user
        return (
            user.is_authenticated and user.role == CustomUser.Role.LIBRARIAN
        )


class IsLibrarianOrReadOnly(BasePermission):
    """Чтение для всех аутентифицированных, запись — только библиотекарям."""
    message = 'Только библиотекарь может изменять данные.'

    def has_permission(self, request: Request, view: APIView) -> bool:
        user: CustomUser = request.user

        if not user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return user.role == CustomUser.Role.LIBRARIAN


class IsOwnerOrLibrarian(BasePermission):
    """
    Обычный пользователь может просматривать и изменять только свой профиль, библиотекарь — профиль любого.
    """
    message = 'Вы можете изменять только свой профиль.'

    def has_object_permission(self, request: Request, view: APIView, obj: CustomUser) -> bool:
        user: CustomUser = request.user

        if request.method in SAFE_METHODS:
            return True
        if user.role == CustomUser.Role.LIBRARIAN:
            return True
        return obj.pk == user.pk
