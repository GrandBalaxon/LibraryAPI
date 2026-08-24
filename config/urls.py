from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),

    path("api/user/", include("users.urls"), name="users"),
    path('api/catalog/', include('catalog.urls'), name='catalog'),
    path('api/lending/', include('lending.urls'), name='lending'),

    # drf-spectacular документирование
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),

    path('', RedirectView.as_view(url='api/docs/')),
]
