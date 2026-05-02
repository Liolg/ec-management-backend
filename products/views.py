from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import DirectMaterial, DirectLabor, CostSheet, Product, StockMovement
from .serializers import (
    DirectMaterialSerializer,
    DirectLaborSerializer,
    CostSheetSerializer,
    ProductSerializer,
    SimpleProductSerializer,
    StockMovementSerializer,
    ProductStockSerializer,
)
from .services import calculate_cost_sheet


class DirectMaterialViewSet(viewsets.ModelViewSet):
    queryset = DirectMaterial.objects.all()
    serializer_class = DirectMaterialSerializer


class DirectLaborViewSet(viewsets.ModelViewSet):
    queryset = DirectLabor.objects.all()
    serializer_class = DirectLaborSerializer


class CostSheetViewSet(viewsets.ModelViewSet):
    queryset = CostSheet.objects.all()
    serializer_class = CostSheetSerializer

    @action(detail=True, methods=['post'])
    def calculate(self, request, pk=None):
        cost_sheet = self.get_object()
        cost_sheet = calculate_cost_sheet(cost_sheet)
        return Response(CostSheetSerializer(cost_sheet).data)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return SimpleProductSerializer
        return super().get_serializer_class()

    @action(detail=True, methods=['get'])
    def stock(self, request, pk=None):
        product = self.get_object()
        data = {
            'current_stock': product.current_stock,
            'movements': product.stock_movements.all(),
        }
        return Response(ProductStockSerializer(data).data)


class StockAdjustmentViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = StockMovement.objects.select_related('product').all()
    serializer_class = StockMovementSerializer
