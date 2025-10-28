from rest_framework.routers import DefaultRouter
from .views import AccountViewSet, EcAccountEntryViewSet

router = DefaultRouter()
router.register(r'accounts', AccountViewSet)
router.register(r'entries', EcAccountEntryViewSet)

urlpatterns = router.urls
