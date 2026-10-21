from rest_framework.routers import DefaultRouter

from catalog.views import AuthorViewSet, GenreViewSet, PublisherViewSet, WorkViewSet, BookEditionViewSet

app_name = 'catalog'

router = DefaultRouter()
router.register(r'authors', AuthorViewSet)
router.register(r'genres', GenreViewSet)
router.register(r'publishers', PublisherViewSet)
router.register(r'books', WorkViewSet)
router.register(r'editions', BookEditionViewSet)

urlpatterns = router.urls
