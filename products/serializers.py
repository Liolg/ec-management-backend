from rest_framework import serializers

from .models import DirectMaterial, DirectLabor, CostSheet, CostSheetMaterial, CostSheetLabor, Product, ProductItem

class DirectMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model=DirectMaterial
        fields="__all__"

class DirectLaborSerializer(serializers.ModelSerializer):
    class Meta:
        model=DirectLabor
        fields="__all__"

class CostSheetSerializer(serializers.ModelSerializer):
    class Meta:
        model=CostSheet
        fields=['total_cost', 'selling_price', 'unit']

class CostSheetMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model=CostSheetMaterial
        fields="__all__"

class CostSheetLaborSerializer(serializers.ModelSerializer):
    class Meta:
        model=CostSheetLabor
        fields="__all__"

class ProductSerializer(serializers.ModelSerializer):
    cost_sheet=CostSheetSerializer()
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
        deserialized_data['product']=deserialized_data.get('product').get('id')
        return deserialized_data
