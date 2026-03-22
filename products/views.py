from rest_framework import viewsets

from .models import DirectMaterial, DirectLabor, CostSheet, Product
from .serializers import (
    DirectMaterialSerializer,
    DirectLaborSerializer,
    CostSheetSerializer,
    ProductSerializer,
    SimpleProductSerializer
)


class DirectMaterialViewSet(viewsets.ModelViewSet):
    queryset = DirectMaterial.objects.all()
    serializer_class = DirectMaterialSerializer

class DirectLaborViewSet(viewsets.ModelViewSet):
    queryset = DirectLabor.objects.all()
    serializer_class = DirectLaborSerializer

class CostSheetViewSet(viewsets.ModelViewSet):
    queryset = CostSheet.objects.all()
    serializer_class = CostSheetSerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return SimpleProductSerializer

        return super().get_serializer_class()
