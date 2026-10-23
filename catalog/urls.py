from rest_framework.routers import DefaultRouter

from catalog.views import AuthorViewSet, GenreViewSet, PublisherViewSet, WorkViewSet, EditionViewSet, BookCopyViewSet

app_name = 'catalog'

router = DefaultRouter()
router.register(r'authors', AuthorViewSet)
router.register(r'genres', GenreViewSet)
router.register(r'publishers', PublisherViewSet)
router.register(r'works', WorkViewSet)
router.register(r'editions', EditionViewSet, basename='edition')
router.register(r'copies', BookCopyViewSet, basename='bookcopy')

urlpatterns = router.urls
