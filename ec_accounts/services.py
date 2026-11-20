from decimal import Decimal
from django.db import transaction
from .models import Entry, Line
from rest_framework.exceptions import ValidationError
from products.models import ProductItem, Product

def validate_lines_balance(lines):
    total_debit = Decimal('0.00')
    total_credit = Decimal('0.00')
    for line in lines:
        v = Decimal(str(line.get('value', 0)))
        if line.get('type') == 'D':
            total_debit += v
        else:
            total_credit += v
    if total_debit != total_credit:
        raise ValidationError(f'Unbalanced accounting entry: total_debit={total_debit} != total_credit={total_credit}')

def get_separated_create_update_lines(lines):
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
    if lines_to_delete:
        Line.objects.filter(pk__in=lines_to_delete).delete()

@transaction.atomic
def create_entry(data):
    lines_data = data.pop('lines', [])
    entry = Entry.objects.create(
        date=data.pop('date'),
        description=data.pop('description', ''),
        reference=data.pop('reference', None)
    )
    create_entry_lines(entry, lines_data)
    entry.refresh_from_db()
    return entry

def create_entry_lines(entry,lines_data):
    with transaction.atomic():
        bulk_create_lines = []
        product_items = []

        for index in range(len(lines_data)):
            line=lines_data[index]
            new_line=Line(
                entry=entry,
                account=line['account'],
                value=line['value'],
                description=line.get('description', ''),
                type=line['type']
            )
            bulk_create_lines.append(new_line)
            product_items.append(line.get('product_item',None))

        created_lines_instances=Line.objects.bulk_create(bulk_create_lines)
        product_items_to_create=[]
        for index  in range(len(product_items)):
            product_item=product_items[index]
            if product_item is None:
                continue
            product=Product.objects.get(pk=product_item.get('product'))
            qty=product_item.get('qty',0)
            line=created_lines_instances[index]
            product_items_to_create.append(ProductItem(product=product, qty=qty, entry_line=line))
        created_product_items=ProductItem.objects.bulk_create(product_items_to_create)

@transaction.atomic
def update_entry(instance, data=None):
    data = dict(data or {})
    lines_supplied = 'lines' in data
    lines = data.pop('lines', None)
    entry = Entry.objects.select_for_update().get(pk=instance.pk)

    for attr, value in data.items():
        setattr(entry, attr, value)
    entry.save()

    if not lines_supplied:
        return entry

    lines_list_to_create, lines_list_to_update = get_separated_create_update_lines(lines)
    bulk_update_lines = []
    update_lines_product_items = []

    for line in lines_list_to_update:
        line_id=line.get('id')
        try:
            ln=Line.objects.select_for_update().get(pk=line_id, entry=entry)
        except Line.DoesNotExist:
            raise ValidationError(
                f'Line {line_id} does not belong to entry {entry.pk}.'
            )
        ln.value=line.get('value', ln.value)
        ln.description=line.get('description', ln.description)
        ln.account=line.get('account', ln.account)
        ln.type=line.get('type', ln.type)
        bulk_update_lines.append(ln)
        update_lines_product_items.append(line.get('product_item',None))

    previous_lines=list(entry.lines.values_list('id', flat=True))
    create_entry_lines(entry,lines_list_to_create)
    Line.objects.bulk_update(bulk_update_lines,['account','value','description','type'])
    updated_lines=[line.id for line in bulk_update_lines]
    product_items_to_create=[]
    product_items_to_edit=[]

    for index in range(len(update_lines_product_items)):
        product_item=update_lines_product_items[index]
        if product_item is None:
            continue
        line=bulk_update_lines[index]
        if product_item.get('id'):
            try:
                prod_it=ProductItem.objects.get(
                    pk=product_item.get('id'), entry_line=line,
                )
            except ProductItem.DoesNotExist:
                raise ValidationError(
                    f'Product item {product_item.get("id")} does not belong to line {line.pk}.'
                )
            prod_it.qty=product_item.get('qty',prod_it.qty)
            product_items_to_edit.append(prod_it)
        else:
            product_id=product_item.get('product')
            product=Product.objects.get(pk=product_id)
            qty=product_item.get('qty',0)
            product_items_to_create.append(ProductItem(product=product, qty=qty, entry_line=line))

    ProductItem.objects.bulk_create(product_items_to_create)
    ProductItem.objects.bulk_update(product_items_to_edit,['qty'])
    delete_obsolete_lines(previous_lines, updated_lines)
    entry.refresh_from_db()
    return entry
