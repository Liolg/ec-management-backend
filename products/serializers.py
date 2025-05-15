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
        fields="__all__"

class CostSheetMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model=CostSheetMaterial
        fields="__all__"

class CostSheetLaborSerializer(serializers.ModelSerializer):
    class Meta:
        model=CostSheetLabor
        fields="__all__"

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model=Product
        fields="__all__"

class ProductItemSerializer(serializers.ModelSerializer):
    class Meta:
        model=ProductItem
        fields="__all__"
