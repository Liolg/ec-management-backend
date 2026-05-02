from django.db import models
from ec_accounts.models import Account, Entry
from products.models import Product

PAYMENT_CHOICES = [('cash', 'Cash'), ('credit', 'Credit / Invoice')]
STATUS_CHOICES  = [('confirmed', 'Confirmed'), ('voided', 'Voided')]


class BusinessConfig(models.Model):
    company_name       = models.CharField(max_length=100)
    currency           = models.CharField(max_length=10, default='USD')
    cash_account       = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='+')
    receivable_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='+')
    payable_account    = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='+')
    revenue_account    = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='+')
    cogs_account       = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    inventory_account  = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='+')
    expense_account    = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='+')

    class Meta:
        verbose_name = 'Business Configuration'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        return cls.objects.filter(pk=1).first()

    def __str__(self):
        return self.company_name


class Sale(models.Model):
    product        = models.ForeignKey(Product, on_delete=models.PROTECT)
    qty            = models.PositiveIntegerField()
    unit_price     = models.DecimalField(max_digits=18, decimal_places=2)
    total_amount   = models.DecimalField(max_digits=18, decimal_places=2)
    date           = models.DateField()
    customer_name  = models.CharField(max_length=100, blank=True)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default='cash')
    status         = models.CharField(max_length=12, choices=STATUS_CHOICES, default='confirmed')
    entry          = models.OneToOneField(Entry, on_delete=models.PROTECT, related_name='sale')
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-date', '-created_at')

    def __str__(self):
        return f"Sale #{self.id} — {self.product.name} x {self.qty}"


class Purchase(models.Model):
    product        = models.ForeignKey(Product, on_delete=models.PROTECT)
    qty            = models.PositiveIntegerField()
    unit_cost      = models.DecimalField(max_digits=18, decimal_places=2)
    total_amount   = models.DecimalField(max_digits=18, decimal_places=2)
    date           = models.DateField()
    supplier_name  = models.CharField(max_length=100, blank=True)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default='cash')
    status         = models.CharField(max_length=12, choices=STATUS_CHOICES, default='confirmed')
    entry          = models.OneToOneField(Entry, on_delete=models.PROTECT, related_name='purchase')
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-date', '-created_at')

    def __str__(self):
        return f"Purchase #{self.id} — {self.product.name} x {self.qty}"


class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('rent',      'Rent'),
        ('utilities', 'Utilities'),
        ('salaries',  'Salaries'),
        ('marketing', 'Marketing'),
        ('supplies',  'Supplies'),
        ('transport', 'Transport'),
        ('other',     'Other'),
    ]

    description    = models.CharField(max_length=200)
    category       = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    amount         = models.DecimalField(max_digits=18, decimal_places=2)
    date           = models.DateField()
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default='cash')
    status         = models.CharField(max_length=12, choices=STATUS_CHOICES, default='confirmed')
    entry          = models.OneToOneField(Entry, on_delete=models.PROTECT, related_name='expense')
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-date', '-created_at')

    def __str__(self):
        return f"Expense #{self.id} — {self.category}: {self.description}"


class Payment(models.Model):
    DIRECTION_RECEIVED = 'received'
    DIRECTION_MADE     = 'made'
    DIRECTION_CHOICES  = [
        ('received', 'Received from customer'),
        ('made',     'Made to supplier'),
    ]

    direction         = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    amount            = models.DecimalField(max_digits=18, decimal_places=2)
    date              = models.DateField()
    counterparty_name = models.CharField(max_length=100, blank=True)
    related_sale      = models.ForeignKey(Sale,     on_delete=models.SET_NULL, null=True, blank=True)
    related_purchase  = models.ForeignKey(Purchase, on_delete=models.SET_NULL, null=True, blank=True)
    status            = models.CharField(max_length=12, choices=STATUS_CHOICES, default='confirmed')
    entry             = models.OneToOneField(Entry, on_delete=models.PROTECT, related_name='payment')
    created_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-date', '-created_at')

    def __str__(self):
        return f"Payment #{self.id} — {self.direction} {self.amount}"
