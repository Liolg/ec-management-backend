from decimal import Decimal
from django.db import transaction
from .models import Entry, Line
from django.core.exceptions import ValidationError


def create_journal_entry(date, lines, description=None, reference=None):
    """
    Crea un EcAccountEntry con sus EcAccountLine en una transacción atómica.

    `lines` debe ser una lista de dicts con: { 'account': <Account instance>, 'debit': Decimal|float|int, 'credit': Decimal|float|int, 'description': str }

    Valida que suma(debit) == suma(credit) y que cada línea tiene sólo debit o credit (no ambos > 0).

    Retorna el EcAccountEntry creado.
    """
    # normalizar inputs a Decimal
    normalized = []
    total_debit = Decimal('0.00')
    total_credit = Decimal('0.00')

    for ln in lines:
        d = Decimal(str(ln.get('debit', 0)))
        c = Decimal(str(ln.get('credit', 0)))
        if d > Decimal('0.00') and c > Decimal('0.00'):
            raise ValidationError('Una línea no puede tener debit y credit simultáneamente')
        total_debit += d
        total_credit += c
        normalized.append({
            'account': ln['account'],
            'debit': d,
            'credit': c,
            'description': ln.get('description', ''),
        })

    if total_debit != total_credit:
        raise ValidationError(f'Asiento desbalanceado: total_debit={total_debit} != total_credit={total_credit}')

    with transaction.atomic():
        entry = Entry.objects.create(date=date, description=description or '', reference=reference)
        bulk = []
        for ln in normalized:
            bulk.append(Line(entry=entry, account=ln['account'], debit=ln['debit'], credit=ln['credit'], description=ln['description']))
        Line.objects.bulk_create(bulk)
        # refetch to ensure aggregates work
        entry.refresh_from_db()
        return entry
