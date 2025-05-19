from django.db import models
from ec_accounts.models import EcAccountEntry

class DirectMaterial(models.Model):
    name = models.CharField(max_length=50)
    unit = models.CharField(max_length=10)
    cost_by_unit = models.PositiveIntegerField()

    def __str__(self) -> str:
        return self.name

class DirectLabor(models.Model):
    name = models.CharField(max_length=50)
    time_unit = models.CharField(max_length=10)
    const_by_unit = models.PositiveIntegerField()

    def __str__(self) -> str:
        return self.name

class CostSheet(models.Model):
    cost_sheet = models.ForeignKey("self", on_delete=models.PROTECT, null=True, blank=True)
    material = models.ManyToManyField(DirectMaterial, through="CostSheetMaterial")
    labor = models.ManyToManyField(DirectLabor, through="CostSheetLabor")
    name = models.CharField(max_length=50)
    manufacturing_overhead = models.IntegerField() # = indirect material + indirect labor + factory related costs + others
    total_manufacturing_cost = models.IntegerField() # = direct material + direct labor + overhead
    non_manufacturing_cost = models.IntegerField() # = selling + administrative
    total_cost = models.IntegerField()
    profit_margin = models.IntegerField() # %
    selling_price = models.IntegerField() # = total cost / (1-margin)

    def __str__(self) -> str:
        return self.name

class CostSheetMaterial(models.Model):
    material = models.ForeignKey(DirectMaterial, on_delete=models.CASCADE)
    cost_sheet = models.ForeignKey(CostSheet, on_delete=models.CASCADE)
    qty = models.IntegerField()
    total_cost = models.IntegerField()
    
    class Meta:
        constraints = [
                models.UniqueConstraint( fields = [ "material", "cost_sheet" ], name = "unique_cost_sheet_material")
        ]

class CostSheetLabor(models.Model):
    labor = models.ForeignKey(DirectLabor, on_delete=models.CASCADE)
    cost_sheet = models.ForeignKey(CostSheet, on_delete=models.CASCADE)
    qty = models.IntegerField()
    total_cost = models.IntegerField()
    
    class Meta:
        constraints = [
                models.UniqueConstraint( fields = [ "labor", "cost_sheet" ], name = "unique_cost_sheet_labor")
        ]

class Product(models.Model):
    name = models.CharField(max_length=50)
    cost_sheet = models.ForeignKey("CostSheet", on_delete=models.CASCADE)
    unit = models.CharField(max_length=10)
    cost_by_unit = models.IntegerField()

    def __str__(self):
        return self.name

class ProductItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    ec_acc_entry = models.ForeignKey(EcAccountEntry, on_delete=models.CASCADE)
    qty = models.IntegerField()

    @property
    def total_price(self):
        return self.qty * self.product.cost_by_unit
    
    def total_price_display(self):
        return f"${self.total_price:.2f}"

