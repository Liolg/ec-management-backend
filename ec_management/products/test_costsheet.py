import pytest
from django.urls import reverse
from rest_framework import status
from products.models import CostSheet, CostSheetMaterial, CostSheetLabor, DirectMaterial, DirectLabor
from products.services import calculate_cost_sheet


def make_cost_sheet(**kwargs):
    return CostSheet.objects.create(name='Test Sheet', **kwargs)


def add_material(cost_sheet, cost_by_unit, qty):
    material = DirectMaterial.objects.create(name='Mat', unit='kg', cost_by_unit=cost_by_unit)
    return CostSheetMaterial.objects.create(
        cost_sheet=cost_sheet, material=material, qty=qty, total_cost=0,
    )


def add_labor(cost_sheet, cost_by_unit, qty):
    labor = DirectLabor.objects.create(name='Lab', time_unit='h', cost_by_unit=float(cost_by_unit))
    return CostSheetLabor.objects.create(
        cost_sheet=cost_sheet, labor=labor, qty=qty, total_cost=0,
    )


@pytest.mark.django_db
class TestCalculateCostSheetService:

    def test_material_cost_computed(self):
        cs = make_cost_sheet()
        add_material(cs, cost_by_unit=100, qty=3)   # 300
        add_material(cs, cost_by_unit=50,  qty=2)   # 100
        result = calculate_cost_sheet(cs)
        assert result.total_manufacturing_cost == 400

    def test_labor_cost_computed(self):
        cs = make_cost_sheet()
        add_labor(cs, cost_by_unit=80, qty=5)   # 400
        result = calculate_cost_sheet(cs)
        assert result.total_manufacturing_cost == 400

    def test_materials_and_labor_combined(self):
        cs = make_cost_sheet()
        add_material(cs, cost_by_unit=200, qty=2)   # 400
        add_labor(cs,   cost_by_unit=50,  qty=4)    # 200
        result = calculate_cost_sheet(cs)
        assert result.total_manufacturing_cost == 600

    def test_manufacturing_overhead_added(self):
        cs = make_cost_sheet(manufacturing_overhead=500)
        add_material(cs, cost_by_unit=100, qty=2)   # 200
        result = calculate_cost_sheet(cs)
        assert result.total_manufacturing_cost == 700

    def test_non_manufacturing_cost_added_to_total(self):
        cs = make_cost_sheet(manufacturing_overhead=0, non_manufacturing_cost=300)
        add_material(cs, cost_by_unit=100, qty=5)   # 500
        result = calculate_cost_sheet(cs)
        assert result.total_cost == 800

    def test_selling_price_from_margin(self):
        # total_cost=1000, margin=20% → 1000 / (1 - 0.20) = 1250
        cs = make_cost_sheet(profit_margin=20)
        add_material(cs, cost_by_unit=1000, qty=1)
        result = calculate_cost_sheet(cs)
        assert result.total_cost == 1000
        assert result.selling_price == 1250

    def test_no_margin_selling_price_equals_total_cost(self):
        cs = make_cost_sheet(profit_margin=None)
        add_material(cs, cost_by_unit=500, qty=2)
        result = calculate_cost_sheet(cs)
        assert result.selling_price == result.total_cost

    def test_zero_margin_selling_price_equals_total_cost(self):
        cs = make_cost_sheet(profit_margin=0)
        add_material(cs, cost_by_unit=400, qty=1)
        result = calculate_cost_sheet(cs)
        assert result.selling_price == 400

    def test_margin_100_raises_validation_error(self):
        from rest_framework.exceptions import ValidationError
        cs = make_cost_sheet(profit_margin=100)
        add_material(cs, cost_by_unit=100, qty=1)
        with pytest.raises(ValidationError):
            calculate_cost_sheet(cs)

    def test_updates_material_through_table_total_cost(self):
        cs  = make_cost_sheet()
        csm = add_material(cs, cost_by_unit=150, qty=4)   # expect 600
        calculate_cost_sheet(cs)
        csm.refresh_from_db()
        assert csm.total_cost == 600

    def test_updates_labor_through_table_total_cost(self):
        cs  = make_cost_sheet()
        csl = add_labor(cs, cost_by_unit=75, qty=3)   # expect 225
        calculate_cost_sheet(cs)
        csl.refresh_from_db()
        assert csl.total_cost == 225

    def test_no_components_sets_totals_to_zero(self):
        cs = make_cost_sheet()
        result = calculate_cost_sheet(cs)
        assert result.total_manufacturing_cost == 0
        assert result.total_cost == 0
        assert result.selling_price == 0

    def test_overhead_only_no_components(self):
        cs = make_cost_sheet(manufacturing_overhead=1000)
        result = calculate_cost_sheet(cs)
        assert result.total_manufacturing_cost == 1000
        assert result.total_cost == 1000

    def test_persists_to_database(self):
        cs = make_cost_sheet(profit_margin=25)
        add_material(cs, cost_by_unit=800, qty=1)   # 800 / 0.75 = ~1067
        calculate_cost_sheet(cs)
        cs.refresh_from_db()
        assert cs.total_cost == 800
        assert cs.selling_price == 1067


@pytest.mark.django_db
class TestCalculateEndpoint:

    def test_returns_200(self, api_client):
        cs = make_cost_sheet()
        response = api_client.post(reverse('costsheet-calculate', kwargs={'pk': cs.pk}))
        assert response.status_code == status.HTTP_200_OK

    def test_response_contains_updated_fields(self, api_client):
        cs = make_cost_sheet(profit_margin=20)
        add_material(cs, cost_by_unit=500, qty=2)   # 1000 / 0.8 = 1250
        response = api_client.post(reverse('costsheet-calculate', kwargs={'pk': cs.pk}))
        assert response.data['total_manufacturing_cost'] == 1000
        assert response.data['total_cost'] == 1000
        assert response.data['selling_price'] == 1250

    def test_404_for_nonexistent_cost_sheet(self, api_client):
        response = api_client.post(reverse('costsheet-calculate', kwargs={'pk': 99999}))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_idempotent_recalculate(self, api_client):
        cs = make_cost_sheet(profit_margin=10)
        add_material(cs, cost_by_unit=900, qty=1)
        api_client.post(reverse('costsheet-calculate', kwargs={'pk': cs.pk}))
        response = api_client.post(reverse('costsheet-calculate', kwargs={'pk': cs.pk}))
        assert response.status_code == status.HTTP_200_OK
        cs.refresh_from_db()
        assert cs.total_cost == 900
