import pytest
from django.urls import reverse
from rest_framework import status
from ec_accounts.models import Account, Entry
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
