import pytest
from rest_framework.exceptions import ValidationError
from ec_accounts.services import validate_lines_balance, create_entry
from ec_accounts.models import Account, Entry
from conftest import AccountFactory

@pytest.mark.django_db
def test_validate_lines_balance_success():
    lines = [
        {'value': '100.00', 'type': 'D'},
        {'value': '100.00', 'type': 'C'}
    ]
    assert validate_lines_balance(lines) is None

@pytest.mark.django_db
def test_validate_lines_balance_failure():
    lines = [
        {'value': '100.00', 'type': 'D'},
        {'value': '90.00', 'type': 'C'}
    ]
    with pytest.raises(ValidationError, match="Unbalanced accounting entry"):
        validate_lines_balance(lines)

@pytest.mark.django_db
def test_create_entry_service():
    acc1 = AccountFactory(type=Account.ASSET)
    acc2 = AccountFactory(type=Account.INCOME)
    
    data = {
        'date': '2026-04-03',
        'description': 'Test Entry',
        'reference': 'REF001',
        'lines': [
            {'account': acc1, 'value': '100.00', 'type': 'D', 'description': 'Debit'},
            {'account': acc2, 'value': '100.00', 'type': 'C', 'description': 'Credit'}
        ]
    }
    
    entry = create_entry(data)
    assert Entry.objects.count() == 1
    assert entry.lines.count() == 2
    assert entry.description == 'Test Entry'
