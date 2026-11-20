from decimal import Decimal
from django.db.models import Sum, Avg
from ec_accounts.models import Line
from products.models import Product, StockMovement


def decimal_string(value):
    return format(Decimal(value).quantize(Decimal('0.01')), 'f')


def _line_sum(filters):
    result = Line.objects.filter(**filters).aggregate(total=Sum('value'))['total']
    return result or Decimal('0.00')


def _apply_period(filters, start, end):
    if start:
        filters['entry__date__gte'] = start
    if end:
        filters['entry__date__lte'] = end
    return filters


def get_revenue(start=None, end=None):
    filters = {'entry__voided': False, 'account__type': 'income', 'type': 'C'}
    return _line_sum(_apply_period(filters, start, end))


def get_expenses(start=None, end=None):
    filters = {'entry__voided': False, 'account__type': 'expense', 'type': 'D'}
    return _line_sum(_apply_period(filters, start, end))


def get_account_balance(account):
    """Debit balance (assets): total debits minus total credits."""
    if account is None:
        return Decimal('0.00')
    base    = {'entry__voided': False, 'account': account}
    debits  = _line_sum({**base, 'type': 'D'})
    credits = _line_sum({**base, 'type': 'C'})
    return debits - credits


def get_credit_balance(account):
    """Credit balance (liabilities): total credits minus total debits."""
    if account is None:
        return Decimal('0.00')
    base    = {'entry__voided': False, 'account': account}
    debits  = _line_sum({**base, 'type': 'D'})
    credits = _line_sum({**base, 'type': 'C'})
    return credits - debits


def get_revenue_breakdown(start=None, end=None):
    filters = {'entry__voided': False, 'account__type': 'income', 'type': 'C'}
    _apply_period(filters, start, end)
    return (
        Line.objects.filter(**filters)
        .values('account__name')
        .annotate(amount=Sum('value'))
        .order_by('account__name')
    )


def get_expenses_breakdown(start=None, end=None):
    filters = {'entry__voided': False, 'account__type': 'expense', 'type': 'D'}
    _apply_period(filters, start, end)
    return (
        Line.objects.filter(**filters)
        .values('account__name')
        .annotate(amount=Sum('value'))
        .order_by('account__name')
    )


def get_inventory_report():
    products = Product.objects.prefetch_related('stock_movements').all()
    result   = []
    for product in products:
        current_stock = product.current_stock
        avg_unit_cost = (
            product.stock_movements
            .filter(direction=StockMovement.DIRECTION_IN, unit_cost__isnull=False)
            .aggregate(avg=Avg('unit_cost'))['avg'] or Decimal('0.00')
        )
        result.append({
            'product':       product.name,
            'current_stock': current_stock,
            'unit_cost':     decimal_string(avg_unit_cost),
            'stock_value':   decimal_string(current_stock * avg_unit_cost),
        })
    return result
