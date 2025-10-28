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
        return f"{self.code} - {self.name}"


class Entry(models.Model):
    date = models.DateField()
    description = models.TextField(blank=True)
    reference = models.CharField(max_length=128, blank=True, null=True)
    voided = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-date', '-created_at')

    def __str__(self):
        return f"Entry {self.id} — {self.date} — {self.reference or 'no-ref'}"

    @property
    def total_debit(self):
        s = self.lines.aggregate(total=models.Sum('debit'))['total']
        return s or Decimal('0.00')

    @property
    def total_credit(self):
        s = self.lines.aggregate(total=models.Sum('credit'))['total']
        return s or Decimal('0.00')

    def is_balanced(self):
        return self.total_debit == self.total_credit

    def clean(self):
        if self.pk:  # si ya existe y tiene líneas
            if not self.is_balanced():
                raise ValidationError('Asiento desbalanceado: debe == haber')


class Line(models.Model):
    entry = models.ForeignKey(Entry, related_name='lines', on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.PROTECT)
    description = models.CharField(max_length=200, blank=True)
    debit = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal('0.00'))
    credit = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(debit__gte=0), name='debit_non_negative'),
            models.CheckConstraint(check=models.Q(credit__gte=0), name='credit_non_negative'),
        ]

    def clean(self):
        if self.debit > Decimal('0.00') and self.credit > Decimal('0.00'):
            raise ValidationError('Una línea no puede tener debit y credit simultáneamente')
    def __str__(self):
        return f"{'debit' if self.debit > 0 else 'credit'} — {self.account} — {self.entry}"

