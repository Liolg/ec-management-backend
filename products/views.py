from django.db.models.deletion import ProtectedError
from rest_framework import viewsets, mixins, status
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


class ConflictDeleteMixin:
    delete_conflict_message = 'Resource cannot be deleted because it is referenced.'

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {'detail': self.delete_conflict_message},
                status=status.HTTP_409_CONFLICT,
            )


class DirectMaterialViewSet(ConflictDeleteMixin, viewsets.ModelViewSet):
    queryset = DirectMaterial.objects.all()
    serializer_class = DirectMaterialSerializer
    delete_conflict_message = 'Material cannot be deleted because it is used by a cost sheet.'


class DirectLaborViewSet(ConflictDeleteMixin, viewsets.ModelViewSet):
    queryset = DirectLabor.objects.all()
    serializer_class = DirectLaborSerializer
    delete_conflict_message = 'Labor cannot be deleted because it is used by a cost sheet.'


class CostSheetViewSet(ConflictDeleteMixin, viewsets.ModelViewSet):
    queryset = CostSheet.objects.prefetch_related(
        'material', 'labor',
        'costsheetmaterial_set__material',
        'costsheetlabor_set__labor',
    ).all()
    serializer_class = CostSheetSerializer
    delete_conflict_message = 'Cost sheet cannot be deleted because it is used by a product.'

    @action(detail=True, methods=['post'])
    def calculate(self, request, pk=None):
        cost_sheet = self.get_object()
        cost_sheet = calculate_cost_sheet(cost_sheet)
        return Response(CostSheetSerializer(cost_sheet).data)


class ProductViewSet(ConflictDeleteMixin, viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    delete_conflict_message = 'Product cannot be deleted because it has transaction or inventory history.'

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
