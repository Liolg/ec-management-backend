from django.db import models
from ec_accounts.models import Line

class DirectMaterial(models.Model):
    name = models.CharField(max_length=50)
    unit = models.CharField(max_length=10)
    cost_by_unit = models.PositiveIntegerField(blank=True)

    def __str__(self) -> str:
        return self.name

class DirectLabor(models.Model):
    name = models.CharField(max_length=50)
    time_unit = models.CharField(max_length=10)
    cost_by_unit = models.FloatField()
    class Meta:
        constraints = [
                models.UniqueConstraint( fields = [ "name", "cost_by_unit", "time_unit" ], name = "unique_labor")
        ]
    def __str__(self) -> str:
        return self.name

class CostSheet(models.Model):
    #cost_sheet = models.ForeignKey("self", on_delete=models.PROTECT, null=True, blank=True)
    material = models.ManyToManyField(DirectMaterial, through="CostSheetMaterial", related_name='cost_sheets')
    labor = models.ManyToManyField(DirectLabor, through="CostSheetLabor", related_name='cost_sheets')
    name = models.CharField(max_length=50)
    manufacturing_overhead = models.IntegerField(blank=True, null=True) # = indirect material + indirect labor + factory related costs + others
    total_manufacturing_cost = models.IntegerField(blank=True, null=True) # = direct material + direct labor + overhead
    non_manufacturing_cost = models.IntegerField(blank=True, null=True) # = selling + administrative
    total_cost = models.IntegerField(blank=True, null=True)
    profit_margin = models.IntegerField(blank=True, null=True) # %
    selling_price = models.IntegerField(blank=True, null=True) # = total cost / (1-margin)
    unit = models.CharField(max_length=10, blank=True, null=True)
    #cost_by_unit = models.IntegerField(blank=True)

    def __str__(self) -> str:
        return self.name

class CostSheetMaterial(models.Model):
    material = models.ForeignKey(DirectMaterial, on_delete=models.CASCADE)
    cost_sheet = models.ForeignKey(CostSheet, on_delete=models.CASCADE)
    qty = models.IntegerField(blank=True)
    total_cost = models.IntegerField(blank=True)
    
    class Meta:
        constraints = [
                models.UniqueConstraint( fields = [ "material", "cost_sheet" ], name = "unique_cost_sheet_material")
        ]

class CostSheetLabor(models.Model):
    labor = models.ForeignKey(DirectLabor, on_delete=models.CASCADE)
    cost_sheet = models.ForeignKey(CostSheet, on_delete=models.CASCADE)
    qty = models.IntegerField(blank=True)
    total_cost = models.IntegerField(blank=True)
    
    class Meta:
        constraints = [
                models.UniqueConstraint( fields = [ "labor", "cost_sheet" ], name = "unique_cost_sheet_labor")
        ]

class Product(models.Model):
    name = models.CharField(max_length=50)
    cost_sheet = models.ForeignKey("CostSheet", on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class ProductItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    qty = models.IntegerField(blank=True)
    entry_line=models.OneToOneField(Line, on_delete=models.CASCADE)

    @property
    def total_price(self):
        return self.qty * self.product.cost_sheet.selling_price
    
    def total_price_display(self):
        return f"${self.total_price:.2f}"

    @property
    def total_cost(self):
        return self.qty * self.product.cost_sheet.total_cost
    
    def total_cost_display(self):
        return f"${self.total_cost:.2f}"
