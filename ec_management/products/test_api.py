import pytest
from django.urls import reverse
from rest_framework import status
from products.models import DirectMaterial, DirectLabor, CostSheet, Product
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
