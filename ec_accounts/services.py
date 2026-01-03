from decimal import Decimal
from django.db import transaction
from .models import Entry, Line
from django.core.exceptions import ValidationError


def create_update_entry(instance=None, data=None):
    if not data:
        raise ValidationError('No data')
    total_debit = Decimal('0.00')
    total_credit = Decimal('0.00')
    lines = data.get('lines', [])
    create_lines = []
    update_lines = []
    for line in lines:
        v = Decimal(str(line.get('value', 0)))
        if(line.get('type') == 'D'):
            total_debit += v
        else:
            total_credit += v
        if line.get('id'):
            update_lines.append(line)
        else:
            create_lines.append(line)
    if total_debit != total_credit:
        raise ValidationError(f'Asiento desbalanceado: total_debit={total_debit} != total_credit={total_credit}')

    with transaction.atomic():
        if instance:
            entry = instance
        else:
            entry = Entry.objects.create(date=data.date, description=data.description or '', reference=data.reference)
        bulk_create_lines = []
        for line in create_lines:
            bulk_create_lines.append(Line(entry=entry, account=line['account'], value=line['value'], description=line['description']))
        Line.objects.bulk_create(bulk_create_lines)
        bulk_update_lines = []
        for line in update_lines:
            line_id=line.get('id')
            ln=Line.objects.get(pk=line_id)
            ln.entry=entry
            ln.value=line['value']
            ln.description=line['description']
            ln.account=line['account']
            bulk_update_lines.append(ln)
            # bulk_update_lines.append(Line(id=line['id'], entry=entry, account=line['account'], value=line['value'], description=line['description']))
        Line.objects.bulk_update(bulk_update_lines,['entry','account','value','description'])
        previous_lines=[e.id for e in entry.lines.all()]
        updated_lines=[e.id for e in bulk_update_lines]
        for l in previous_lines:
            if l not in updated_lines:
                Line.objects.get(pk=l).delete()
        entry.refresh_from_db()
        return entry
