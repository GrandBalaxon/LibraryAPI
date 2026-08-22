from rest_framework.routers import DefaultRouter

from catalog.views import AuthorViewSet

app_name = 'catalog'

router = DefaultRouter()
router.register(r'authors', AuthorViewSet)

urlpatterns = router.urls
