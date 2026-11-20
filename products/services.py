from django.db import transaction
from rest_framework.exceptions import ValidationError

from .models import CostSheet, CostSheetMaterial, CostSheetLabor


@transaction.atomic
def calculate_cost_sheet(cost_sheet):
    # Viewsets prefetch component rows for reads. Calculations must always use
    # the rows committed by the current nested write, not a stale prefetch.
    cost_sheet._prefetched_objects_cache = {}
    materials = list(cost_sheet.costsheetmaterial_set.select_related('material').all())
    labors    = list(cost_sheet.costsheetlabor_set.select_related('labor').all())

    # Per-row totals
    for csm in materials:
        csm.total_cost = csm.qty * csm.material.cost_by_unit
    for csl in labors:
        csl.total_cost = round(csl.qty * csl.labor.cost_by_unit)

    if materials:
        CostSheetMaterial.objects.bulk_update(materials, ['total_cost'])
    if labors:
        CostSheetLabor.objects.bulk_update(labors, ['total_cost'])

    material_cost = sum(csm.total_cost for csm in materials)
    labor_cost    = sum(csl.total_cost for csl in labors)

    total_manufacturing_cost = material_cost + labor_cost + (cost_sheet.manufacturing_overhead or 0)
    total_cost               = total_manufacturing_cost + (cost_sheet.non_manufacturing_cost or 0)

    profit_margin = cost_sheet.profit_margin
    if profit_margin:
        if profit_margin >= 100:
            raise ValidationError('Profit margin must be less than 100%.')
        selling_price = round(total_cost / (1 - profit_margin / 100))
    else:
        selling_price = total_cost

    cost_sheet.total_manufacturing_cost = total_manufacturing_cost
    cost_sheet.total_cost               = total_cost
    cost_sheet.selling_price            = selling_price
    cost_sheet.save()

    return cost_sheet
