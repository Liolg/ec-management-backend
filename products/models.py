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
    material = models.ForeignKey(DirectMaterial, on_delete=models.PROTECT)
    cost_sheet = models.ForeignKey(CostSheet, on_delete=models.CASCADE)
    qty = models.IntegerField(blank=True)
    total_cost = models.IntegerField(blank=True)
    
    class Meta:
        constraints = [
                models.UniqueConstraint( fields = [ "material", "cost_sheet" ], name = "unique_cost_sheet_material")
        ]

class CostSheetLabor(models.Model):
    labor = models.ForeignKey(DirectLabor, on_delete=models.PROTECT)
    cost_sheet = models.ForeignKey(CostSheet, on_delete=models.CASCADE)
    qty = models.IntegerField(blank=True)
    total_cost = models.IntegerField(blank=True)
    
    class Meta:
        constraints = [
                models.UniqueConstraint( fields = [ "labor", "cost_sheet" ], name = "unique_cost_sheet_labor")
        ]

class Product(models.Model):
    name = models.CharField(max_length=50)
    cost_sheet = models.ForeignKey("CostSheet", on_delete=models.PROTECT)

    def __str__(self):
        return self.name

    @property
    def current_stock(self):
        from django.db.models import Sum
        in_qty  = self.stock_movements.filter(direction='IN').aggregate(t=Sum('qty'))['t'] or 0
        out_qty = self.stock_movements.filter(direction='OUT').aggregate(t=Sum('qty'))['t'] or 0
        return in_qty - out_qty


class StockMovement(models.Model):
    DIRECTION_IN  = 'IN'
    DIRECTION_OUT = 'OUT'
    DIRECTION_CHOICES = [
        ('IN',  'Stock In'),
        ('OUT', 'Stock Out'),
    ]

    product    = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='stock_movements')
    qty        = models.PositiveIntegerField()
    direction  = models.CharField(max_length=3, choices=DIRECTION_CHOICES)
    unit_cost  = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    date       = models.DateField()
    reference  = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-date', '-created_at')

    def __str__(self):
        return f"{self.direction} {self.qty} x {self.product} on {self.date}"

class ProductItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    qty = models.IntegerField(blank=True)
    entry_line=models.OneToOneField(Line, on_delete=models.CASCADE, related_name="product_item")

    @property
    def total_price(self):
        return self.qty * (self.product.cost_sheet.selling_price or 0)

    def total_price_display(self):
        return f"${self.total_price:.2f}"

    @property
    def total_cost(self):
        return self.qty * (self.product.cost_sheet.total_cost or 0)

    def total_cost_display(self):
        return f"${self.total_cost:.2f}"
