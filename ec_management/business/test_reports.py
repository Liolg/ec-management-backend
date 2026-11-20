import pytest
from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from business.services import create_sale, create_expense, create_purchase, void_sale
from conftest import ProductFactory

SUMMARY_URL     = reverse('report-summary')
PROFIT_LOSS_URL = reverse('report-profit-loss')
INVENTORY_URL   = reverse('report-inventory')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sale(business_config, product, amount, date='2026-05-01', payment_method='cash'):
    return create_sale({
        'product': product, 'qty': 1,
        'unit_price': Decimal(str(amount)),
        'date': date, 'payment_method': payment_method,
    })

def expense(business_config, amount, date='2026-05-01', payment_method='cash'):
    return create_expense({
        'description': 'Test expense', 'category': 'other',
        'amount': Decimal(str(amount)),
        'date': date, 'payment_method': payment_method,
    })

def purchase(business_config, product, qty, unit_cost, date='2026-05-01'):
    return create_purchase({
        'product': product, 'qty': qty,
        'unit_cost': Decimal(str(unit_cost)),
        'date': date,
    })


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestSummaryReport:

    def test_returns_200(self, api_client, business_config):
        response = api_client.get(SUMMARY_URL)
        assert response.status_code == status.HTTP_200_OK

    def test_all_zeros_with_no_data(self, api_client, business_config):
        response = api_client.get(SUMMARY_URL)
        assert response.data['revenue'] == '0.00'
        assert Decimal(str(response.data['revenue']))    == Decimal('0.00')
        assert Decimal(str(response.data['expenses']))   == Decimal('0.00')
        assert Decimal(str(response.data['net_profit'])) == Decimal('0.00')
        assert Decimal(str(response.data['cash_balance'])) == Decimal('0.00')

    def test_revenue_from_sales(self, api_client, business_config):
        p = ProductFactory()
        sale(business_config, p, 300)
        sale(business_config, p, 200)
        response = api_client.get(SUMMARY_URL)
        assert Decimal(str(response.data['revenue'])) == Decimal('500.00')

    def test_expenses_from_expenses(self, api_client, business_config):
        expense(business_config, 400)
        expense(business_config, 100)
        response = api_client.get(SUMMARY_URL)
        assert Decimal(str(response.data['expenses'])) == Decimal('500.00')

    def test_net_profit_is_revenue_minus_expenses(self, api_client, business_config):
        p = ProductFactory()
        sale(business_config, p, 1000)
        expense(business_config, 300)
        response = api_client.get(SUMMARY_URL)
        assert Decimal(str(response.data['net_profit'])) == Decimal('700.00')

    def test_period_filter_excludes_entries_outside_range(self, api_client, business_config):
        p = ProductFactory()
        sale(business_config, p, 500, date='2026-01-15')   # outside
        sale(business_config, p, 300, date='2026-03-10')   # inside
        response = api_client.get(SUMMARY_URL, {'start': '2026-03-01', 'end': '2026-03-31'})
        assert Decimal(str(response.data['revenue'])) == Decimal('300.00')

    def test_period_filter_includes_boundary_dates(self, api_client, business_config):
        p = ProductFactory()
        sale(business_config, p, 100, date='2026-03-01')
        sale(business_config, p, 200, date='2026-03-31')
        response = api_client.get(SUMMARY_URL, {'start': '2026-03-01', 'end': '2026-03-31'})
        assert Decimal(str(response.data['revenue'])) == Decimal('300.00')

    def test_voided_entries_excluded(self, api_client, business_config):
        p = ProductFactory()
        s = sale(business_config, p, 400)
        void_sale(s)
        response = api_client.get(SUMMARY_URL)
        assert Decimal(str(response.data['revenue'])) == Decimal('0.00')

    def test_cash_balance_increases_with_cash_sales(self, api_client, business_config):
        p = ProductFactory()
        sale(business_config, p, 250, payment_method='cash')
        expense(business_config, 100, payment_method='cash')
        response = api_client.get(SUMMARY_URL)
        assert Decimal(str(response.data['cash_balance'])) == Decimal('150.00')

    def test_receivables_from_credit_sales(self, api_client, business_config):
        p = ProductFactory()
        sale(business_config, p, 600, payment_method='credit')
        response = api_client.get(SUMMARY_URL)
        assert Decimal(str(response.data['receivables'])) == Decimal('600.00')

    def test_payables_from_credit_expenses(self, api_client, business_config):
        expense(business_config, 150, payment_method='credit')
        response = api_client.get(SUMMARY_URL)
        assert Decimal(str(response.data['payables'])) == Decimal('150.00')

    def test_period_key_returned(self, api_client, business_config):
        response = api_client.get(SUMMARY_URL, {'start': '2026-01-01', 'end': '2026-12-31'})
        assert response.data['period']['start'] == '2026-01-01'
        assert response.data['period']['end']   == '2026-12-31'

    def test_start_after_end_returns_400(self, api_client, business_config):
        response = api_client.get(SUMMARY_URL, {'start': '2026-05-31', 'end': '2026-05-01'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_date_format_returns_400(self, api_client, business_config):
        response = api_client.get(SUMMARY_URL, {'start': 'not-a-date'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# Profit & Loss
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestProfitLossReport:

    def test_returns_200(self, api_client, business_config):
        assert api_client.get(PROFIT_LOSS_URL).status_code == status.HTTP_200_OK

    def test_empty_with_no_data(self, api_client, business_config):
        response = api_client.get(PROFIT_LOSS_URL)
        assert response.data['revenue']  == []
        assert response.data['expenses'] == []
        assert response.data['total_revenue']  == '0.00'
        assert response.data['total_expenses'] == '0.00'
        assert response.data['net_profit']     == '0.00'

    def test_revenue_row_per_account(self, api_client, business_config):
        p = ProductFactory()
        sale(business_config, p, 300)
        response = api_client.get(PROFIT_LOSS_URL)
        assert len(response.data['revenue']) == 1
        assert response.data['revenue'][0]['account'] == 'Sales Revenue'
        assert Decimal(str(response.data['revenue'][0]['amount'])) == Decimal('300.00')

    def test_expense_row_per_account(self, api_client, business_config):
        expense(business_config, 200)
        response = api_client.get(PROFIT_LOSS_URL)
        assert len(response.data['expenses']) == 1
        assert response.data['expenses'][0]['account'] == 'Operating Expenses'
        assert Decimal(str(response.data['expenses'][0]['amount'])) == Decimal('200.00')

    def test_multiple_sales_aggregated_per_account(self, api_client, business_config):
        p = ProductFactory()
        sale(business_config, p, 100)
        sale(business_config, p, 200)
        response = api_client.get(PROFIT_LOSS_URL)
        assert len(response.data['revenue']) == 1
        assert Decimal(str(response.data['revenue'][0]['amount'])) == Decimal('300.00')

    def test_total_revenue_and_expenses(self, api_client, business_config):
        p = ProductFactory()
        sale(business_config, p, 1000)
        expense(business_config, 400)
        response = api_client.get(PROFIT_LOSS_URL)
        assert Decimal(str(response.data['total_revenue']))  == Decimal('1000.00')
        assert Decimal(str(response.data['total_expenses'])) == Decimal('400.00')

    def test_net_profit(self, api_client, business_config):
        p = ProductFactory()
        sale(business_config, p, 1000)
        expense(business_config, 350)
        response = api_client.get(PROFIT_LOSS_URL)
        assert Decimal(str(response.data['net_profit'])) == Decimal('650.00')

    def test_period_filter_applied(self, api_client, business_config):
        p = ProductFactory()
        sale(business_config, p, 200, date='2026-01-10')   # outside
        sale(business_config, p, 500, date='2026-05-01')   # inside
        response = api_client.get(PROFIT_LOSS_URL, {'start': '2026-05-01', 'end': '2026-05-31'})
        assert Decimal(str(response.data['total_revenue'])) == Decimal('500.00')

    def test_start_after_end_returns_400(self, api_client, business_config):
        response = api_client.get(PROFIT_LOSS_URL, {'start': '2026-06-01', 'end': '2026-05-01'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestInventoryReport:

    def test_returns_200(self, api_client, business_config):
        assert api_client.get(INVENTORY_URL).status_code == status.HTTP_200_OK

    def test_empty_with_no_products(self, api_client, business_config):
        assert api_client.get(INVENTORY_URL).data == []

    def test_returns_one_row_per_product(self, api_client, business_config):
        ProductFactory.create_batch(3)
        response = api_client.get(INVENTORY_URL)
        assert len(response.data) == 3

    def test_current_stock_reflects_purchases(self, api_client, business_config):
        p = ProductFactory()
        purchase(business_config, p, qty=10, unit_cost=50)
        response = api_client.get(INVENTORY_URL)
        item = next(r for r in response.data if r['product'] == p.name)
        assert item['current_stock'] == 10

    def test_current_stock_after_sale_decreases(self, api_client, business_config):
        p = ProductFactory()
        purchase(business_config, p, qty=10, unit_cost=50)
        sale(business_config, p, 50)
        response = api_client.get(INVENTORY_URL)
        item = next(r for r in response.data if r['product'] == p.name)
        assert item['current_stock'] == 9

    def test_unit_cost_is_average_of_in_movements(self, api_client, business_config):
        p = ProductFactory()
        purchase(business_config, p, qty=5, unit_cost=100)
        purchase(business_config, p, qty=5, unit_cost=200)
        response = api_client.get(INVENTORY_URL)
        item = next(r for r in response.data if r['product'] == p.name)
        assert Decimal(str(item['unit_cost'])) == Decimal('150.00')

    def test_stock_value_is_stock_times_unit_cost(self, api_client, business_config):
        p = ProductFactory()
        purchase(business_config, p, qty=4, unit_cost=250)
        response = api_client.get(INVENTORY_URL)
        item = next(r for r in response.data if r['product'] == p.name)
        assert Decimal(str(item['stock_value'])) == Decimal('1000.00')

    def test_product_with_no_movements_shows_zeros(self, api_client, business_config):
        p = ProductFactory()
        response = api_client.get(INVENTORY_URL)
        item = next(r for r in response.data if r['product'] == p.name)
        assert item['current_stock'] == 0
        assert item['unit_cost'] == '0.00'
        assert item['stock_value'] == '0.00'
        assert Decimal(str(item['unit_cost']))   == Decimal('0.00')
        assert Decimal(str(item['stock_value'])) == Decimal('0.00')
