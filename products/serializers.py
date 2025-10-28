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
    product = ProductSerializer()
    class Meta:
        model=ProductItem
        fields=['id', 'qty', 'product']
