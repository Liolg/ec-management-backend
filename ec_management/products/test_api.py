import pytest
from django.urls import reverse
from rest_framework import status
from products.models import DirectMaterial, DirectLabor, CostSheet, Product, StockMovement
from conftest import DirectMaterialFactory, DirectLaborFactory, CostSheetFactory, ProductFactory

@pytest.mark.django_db
class TestDirectMaterialAPI:
    def test_list_direct_materials(self, api_client):
        DirectMaterialFactory.create_batch(3)
        url = reverse('directmaterial-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3

    def test_create_direct_material(self, api_client):
        url = reverse('directmaterial-list')
        data = {
            'name': 'Steel Rod',
            'unit': 'kg',
            'cost_by_unit': 50
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert DirectMaterial.objects.filter(name='Steel Rod').exists()

@pytest.mark.django_db
class TestDirectLaborAPI:
    def test_list_direct_labors(self, api_client):
        DirectLaborFactory.create_batch(3)
        url = reverse('directlabor-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3

    def test_create_direct_labor(self, api_client):
        url = reverse('directlabor-list')
        data = {
            'name': 'Welder',
            'time_unit': 'hour',
            'cost_by_unit': 75.50
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert DirectLabor.objects.filter(name='Welder').exists()

@pytest.mark.django_db
class TestCostSheetAPI:
    def test_list_cost_sheets(self, api_client):
        CostSheetFactory.create_batch(3)
        url = reverse('costsheet-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3

    def test_create_cost_sheet(self, api_client):
        url = reverse('costsheet-list')
        data = {
            'name': 'Basic Cost Sheet',
            'manufacturing_overhead': 500,
            'total_manufacturing_cost': 1500,
            'non_manufacturing_cost': 200,
            'total_cost': 1700,
            'profit_margin': 20,
            'selling_price': 2125,
            'unit': 'pcs'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert CostSheet.objects.filter(name='Basic Cost Sheet').exists()

    def test_nested_lines_are_calculated_on_create(self, api_client):
        material = DirectMaterialFactory(cost_by_unit=10)
        labor = DirectLaborFactory(cost_by_unit=5)

        response = api_client.post(reverse('costsheet-list'), {
            'name': 'Nested',
            'material_lines': [{'material': material.pk, 'qty': 3}],
            'labor_lines': [{'labor': labor.pk, 'qty': 2}],
        }, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['material_lines'][0]['total_cost'] == 30
        assert response.data['labor_lines'][0]['total_cost'] == 10
        assert response.data['total_cost'] == 40

    def test_patch_omitted_lines_preserves_and_empty_lines_clear(self, api_client):
        material = DirectMaterialFactory(cost_by_unit=10)
        create = api_client.post(reverse('costsheet-list'), {
            'name': 'Nested',
            'material_lines': [{'material': material.pk, 'qty': 3}],
        }, format='json')
        url = reverse('costsheet-detail', kwargs={'pk': create.data['id']})

        preserved = api_client.patch(url, {'unit': 'kg'}, format='json')
        cleared = api_client.patch(url, {'material_lines': []}, format='json')

        assert len(preserved.data['material_lines']) == 1
        assert cleared.data['material_lines'] == []
        assert cleared.data['total_cost'] == 0

    def test_referenced_material_delete_returns_conflict(self, api_client):
        material = DirectMaterialFactory()
        create = api_client.post(reverse('costsheet-list'), {
            'name': 'Nested',
            'material_lines': [{'material': material.pk, 'qty': 1}],
        }, format='json')

        response = api_client.delete(
            reverse('directmaterial-detail', kwargs={'pk': material.pk}),
        )

        assert create.status_code == status.HTTP_201_CREATED
        assert response.status_code == status.HTTP_409_CONFLICT

@pytest.mark.django_db
class TestProductAPI:
    def test_list_products(self, api_client):
        ProductFactory.create_batch(3)
        url = reverse('product-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3

    def test_create_product(self, api_client):
        cost_sheet = CostSheetFactory(name='Example Cost Sheet')
        url = reverse('product-list')
        data = {
            'name': 'Example Product',
            'cost_sheet': cost_sheet.id
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Product.objects.filter(name='Example Product').exists()

    def test_product_with_history_delete_returns_conflict(self, api_client):
        product = ProductFactory()
        StockMovement.objects.create(
            product=product, qty=1, direction='IN', date='2026-05-01',
        )

        response = api_client.delete(
            reverse('product-detail', kwargs={'pk': product.pk}),
        )

        assert response.status_code == status.HTTP_409_CONFLICT
