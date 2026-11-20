import pytest
from django.urls import reverse
from rest_framework import status
from ec_accounts.models import Account, Entry, Line
from conftest import AccountFactory, EntryFactory, LineFactory
from decimal import Decimal

@pytest.mark.django_db
class TestAccountAPI:
    def test_list_accounts(self, api_client):
        AccountFactory.create_batch(3)
        url = reverse('account-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3

    def test_create_account(self, api_client):
        url = reverse('account-list')
        data = {
            "code": "1101",
            "name": "Cash",
            "type": Account.ASSET
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Account.objects.filter(code="1101").exists()

@pytest.mark.django_db
class TestEntryAPI:
    def test_list_entries(self, api_client):
        EntryFactory.create_batch(2)
        url = reverse('entry-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_create_balanced_entry(self, api_client):
        acc1 = AccountFactory(code="1001", type=Account.ASSET)
        acc2 = AccountFactory(code="4001", type=Account.INCOME)
        url = reverse('entry-list')
        data = {
            "date": "2025-01-01",
            "description": "Test Entry",
            "reference": "REF001",
            "lines": [
                {
                    "account": acc1.id,
                    "description": "Debit line",
                    "value": "100.00",
                    "type": "D"
                },
                {
                    "account": acc2.id,
                    "description": "Credit line",
                    "value": "100.00",
                    "type": "C"
                }
            ]
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert Entry.objects.count() == 1
        entry = Entry.objects.first()
        assert entry.lines.count() == 2
        assert entry.is_balanced()

    def test_create_unbalanced_entry_fails(self, api_client):
        acc1 = AccountFactory()
        acc2 = AccountFactory()
        url = reverse('entry-list')
        data = {
            "date": "2025-01-01",
            "description": "Unbalanced Entry",
            "reference": "REF002",
            "lines": [
                {
                    "account": acc1.id,
                    "value": "100.00",
                    "type": "D"
                },
                {
                    "account": acc2.id,
                    "value": "90.00",
                    "type": "C"
                }
            ]
        }
        # In Django REST Framework, if the service raises ValidationError (django core), 
        # it usually results in 500 if not handled, or 400 if it's a serializers.ValidationError.
        # Looking at serializers.py, it calls validate_lines_balance in LineListSerializer.validate.
        # LineListSerializer.validate raises serializers.ValidationError, which DRF catches as 400.
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_void_entry(self, api_client):
        entry = EntryFactory()
        url = reverse('entry-void', kwargs={'pk': entry.pk})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        entry.refresh_from_db()
        assert entry.voided is True

    def test_update_entry(self, api_client):
        entry = EntryFactory(description="Initial description")
        acc1 = AccountFactory()
        acc2 = AccountFactory()
        line1 = LineFactory(entry=entry, account=acc1, value=Decimal('100.00'), type='D')
        line2 = LineFactory(entry=entry, account=acc2, value=Decimal('100.00'), type='C')
        
        url = reverse('entry-detail', kwargs={'pk': entry.pk})
        data = {
            "date": "2025-01-02",
            "description": "Updated Entry",
            "reference": "REF002",
            "lines": [
                {
                    "id": line1.id,
                    "account": acc1.id,
                    "description": "Updated line",
                    "value": "200.00",
                    "type": "D"
                },
                {
                    "id": line2.id,
                    "account": acc2.id,
                    "description": "Unchanged line",
                    "value": "200.00",
                    "type": "C"
                }
            ]
        }
        response = api_client.put(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        entry.refresh_from_db()
        assert entry.description == "Updated Entry"
        assert entry.lines.count() == 2
        
        # Verify lines were updated
        line1.refresh_from_db()
        assert line1.value == Decimal('200.00')

    def test_delete_entry(self, api_client):
        entry = EntryFactory()
        url = reverse('entry-detail', kwargs={'pk': entry.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Entry.objects.filter(pk=entry.pk).exists()

    def test_patch_without_lines_preserves_lines(self, api_client):
        entry = EntryFactory(description='Before')
        LineFactory(entry=entry, type='D')
        LineFactory(entry=entry, type='C')

        response = api_client.patch(
            reverse('entry-detail', kwargs={'pk': entry.pk}),
            {'description': 'After'},
            format='json',
        )

        assert response.status_code == status.HTTP_200_OK
        assert entry.lines.count() == 2

    def test_patch_rejects_foreign_line_id(self, api_client):
        entry = EntryFactory()
        other_entry = EntryFactory()
        account = AccountFactory()
        own_debit = LineFactory(entry=entry, account=account, type='D')
        own_credit = LineFactory(entry=entry, account=account, type='C')
        foreign = LineFactory(entry=other_entry, account=account, type='D')

        response = api_client.patch(
            reverse('entry-detail', kwargs={'pk': entry.pk}),
            {'lines': [
                {'id': foreign.pk, 'account': account.pk, 'value': '100.00', 'type': 'D'},
                {'id': own_credit.pk, 'account': account.pk, 'value': '100.00', 'type': 'C'},
            ]},
            format='json',
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Line.objects.get(pk=foreign.pk).entry == other_entry
        assert Line.objects.filter(pk=own_debit.pk).exists()

    def test_patch_rejects_duplicate_line_ids(self, api_client):
        entry = EntryFactory()
        account = AccountFactory()
        line = LineFactory(entry=entry, account=account, type='D')

        response = api_client.patch(
            reverse('entry-detail', kwargs={'pk': entry.pk}),
            {'lines': [
                {'id': line.pk, 'account': account.pk, 'value': '100.00', 'type': 'D'},
                {'id': line.pk, 'account': account.pk, 'value': '100.00', 'type': 'C'},
            ]},
            format='json',
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_read_keeps_numeric_account_and_text_code(self, api_client):
        entry = EntryFactory()
        account = AccountFactory(code='0010')
        LineFactory(entry=entry, account=account, type='D')

        response = api_client.get(reverse('entry-detail', kwargs={'pk': entry.pk}))
        account_response = api_client.get(reverse('account-detail', kwargs={'pk': account.pk}))

        assert response.data['source'] is None
        assert response.data['lines'][0]['account'] == account.pk
        assert account_response.data['code'] == '0010'

    def test_generated_entry_cannot_be_patched(self, api_client, business_config):
        from business.services import create_expense

        expense = create_expense({
            'description': 'Rent', 'amount': Decimal('10.00'),
            'date': '2026-05-01', 'payment_method': 'cash',
        })

        get_response = api_client.get(
            reverse('entry-detail', kwargs={'pk': expense.entry_id}),
        )
        patch_response = api_client.patch(
            reverse('entry-detail', kwargs={'pk': expense.entry_id}),
            {'description': 'Changed'},
            format='json',
        )

        assert get_response.data['source'] == {'type': 'expense', 'id': expense.pk}
        assert patch_response.status_code == status.HTTP_409_CONFLICT

    def test_referenced_account_delete_returns_conflict(self, api_client):
        account = AccountFactory()
        LineFactory(account=account)

        response = api_client.delete(
            reverse('account-detail', kwargs={'pk': account.pk}),
        )

        assert response.status_code == status.HTTP_409_CONFLICT
