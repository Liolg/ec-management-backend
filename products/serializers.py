from rest_framework import serializers
from django.db import transaction

from .models import DirectMaterial, DirectLabor, CostSheet, CostSheetMaterial, CostSheetLabor, Product, ProductItem, StockMovement
from .services import calculate_cost_sheet

class DirectMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model=DirectMaterial
        fields="__all__"

class DirectLaborSerializer(serializers.ModelSerializer):
    class Meta:
        model=DirectLabor
        fields="__all__"

class CostSheetMaterialSerializer(serializers.ModelSerializer):
    material = serializers.PrimaryKeyRelatedField(queryset=DirectMaterial.objects.all())
    qty = serializers.IntegerField(min_value=1)

    class Meta:
        model=CostSheetMaterial
        fields=['id', 'material', 'qty', 'total_cost']
        read_only_fields=['id', 'total_cost']

class CostSheetLaborSerializer(serializers.ModelSerializer):
    labor = serializers.PrimaryKeyRelatedField(queryset=DirectLabor.objects.all())
    qty = serializers.IntegerField(min_value=1)

    class Meta:
        model=CostSheetLabor
        fields=['id', 'labor', 'qty', 'total_cost']
        read_only_fields=['id', 'total_cost']


class CostSheetSerializer(serializers.ModelSerializer):
    material = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    labor = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    material_lines = CostSheetMaterialSerializer(
        source='costsheetmaterial_set', many=True, required=False,
    )
    labor_lines = CostSheetLaborSerializer(
        source='costsheetlabor_set', many=True, required=False,
    )

    class Meta:
        model=CostSheet
        fields=[
            'id', 'name', 'manufacturing_overhead', 'total_manufacturing_cost',
            'non_manufacturing_cost', 'total_cost', 'profit_margin',
            'selling_price', 'unit', 'material', 'labor',
            'material_lines', 'labor_lines',
        ]
        read_only_fields=[
            'total_manufacturing_cost', 'total_cost', 'selling_price',
        ]

    def validate(self, attrs):
        for key, resource_key in (
            ('costsheetmaterial_set', 'material'),
            ('costsheetlabor_set', 'labor'),
        ):
            lines = attrs.get(key)
            if lines is None:
                continue
            resource_ids = [line[resource_key].pk for line in lines]
            if len(resource_ids) != len(set(resource_ids)):
                raise serializers.ValidationError(
                    {resource_key + '_lines': f'Duplicate {resource_key} ids are not allowed.'}
                )
        return attrs

    @staticmethod
    def _replace_material_lines(cost_sheet, lines):
        cost_sheet.costsheetmaterial_set.all().delete()
        CostSheetMaterial.objects.bulk_create([
            CostSheetMaterial(cost_sheet=cost_sheet, total_cost=0, **line)
            for line in lines
        ])

    @staticmethod
    def _replace_labor_lines(cost_sheet, lines):
        cost_sheet.costsheetlabor_set.all().delete()
        CostSheetLabor.objects.bulk_create([
            CostSheetLabor(cost_sheet=cost_sheet, total_cost=0, **line)
            for line in lines
        ])

    @transaction.atomic
    def create(self, validated_data):
        material_lines = validated_data.pop('costsheetmaterial_set', [])
        labor_lines = validated_data.pop('costsheetlabor_set', [])
        cost_sheet = CostSheet.objects.create(**validated_data)
        self._replace_material_lines(cost_sheet, material_lines)
        self._replace_labor_lines(cost_sheet, labor_lines)
        return calculate_cost_sheet(cost_sheet)

    @transaction.atomic
    def update(self, instance, validated_data):
        material_lines = validated_data.pop('costsheetmaterial_set', serializers.empty)
        labor_lines = validated_data.pop('costsheetlabor_set', serializers.empty)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if material_lines is not serializers.empty:
            self._replace_material_lines(instance, material_lines)
        if labor_lines is not serializers.empty:
            self._replace_labor_lines(instance, labor_lines)
        return calculate_cost_sheet(instance)

class ProductSerializer(serializers.ModelSerializer):
    cost_sheet=CostSheetSerializer()
    class Meta:
        model=Product
        fields=['id', 'name', 'cost_sheet']

class SimpleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model=Product
        fields=['id', 'name', 'cost_sheet']

class ProductItemSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    name=serializers.CharField(source='product.name',read_only=True)
    product=serializers.IntegerField(source='product.id')
    total_cost=serializers.CharField(source='product.cost_sheet.total_cost',read_only=True)
    selling_price=serializers.CharField(source='product.cost_sheet.selling_price',read_only=True)
    unit=serializers.CharField(source='product.cost_sheet.unit',read_only=True)
    class Meta:
        model=ProductItem
        fields=['id','qty','name','total_cost','selling_price','unit','product']

    def to_internal_value(self, data):
        deserialized_data=super().to_internal_value(data)
        product = deserialized_data.get('product')
        if product is None:
            raise serializers.ValidationError({'product': 'This field is required.'})
        deserialized_data['product'] = product['id']
        return deserialized_data


class StockMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model  = StockMovement
        fields = ['id', 'product', 'qty', 'direction', 'unit_cost', 'date', 'reference', 'created_at']
        read_only_fields = ['created_at']


class ProductStockSerializer(serializers.Serializer):
    current_stock = serializers.IntegerField()
    movements     = StockMovementSerializer(many=True)
