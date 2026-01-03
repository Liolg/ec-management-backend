from django.test import TestCase
from decimal import Decimal
from .models import Account, Entry, Line
from .services import create_update_entry

class AccountingBasicTests(TestCase):
    def setUp(self):
        self.a1 = Account.objects.create(code='1000', name='Caja', type=Account.ASSET)
        self.a2 = Account.objects.create(code='4000', name='Ventas', type=Account.INCOME)

    def test_create_balanced_entry(self):
        entry = create_update_entry(
            date='2025-01-01',
            lines=[
                {'account': self.a1, 'debit': Decimal('100.00'), 'credit': Decimal('0.00')},
                {'account': self.a2, 'debit': Decimal('0.00'), 'credit': Decimal('100.00')},
            ],
            description='Venta en efectivo'
        )
        self.assertTrue(entry.is_balanced())
        self.assertEqual(entry.lines.count(), 2)

    def test_unbalanced_raises(self):
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            create_update_entry(
                date='2025-01-01',
                lines=[
                    {'account': self.a1, 'debit': Decimal('90.00'), 'credit': Decimal('0.00')},
                    {'account': self.a2, 'debit': Decimal('0.00'), 'credit': Decimal('100.00')},
                ]
            )
