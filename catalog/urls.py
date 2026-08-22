from rest_framework.routers import DefaultRouter

from catalog.views import AuthorViewSet, GenreViewSet

app_name = 'catalog'

router = DefaultRouter()
router.register(r'authors', AuthorViewSet)
router.register(r'genres', GenreViewSet)

urlpatterns = router.urls
