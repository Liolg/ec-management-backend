from decimal import Decimal
from django.db import models, transaction
from django.core.exceptions import ValidationError


class Account(models.Model):
    ASSET = 'asset'
    LIABILITY = 'liability'
    EQUITY = 'equity'
    INCOME = 'income'
    EXPENSE = 'expense'

    TYPE_CHOICES = [
        (ASSET, 'Activo'),
        (LIABILITY, 'Pasivo'),
        (EQUITY, 'Patrimonio'),
        (INCOME, 'Ingreso'),
        (EXPENSE, 'Gasto'),
    ]

    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=16, choices=TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('code',)

    def __str__(self):
        return f"Account - {self.name}"


class Entry(models.Model):
    date = models.DateField()
    description = models.TextField(blank=True)
    reference = models.CharField(max_length=128, blank=True, null=True)
    voided = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-date', '-created_at')

    def __str__(self):
        return f"Entry #{self.id} of {self.date}"

    @property
    def total_debit(self):
        total = self.lines.filter(type="D").aggregate(total=models.Sum('value'))['total']
        return total or Decimal('0.00')

    @property
    def total_credit(self):
        total = self.lines.filter(type="C").aggregate(total=models.Sum('value'))['total']
        return total or Decimal('0.00')

    def is_balanced(self):
        return self.total_debit == self.total_credit

    def clean(self):
        if not self.is_balanced():
            raise ValidationError('Asiento desbalanceado')


class Line(models.Model):
    type_choices = [('D', 'debit'), ('C', 'credit')]
    entry = models.ForeignKey(Entry, related_name='lines', on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.PROTECT)
    description = models.CharField(max_length=200, blank=True)
    value = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal('0.00'))
    type = models.CharField(max_length=18, choices=type_choices, default='D')

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(value__gte=0), name='value_non_negative'),
        ]

    def __str__(self):
        return f"id: {self.id}, {'debit' if self.type == 'D' else 'credit'} {self.value} in {self.account} — {self.entry}"

