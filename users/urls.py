from django.urls import path
from rest_framework import routers
from rest_framework.permissions import AllowAny

from users.views import UserViewSet, RegisterView, CustomTokenObtainPairView, CustomTokenRefreshView

app_name = 'users'

router = routers.DefaultRouter()

router.register(r'', UserViewSet)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),

    # JWT-эндпоинты аутентификации
    path('token/', CustomTokenObtainPairView.as_view(permission_classes=[AllowAny]), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(permission_classes=[AllowAny]), name='token_refresh'),
]
urlpatterns += router.urls
