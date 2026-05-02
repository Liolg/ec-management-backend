import pytest
from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from business.models import Purchase
from products.models import StockMovement
from conftest import ProductFactory

PURCHASES_URL = reverse('purchase-list')


@pytest.mark.django_db
class TestCreatePurchase:

    def test_cash_purchase_returns_201(self, api_client, business_config):
        product = ProductFactory()
        response = api_client.post(PURCHASES_URL, {
            'product': product.id, 'qty': 5, 'unit_cost': '80.00',
            'date': '2026-05-01', 'payment_method': 'cash',
        }, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_cash_purchase_credits_cash_account(self, api_client, business_config):
        product = ProductFactory()
        api_client.post(PURCHASES_URL, {
            'product': product.id, 'qty': 1, 'unit_cost': '200.00',
            'date': '2026-05-01', 'payment_method': 'cash',
        }, format='json')
        purchase    = Purchase.objects.first()
        credit_line = purchase.entry.lines.get(type='C')
        assert credit_line.account == business_config.cash_account

    def test_credit_purchase_credits_payable_account(self, api_client, business_config):
        product = ProductFactory()
        api_client.post(PURCHASES_URL, {
            'product': product.id, 'qty': 1, 'unit_cost': '200.00',
            'date': '2026-05-01', 'payment_method': 'credit',
        }, format='json')
        purchase    = Purchase.objects.first()
        credit_line = purchase.entry.lines.get(type='C')
        assert credit_line.account == business_config.payable_account

    def test_purchase_debits_inventory_account(self, api_client, business_config):
        product = ProductFactory()
        api_client.post(PURCHASES_URL, {
            'product': product.id, 'qty': 1, 'unit_cost': '100.00',
            'date': '2026-05-01',
        }, format='json')
        purchase   = Purchase.objects.first()
        debit_line = purchase.entry.lines.get(type='D')
        assert debit_line.account == business_config.inventory_account

    def test_total_amount_is_qty_times_unit_cost(self, api_client, business_config):
        product = ProductFactory()
        api_client.post(PURCHASES_URL, {
            'product': product.id, 'qty': 4, 'unit_cost': '25.00',
            'date': '2026-05-01',
        }, format='json')
        assert Purchase.objects.first().total_amount == Decimal('100.00')

    def test_creates_stock_in_movement(self, api_client, business_config):
        product = ProductFactory()
        api_client.post(PURCHASES_URL, {
            'product': product.id, 'qty': 10, 'unit_cost': '5.00',
            'date': '2026-05-01',
        }, format='json')
        movement = StockMovement.objects.get(product=product)
        assert movement.direction == StockMovement.DIRECTION_IN
        assert movement.qty == 10

    def test_purchase_increases_current_stock(self, api_client, business_config):
        product = ProductFactory()
        api_client.post(PURCHASES_URL, {
            'product': product.id, 'qty': 6, 'unit_cost': '10.00',
            'date': '2026-05-01',
        }, format='json')
        assert product.current_stock == 6

    def test_fails_without_business_config(self, api_client):
        product = ProductFactory()
        response = api_client.post(PURCHASES_URL, {
            'product': product.id, 'qty': 1, 'unit_cost': '10.00',
            'date': '2026-05-01',
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestVoidPurchase:

    def test_void_sets_status_voided(self, api_client, business_config):
        product     = ProductFactory()
        create_resp = api_client.post(PURCHASES_URL, {
            'product': product.id, 'qty': 2, 'unit_cost': '50.00',
            'date': '2026-05-01',
        }, format='json')
        purchase_id = create_resp.data['id']
        response    = api_client.post(reverse('purchase-void', kwargs={'pk': purchase_id}))
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'voided'

    def test_void_marks_entry_voided(self, api_client, business_config):
        product     = ProductFactory()
        create_resp = api_client.post(PURCHASES_URL, {
            'product': product.id, 'qty': 1, 'unit_cost': '30.00',
            'date': '2026-05-01',
        }, format='json')
        purchase_id = create_resp.data['id']
        api_client.post(reverse('purchase-void', kwargs={'pk': purchase_id}))
        purchase = Purchase.objects.get(pk=purchase_id)
        assert purchase.entry.voided is True

    def test_void_creates_reverse_stock_out_movement(self, api_client, business_config):
        product     = ProductFactory()
        create_resp = api_client.post(PURCHASES_URL, {
            'product': product.id, 'qty': 8, 'unit_cost': '10.00',
            'date': '2026-05-01',
        }, format='json')
        purchase_id = create_resp.data['id']
        api_client.post(reverse('purchase-void', kwargs={'pk': purchase_id}))
        out_movements = StockMovement.objects.filter(product=product, direction='OUT')
        assert out_movements.exists()
        assert out_movements.first().qty == 8

    def test_void_twice_returns_400(self, api_client, business_config):
        product     = ProductFactory()
        create_resp = api_client.post(PURCHASES_URL, {
            'product': product.id, 'qty': 1, 'unit_cost': '10.00',
            'date': '2026-05-01',
        }, format='json')
        purchase_id = create_resp.data['id']
        void_url    = reverse('purchase-void', kwargs={'pk': purchase_id})
        api_client.post(void_url)
        response = api_client.post(void_url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
