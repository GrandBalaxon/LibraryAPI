from rest_framework.routers import DefaultRouter

from lending.views import BookLoanViewSet

app_name = 'lending'

router = DefaultRouter()
router.register(r'', BookLoanViewSet)

urlpatterns = router.urls
