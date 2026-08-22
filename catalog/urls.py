from rest_framework.routers import DefaultRouter

from catalog.views import AuthorViewSet, GenreViewSet, PublisherViewSet, BookViewSet, BookEditionViewSet

app_name = 'catalog'

router = DefaultRouter()
router.register(r'authors', AuthorViewSet)
router.register(r'genres', GenreViewSet)
router.register(r'publishers', PublisherViewSet)
router.register(r'books', BookViewSet)
router.register(r'editions', BookEditionViewSet)

urlpatterns = router.urls
