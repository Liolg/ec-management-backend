from django.contrib import admin
from .models import DirectMaterial, DirectLabor, CostSheet, CostSheetMaterial, CostSheetLabor, Product, ProductItem 

admin.site.register( DirectMaterial )
admin.site.register( DirectLabor )
admin.site.register( CostSheet )
admin.site.register( CostSheetMaterial )
admin.site.register( CostSheetLabor )
admin.site.register( Product )

@admin.register( ProductItem )
class ProductItemAdmin(admin.ModelAdmin):
    readonly_fields = ('total_cost', "total_price")
