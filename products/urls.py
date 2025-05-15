from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import DirectMaterialViewSet, DirectLaborViewSet, CostSheetViewSet, ProductViewSet

router = SimpleRouter()
router.register("materials", DirectMaterialViewSet, basename="material")
router.register("labors", DirectLaborViewSet, basename="labor")
router.register("costsheets", CostSheetViewSet, basename="costsheet")
router.register("products", ProductViewSet, basename="product")

urlpatterns = router.urls
