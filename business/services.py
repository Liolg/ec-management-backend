from decimal import Decimal
from django.db import transaction
from rest_framework.exceptions import ValidationError

from ec_accounts.models import Account
from ec_accounts.services import create_entry
from products.models import StockMovement
from .models import BusinessConfig, Sale, Purchase, Expense, Payment

STANDARD_ACCOUNTS = [
    {'code': '1000', 'name': 'Cash / Bank',         'type': Account.ASSET},
    {'code': '1100', 'name': 'Accounts Receivable', 'type': Account.ASSET},
    {'code': '1200', 'name': 'Inventory',            'type': Account.ASSET},
    {'code': '2000', 'name': 'Accounts Payable',     'type': Account.LIABILITY},
    {'code': '3000', 'name': "Owner's Equity",       'type': Account.EQUITY},
    {'code': '4000', 'name': 'Sales Revenue',        'type': Account.INCOME},
    {'code': '5000', 'name': 'Cost of Goods Sold',   'type': Account.EXPENSE},
    {'code': '6000', 'name': 'Operating Expenses',   'type': Account.EXPENSE},
]


@transaction.atomic
def setup_business(company_name, currency='USD'):
    accounts = {}
    for acc_data in STANDARD_ACCOUNTS:
        account, _ = Account.objects.get_or_create(
            code=acc_data['code'],
            defaults={'name': acc_data['name'], 'type': acc_data['type']},
        )
        accounts[acc_data['code']] = account

    config = BusinessConfig(
        pk=1,
        company_name=company_name,
        currency=currency,
        cash_account=accounts['1000'],
        receivable_account=accounts['1100'],
        payable_account=accounts['2000'],
        revenue_account=accounts['4000'],
        inventory_account=accounts['1200'],
        expense_account=accounts['6000'],
    )
    config.save()
    return config


def _get_config():
    config = BusinessConfig.get()
    if config is None:
        raise ValidationError('Business is not configured. Call POST /api/v1/business/setup/ first.')
    return config


def _make_entry(debit_account, credit_account, amount, date, description, reference=None):
    return create_entry({
        'date':        date,
        'description': description,
        'reference':   reference,
        'lines': [
            {'account': debit_account,  'value': amount, 'type': 'D'},
            {'account': credit_account, 'value': amount, 'type': 'C'},
        ],
    })


# ---------------------------------------------------------------------------
# Sales
# ---------------------------------------------------------------------------

@transaction.atomic
def create_sale(data):
    product        = data['product']
    qty            = data['qty']
    unit_price     = data.get('unit_price')
    date           = data['date']
    customer_name  = data.get('customer_name', '')
    payment_method = data.get('payment_method', 'cash')

    if unit_price is None:
        selling_price = product.cost_sheet.selling_price
        if selling_price is None:
            raise ValidationError(
                'Product has no selling price. Provide unit_price or complete the cost sheet.'
            )
        unit_price = Decimal(str(selling_price))

    total_amount   = qty * unit_price
    config         = _get_config()
    debit_account  = config.cash_account if payment_method == 'cash' else config.receivable_account
    credit_account = config.revenue_account

    entry = _make_entry(
        debit_account, credit_account, total_amount, date,
        description=f"Sale: {product.name} x {qty}",
    )

    sale = Sale.objects.create(
        product=product, qty=qty, unit_price=unit_price,
        total_amount=total_amount, date=date,
        customer_name=customer_name, payment_method=payment_method,
        entry=entry,
    )

    StockMovement.objects.create(
        product=product, qty=qty, direction=StockMovement.DIRECTION_OUT,
        unit_cost=unit_price, date=date, reference=f'SALE-{sale.id}',
    )

    return sale


@transaction.atomic
def void_sale(sale):
    if sale.status == 'voided':
        raise ValidationError('Sale is already voided.')
    sale.entry.voided = True
    sale.entry.save()
    StockMovement.objects.create(
        product=sale.product, qty=sale.qty, direction=StockMovement.DIRECTION_IN,
        date=sale.date, reference=f'VOID-SALE-{sale.id}',
    )
    sale.status = 'voided'
    sale.save()
    return sale


# ---------------------------------------------------------------------------
# Purchases
# ---------------------------------------------------------------------------

@transaction.atomic
def create_purchase(data):
    product        = data['product']
    qty            = data['qty']
    unit_cost      = data['unit_cost']
    date           = data['date']
    supplier_name  = data.get('supplier_name', '')
    payment_method = data.get('payment_method', 'cash')

    total_amount   = qty * unit_cost
    config         = _get_config()
    debit_account  = config.inventory_account
    credit_account = config.cash_account if payment_method == 'cash' else config.payable_account

    entry = _make_entry(
        debit_account, credit_account, total_amount, date,
        description=f"Purchase: {product.name} x {qty}",
    )

    purchase = Purchase.objects.create(
        product=product, qty=qty, unit_cost=unit_cost,
        total_amount=total_amount, date=date,
        supplier_name=supplier_name, payment_method=payment_method,
        entry=entry,
    )

    StockMovement.objects.create(
        product=product, qty=qty, direction=StockMovement.DIRECTION_IN,
        unit_cost=unit_cost, date=date, reference=f'PUR-{purchase.id}',
    )

    return purchase


@transaction.atomic
def void_purchase(purchase):
    if purchase.status == 'voided':
        raise ValidationError('Purchase is already voided.')
    purchase.entry.voided = True
    purchase.entry.save()
    StockMovement.objects.create(
        product=purchase.product, qty=purchase.qty, direction=StockMovement.DIRECTION_OUT,
        date=purchase.date, reference=f'VOID-PUR-{purchase.id}',
    )
    purchase.status = 'voided'
    purchase.save()
    return purchase


# ---------------------------------------------------------------------------
# Expenses
# ---------------------------------------------------------------------------

@transaction.atomic
def create_expense(data):
    description    = data['description']
    category       = data.get('category', 'other')
    amount         = data['amount']
    date           = data['date']
    payment_method = data.get('payment_method', 'cash')

    config         = _get_config()
    debit_account  = config.expense_account
    credit_account = config.cash_account if payment_method == 'cash' else config.payable_account

    entry = _make_entry(
        debit_account, credit_account, amount, date,
        description=f"{category.title()}: {description}",
    )

    return Expense.objects.create(
        description=description, category=category, amount=amount,
        date=date, payment_method=payment_method, entry=entry,
    )


@transaction.atomic
def void_expense(expense):
    if expense.status == 'voided':
        raise ValidationError('Expense is already voided.')
    expense.entry.voided = True
    expense.entry.save()
    expense.status = 'voided'
    expense.save()
    return expense


# ---------------------------------------------------------------------------
# Payments
# ---------------------------------------------------------------------------

@transaction.atomic
def create_payment(data):
    direction         = data['direction']
    amount            = data['amount']
    date              = data['date']
    counterparty_name = data.get('counterparty_name', '')
    related_sale      = data.get('related_sale')
    related_purchase  = data.get('related_purchase')

    config = _get_config()

    if direction == Payment.DIRECTION_RECEIVED:
        debit_account  = config.cash_account
        credit_account = config.receivable_account
        description    = f"Payment received from {counterparty_name or 'customer'}"
    else:
        debit_account  = config.payable_account
        credit_account = config.cash_account
        description    = f"Payment made to {counterparty_name or 'supplier'}"

    entry = _make_entry(debit_account, credit_account, amount, date, description=description)

    return Payment.objects.create(
        direction=direction, amount=amount, date=date,
        counterparty_name=counterparty_name,
        related_sale=related_sale, related_purchase=related_purchase,
        entry=entry,
    )


@transaction.atomic
def void_payment(payment):
    if payment.status == 'voided':
        raise ValidationError('Payment is already voided.')
    payment.entry.voided = True
    payment.entry.save()
    payment.status = 'voided'
    payment.save()
    return payment
