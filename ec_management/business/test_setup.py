import pytest
from django.urls import reverse
from rest_framework import status
from ec_accounts.models import Account
from business.models import BusinessConfig
from business.services import setup_business
from conftest import AccountFactory

SETUP_URL = reverse('business-setup')


@pytest.mark.django_db
class TestSetupPost:

    def test_creates_eight_standard_accounts(self, api_client):
        response = api_client.post(SETUP_URL, {'company_name': 'ACME', 'currency': 'USD'}, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert Account.objects.count() == 8

    def test_is_idempotent(self, api_client):
        api_client.post(SETUP_URL, {'company_name': 'ACME'}, format='json')
        api_client.post(SETUP_URL, {'company_name': 'ACME'}, format='json')
        assert Account.objects.count() == 8
        assert BusinessConfig.objects.count() == 1

    def test_returns_config_with_nested_accounts(self, api_client):
        response = api_client.post(SETUP_URL, {'company_name': 'ACME', 'currency': 'USD'}, format='json')
        data = response.data
        assert data['company_name'] == 'ACME'
        assert data['currency'] == 'USD'
        assert data['cash_account']['code'] == '1000'
        assert data['receivable_account']['code'] == '1100'
        assert data['payable_account']['code'] == '2000'
        assert data['revenue_account']['code'] == '4000'
        assert data['inventory_account']['code'] == '1200'
        assert data['expense_account']['code'] == '6000'

    def test_currency_defaults_to_usd(self, api_client):
        response = api_client.post(SETUP_URL, {'company_name': 'ACME'}, format='json')
        assert response.data['currency'] == 'USD'

    def test_missing_company_name_returns_400(self, api_client):
        response = api_client.post(SETUP_URL, {}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_existing_account_codes_are_reused(self, api_client):
        AccountFactory(code='1000', type=Account.ASSET)
        api_client.post(SETUP_URL, {'company_name': 'ACME'}, format='json')
        assert Account.objects.filter(code='1000').count() == 1


@pytest.mark.django_db
class TestSetupGet:

    def test_returns_config_when_configured(self, api_client):
        api_client.post(SETUP_URL, {'company_name': 'ACME'}, format='json')
        response = api_client.get(SETUP_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['company_name'] == 'ACME'

    def test_returns_404_when_not_configured(self, api_client):
        response = api_client.get(SETUP_URL)
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestSetupPatch:

    def test_updates_company_name(self, api_client):
        api_client.post(SETUP_URL, {'company_name': 'ACME'}, format='json')
        response = api_client.patch(SETUP_URL, {'company_name': 'New Name'}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['company_name'] == 'New Name'

    def test_remaps_cash_account(self, api_client):
        api_client.post(SETUP_URL, {'company_name': 'ACME'}, format='json')
        new_account = AccountFactory(code='1050', type=Account.ASSET)
        response = api_client.patch(SETUP_URL, {'cash_account': new_account.id}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['cash_account']['code'] == '1050'

    def test_patch_without_config_returns_404(self, api_client):
        response = api_client.patch(SETUP_URL, {'company_name': 'X'}, format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestSetupService:

    def test_setup_business_creates_config(self):
        config = setup_business('ACME Corp', 'USD')
        assert BusinessConfig.get() is not None
        assert config.company_name == 'ACME Corp'
        assert config.cash_account.code == '1000'
        assert config.revenue_account.type == Account.INCOME
        assert config.expense_account.type == Account.EXPENSE

    def test_setup_business_is_idempotent(self):
        setup_business('First')
        setup_business('Second')
        assert BusinessConfig.objects.count() == 1
        assert BusinessConfig.get().company_name == 'Second'
