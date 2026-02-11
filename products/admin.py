from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import DirectMaterial, DirectLabor, CostSheet, CostSheetMaterial, CostSheetLabor, Product, ProductItem

@admin.register( DirectMaterial )
class DirectMaterialAdmin(ModelAdmin):
    pass

@admin.register( DirectLabor )
class DirectLaborAdmin(ModelAdmin):
    pass

@admin.register( CostSheet )
class CostSheetAdmin(ModelAdmin):
    pass

@admin.register( CostSheetMaterial )
class CostSheetMaterialAdmin(ModelAdmin):
    pass

@admin.register( CostSheetLabor )
class CostSheetLaborAdmin(ModelAdmin):
    pass

@admin.register( Product )
class ProductAdmin(ModelAdmin):
    pass

@admin.register( ProductItem )
class ProductItemAdmin(admin.ModelAdmin):
    readonly_fields = ('total_cost', "total_price")
