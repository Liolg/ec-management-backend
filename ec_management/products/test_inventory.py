import pytest
from django.urls import reverse
from rest_framework import status
from products.models import StockMovement
from conftest import ProductFactory, StockMovementFactory


@pytest.mark.django_db
class TestCurrentStock:

    def test_empty_product_has_zero_stock(self):
        product = ProductFactory()
        assert product.current_stock == 0

    def test_stock_increases_after_in_movement(self):
        product = ProductFactory()
        StockMovementFactory(product=product, qty=10, direction='IN')
        assert product.current_stock == 10

    def test_stock_decreases_after_out_movement(self):
        product = ProductFactory()
        StockMovementFactory(product=product, qty=10, direction='IN')
        StockMovementFactory(product=product, qty=3,  direction='OUT')
        assert product.current_stock == 7

    def test_multiple_movements_accumulate(self):
        product = ProductFactory()
        StockMovementFactory(product=product, qty=20, direction='IN')
        StockMovementFactory(product=product, qty=5,  direction='IN')
        StockMovementFactory(product=product, qty=8,  direction='OUT')
        assert product.current_stock == 17

    def test_stock_is_isolated_per_product(self):
        p1 = ProductFactory()
        p2 = ProductFactory()
        StockMovementFactory(product=p1, qty=15, direction='IN')
        StockMovementFactory(product=p2, qty=3,  direction='IN')
        assert p1.current_stock == 15
        assert p2.current_stock == 3


@pytest.mark.django_db
class TestStockEndpoint:

    def test_returns_current_stock(self, api_client):
        product = ProductFactory()
        StockMovementFactory(product=product, qty=10, direction='IN')
        StockMovementFactory(product=product, qty=4,  direction='OUT')
        url = reverse('product-stock', kwargs={'pk': product.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['current_stock'] == 6

    def test_returns_movements_list(self, api_client):
        product = ProductFactory()
        StockMovementFactory(product=product, qty=10, direction='IN')
        StockMovementFactory(product=product, qty=4,  direction='OUT')
        url = reverse('product-stock', kwargs={'pk': product.pk})
        response = api_client.get(url)
        assert len(response.data['movements']) == 2

    def test_returns_zero_when_no_movements(self, api_client):
        product = ProductFactory()
        url = reverse('product-stock', kwargs={'pk': product.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['current_stock'] == 0
        assert response.data['movements'] == []

    def test_movement_fields_are_present(self, api_client):
        product = ProductFactory()
        StockMovementFactory(product=product, qty=5, direction='IN', unit_cost='50.00')
        url = reverse('product-stock', kwargs={'pk': product.pk})
        response = api_client.get(url)
        movement = response.data['movements'][0]
        assert 'qty' in movement
        assert 'direction' in movement
        assert 'unit_cost' in movement
        assert 'date' in movement


@pytest.mark.django_db
class TestStockAdjustmentAPI:

    def test_create_in_adjustment(self, api_client):
        product = ProductFactory()
        url = reverse('stock-adjustment-list')
        data = {
            'product':   product.id,
            'qty':       20,
            'direction': 'IN',
            'date':      '2026-05-01',
            'reference': 'MANUAL-ADJ',
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert StockMovement.objects.filter(product=product, direction='IN').exists()

    def test_create_out_adjustment(self, api_client):
        product = ProductFactory()
        url = reverse('stock-adjustment-list')
        data = {
            'product':   product.id,
            'qty':       5,
            'direction': 'OUT',
            'date':      '2026-05-01',
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_invalid_direction_returns_400(self, api_client):
        product = ProductFactory()
        url = reverse('stock-adjustment-list')
        data = {
            'product':   product.id,
            'qty':       5,
            'direction': 'WRONG',
            'date':      '2026-05-01',
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_adjustments(self, api_client):
        StockMovementFactory.create_batch(3)
        url = reverse('stock-adjustment-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3

    def test_adjustment_affects_current_stock(self, api_client):
        product = ProductFactory()
        url = reverse('stock-adjustment-list')
        api_client.post(url, {'product': product.id, 'qty': 10, 'direction': 'IN',  'date': '2026-05-01'}, format='json')
        api_client.post(url, {'product': product.id, 'qty': 3,  'direction': 'OUT', 'date': '2026-05-01'}, format='json')
        product.refresh_from_db()
        assert product.current_stock == 7
