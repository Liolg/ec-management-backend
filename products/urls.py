from rest_framework.routers import DefaultRouter

from .views import DirectMaterialViewSet, DirectLaborViewSet, CostSheetViewSet, ProductViewSet

router = DefaultRouter()
router.register(r"materials", DirectMaterialViewSet)
router.register(r"labors", DirectLaborViewSet)
router.register(r"costsheets", CostSheetViewSet)
router.register(r"products", ProductViewSet)

urlpatterns = router.urls
