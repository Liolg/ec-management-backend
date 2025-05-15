from django.contrib import admin
from .models import DirectMaterial, DirectLabor, CostSheet, CostSheetMaterial, CostSheetLabor, Product, ProductItem

admin.site.register( DirectMaterial )
admin.site.register( DirectLabor )
admin.site.register( CostSheet )
admin.site.register( CostSheetMaterial )
admin.site.register( CostSheetLabor )
admin.site.register( Product )
admin.site.register( ProductItem )
