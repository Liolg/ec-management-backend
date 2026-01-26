from decimal import Decimal
from django.db import transaction
from .models import Entry, Line
from django.core.exceptions import ValidationError
from products.models import ProductItem

def validate_entry(lines):
    total_debit = Decimal('0.00')
    total_credit = Decimal('0.00')
    for line in lines:
        v = Decimal(str(line.get('value', 0)))
        if line.get('type') == 'D':
            total_debit += v
        else:
            total_credit += v
    if total_debit != total_credit:
        raise ValidationError(f'Asiento desbalanceado: total_debit={total_debit} != total_credit={total_credit}')

def get_create_update_lines(lines):
    create_lines = []
    update_lines = []
    for line in lines:
        if line.get('id'):
            update_lines.append(line)
        else:
            create_lines.append(line)
    return create_lines, update_lines

def delete_obsolete_lines(previous_lines, updated_lines):
    lines_to_delete = set(previous_lines) - set(updated_lines)
    for line_id in lines_to_delete:
        Line.objects.get(pk=line_id).delete()

def create_update_entry(instance=None, data=None):
    lines = data.get('lines', [])
    validate_entry(lines)
    lines_list_to_create, lines_list_to_update = get_create_update_lines(lines)

    with transaction.atomic():
        bulk_create_lines = []
        bulk_update_lines = []
        if instance:
            entry = instance
        else:
            entry = Entry.objects.create(date=data.get('date'), description=data.get('description',''), reference=data.get('reference'))
        for line in lines_list_to_create:
            new_line=Line(entry=entry, account=line['account'], value=line['value'], description=line['description'],type=line['type'])
            bulk_create_lines.append(new_line)
        for line in lines_list_to_update:
            line_id=line.get('id')
            ln=Line.objects.get(pk=line_id)
            ln.entry=entry
            ln.value=line.get('value', ln.value)
            ln.description=line.get('description', ln.description)
            ln.account=line.get('account', ln.account)
            ln.type=line.get('type', ln.type)
            bulk_update_lines.append(ln)
            # bulk_update_lines.append(Line(id=line['id'], entry=entry, account=line['account'], value=line['value'], description=line['description']))
        previous_lines=[e.id for e in entry.lines.all()]
        Line.objects.bulk_create(bulk_create_lines)
        Line.objects.bulk_update(bulk_update_lines,['entry','account','value','description','type'])
        updated_lines=[e.id for e in bulk_update_lines]
        delete_obsolete_lines(previous_lines, updated_lines)
        entry.refresh_from_db()
        return entry
