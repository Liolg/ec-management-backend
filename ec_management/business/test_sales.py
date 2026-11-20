import pytest
from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from business.models import Sale
from products.models import StockMovement
from conftest import ProductFactory, CostSheetFactory

SALES_URL = reverse('sale-list')


@pytest.mark.django_db
class TestCreateSale:

    def test_cash_sale_returns_201(self, api_client, business_config):
        product = ProductFactory()
        response = api_client.post(SALES_URL, {
            'product': product.id, 'qty': 2, 'unit_price': '100.00',
            'date': '2026-05-01', 'payment_method': 'cash',
        }, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_cash_sale_debits_cash_account(self, api_client, business_config):
        product = ProductFactory()
        api_client.post(SALES_URL, {
            'product': product.id, 'qty': 1, 'unit_price': '200.00',
            'date': '2026-05-01', 'payment_method': 'cash',
        }, format='json')
        sale = Sale.objects.first()
        debit_line = sale.entry.lines.get(type='D')
        assert debit_line.account == business_config.cash_account
        assert debit_line.value == Decimal('200.00')

    def test_credit_sale_debits_receivable_account(self, api_client, business_config):
        product = ProductFactory()
        api_client.post(SALES_URL, {
            'product': product.id, 'qty': 1, 'unit_price': '150.00',
            'date': '2026-05-01', 'payment_method': 'credit',
        }, format='json')
        sale = Sale.objects.first()
        debit_line = sale.entry.lines.get(type='D')
        assert debit_line.account == business_config.receivable_account

    def test_sale_credits_revenue_account(self, api_client, business_config):
        product = ProductFactory()
        api_client.post(SALES_URL, {
            'product': product.id, 'qty': 1, 'unit_price': '100.00',
            'date': '2026-05-01',
        }, format='json')
        sale = Sale.objects.first()
        credit_line = sale.entry.lines.get(type='C')
        assert credit_line.account == business_config.revenue_account

    def test_total_amount_is_qty_times_unit_price(self, api_client, business_config):
        product = ProductFactory()
        api_client.post(SALES_URL, {
            'product': product.id, 'qty': 3, 'unit_price': '50.00',
            'date': '2026-05-01',
        }, format='json')
        sale = Sale.objects.first()
        assert sale.total_amount == Decimal('150.00')

    def test_defaults_to_product_selling_price(self, api_client, business_config):
        cost_sheet = CostSheetFactory(selling_price=500)
        product    = ProductFactory(cost_sheet=cost_sheet)
        api_client.post(SALES_URL, {
            'product': product.id, 'qty': 2, 'date': '2026-05-01',
        }, format='json')
        sale = Sale.objects.first()
        assert sale.unit_price == Decimal('500')
        assert sale.total_amount == Decimal('1000')

    def test_creates_stock_out_movement(self, api_client, business_config):
        product = ProductFactory()
        api_client.post(SALES_URL, {
            'product': product.id, 'qty': 4, 'unit_price': '10.00',
            'date': '2026-05-01',
        }, format='json')
        movement = StockMovement.objects.get(product=product)
        assert movement.direction == StockMovement.DIRECTION_OUT
        assert movement.qty == 4

    def test_sale_reduces_current_stock(self, api_client, business_config):
        product = ProductFactory()
        from conftest import StockMovementFactory
        StockMovementFactory(product=product, qty=10, direction='IN')
        api_client.post(SALES_URL, {
            'product': product.id, 'qty': 3, 'unit_price': '10.00',
            'date': '2026-05-01',
        }, format='json')
        assert product.current_stock == 7

    def test_fails_without_business_config(self, api_client):
        product = ProductFactory()
        response = api_client.post(SALES_URL, {
            'product': product.id, 'qty': 1, 'unit_price': '100.00',
            'date': '2026-05-01',
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_fails_when_no_selling_price_and_no_unit_price(self, api_client, business_config):
        cost_sheet = CostSheetFactory(selling_price=None)
        product    = ProductFactory(cost_sheet=cost_sheet)
        response   = api_client.post(SALES_URL, {
            'product': product.id, 'qty': 1, 'date': '2026-05-01',
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_response_contains_product_name(self, api_client, business_config):
        product = ProductFactory(name='Widget')
        response = api_client.post(SALES_URL, {
            'product': product.id, 'qty': 1, 'unit_price': '10.00',
            'date': '2026-05-01',
        }, format='json')
        assert response.data['product_name'] == 'Widget'


@pytest.mark.django_db
class TestVoidSale:

    def test_void_sets_status_voided(self, api_client, business_config):
        product = ProductFactory()
        create_resp = api_client.post(SALES_URL, {
            'product': product.id, 'qty': 2, 'unit_price': '100.00',
            'date': '2026-05-01',
        }, format='json')
        sale_id  = create_resp.data['id']
        response = api_client.post(reverse('sale-void', kwargs={'pk': sale_id}))
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'voided'

    def test_void_marks_entry_voided(self, api_client, business_config):
        product = ProductFactory()
        create_resp = api_client.post(SALES_URL, {
            'product': product.id, 'qty': 1, 'unit_price': '50.00',
            'date': '2026-05-01',
        }, format='json')
        sale_id = create_resp.data['id']
        api_client.post(reverse('sale-void', kwargs={'pk': sale_id}))
        sale = Sale.objects.get(pk=sale_id)
        assert sale.entry.voided is True

    def test_void_creates_reverse_stock_in_movement(self, api_client, business_config):
        product = ProductFactory()
        create_resp = api_client.post(SALES_URL, {
            'product': product.id, 'qty': 5, 'unit_price': '10.00',
            'date': '2026-05-01',
        }, format='json')
        sale_id = create_resp.data['id']
        api_client.post(reverse('sale-void', kwargs={'pk': sale_id}))
        in_movements = StockMovement.objects.filter(product=product, direction='IN')
        assert in_movements.exists()
        assert in_movements.first().qty == 5

    def test_void_twice_returns_400(self, api_client, business_config):
        product = ProductFactory()
        create_resp = api_client.post(SALES_URL, {
            'product': product.id, 'qty': 1, 'unit_price': '10.00',
            'date': '2026-05-01',
        }, format='json')
        sale_id = create_resp.data['id']
        void_url = reverse('sale-void', kwargs={'pk': sale_id})
        api_client.post(void_url)
        response = api_client.post(void_url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_stale_parallel_style_void_claim_creates_one_reversal(self, business_config):
        from rest_framework.exceptions import ValidationError
        from business.models import Sale
        from business.services import create_sale, void_sale

        product = ProductFactory()
        sale = create_sale({
            'product': product, 'qty': 1, 'unit_price': Decimal('10.00'),
            'date': '2026-05-01',
        })
        stale_copy = Sale.objects.get(pk=sale.pk)

        void_sale(sale)
        with pytest.raises(ValidationError):
            void_sale(stale_copy)

        assert StockMovement.objects.filter(
            product=product, reference=f'VOID-SALE-{sale.pk}',
        ).count() == 1


@pytest.mark.django_db
class TestListSales:

    def test_list_returns_all_sales(self, api_client, business_config):
        product = ProductFactory()
        for _ in range(3):
            api_client.post(SALES_URL, {
                'product': product.id, 'qty': 1, 'unit_price': '10.00',
                'date': '2026-05-01',
            }, format='json')
        response = api_client.get(SALES_URL)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3
