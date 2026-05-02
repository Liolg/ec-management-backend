import pytest
from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from business.models import Expense

EXPENSES_URL = reverse('expense-list')


@pytest.mark.django_db
class TestCreateExpense:

    def test_cash_expense_returns_201(self, api_client, business_config):
        response = api_client.post(EXPENSES_URL, {
            'description': 'Office rent', 'category': 'rent',
            'amount': '1500.00', 'date': '2026-05-01', 'payment_method': 'cash',
        }, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_cash_expense_debits_expense_account(self, api_client, business_config):
        api_client.post(EXPENSES_URL, {
            'description': 'Electric bill', 'category': 'utilities',
            'amount': '300.00', 'date': '2026-05-01', 'payment_method': 'cash',
        }, format='json')
        expense    = Expense.objects.first()
        debit_line = expense.entry.lines.get(type='D')
        assert debit_line.account == business_config.expense_account
        assert debit_line.value == Decimal('300.00')

    def test_cash_expense_credits_cash_account(self, api_client, business_config):
        api_client.post(EXPENSES_URL, {
            'description': 'Supplies', 'category': 'supplies',
            'amount': '50.00', 'date': '2026-05-01', 'payment_method': 'cash',
        }, format='json')
        expense     = Expense.objects.first()
        credit_line = expense.entry.lines.get(type='C')
        assert credit_line.account == business_config.cash_account

    def test_credit_expense_credits_payable_account(self, api_client, business_config):
        api_client.post(EXPENSES_URL, {
            'description': 'Marketing campaign', 'category': 'marketing',
            'amount': '800.00', 'date': '2026-05-01', 'payment_method': 'credit',
        }, format='json')
        expense     = Expense.objects.first()
        credit_line = expense.entry.lines.get(type='C')
        assert credit_line.account == business_config.payable_account

    def test_defaults_category_to_other(self, api_client, business_config):
        api_client.post(EXPENSES_URL, {
            'description': 'Misc cost', 'amount': '100.00', 'date': '2026-05-01',
        }, format='json')
        assert Expense.objects.first().category == 'other'

    def test_all_valid_categories_accepted(self, api_client, business_config):
        categories = ['rent', 'utilities', 'salaries', 'marketing', 'supplies', 'transport', 'other']
        for i, cat in enumerate(categories):
            response = api_client.post(EXPENSES_URL, {
                'description': f'Expense {i}', 'category': cat,
                'amount': '10.00', 'date': '2026-05-01',
            }, format='json')
            assert response.status_code == status.HTTP_201_CREATED

    def test_invalid_category_returns_400(self, api_client, business_config):
        response = api_client.post(EXPENSES_URL, {
            'description': 'Bad', 'category': 'unknown',
            'amount': '10.00', 'date': '2026-05-01',
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_fails_without_business_config(self, api_client):
        response = api_client.post(EXPENSES_URL, {
            'description': 'Rent', 'amount': '500.00', 'date': '2026-05-01',
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestVoidExpense:

    def test_void_sets_status_voided(self, api_client, business_config):
        create_resp = api_client.post(EXPENSES_URL, {
            'description': 'Rent', 'amount': '500.00', 'date': '2026-05-01',
        }, format='json')
        expense_id = create_resp.data['id']
        response   = api_client.post(reverse('expense-void', kwargs={'pk': expense_id}))
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'voided'

    def test_void_marks_entry_voided(self, api_client, business_config):
        create_resp = api_client.post(EXPENSES_URL, {
            'description': 'Utilities', 'amount': '200.00', 'date': '2026-05-01',
        }, format='json')
        expense_id = create_resp.data['id']
        api_client.post(reverse('expense-void', kwargs={'pk': expense_id}))
        expense = Expense.objects.get(pk=expense_id)
        assert expense.entry.voided is True

    def test_void_twice_returns_400(self, api_client, business_config):
        create_resp = api_client.post(EXPENSES_URL, {
            'description': 'Rent', 'amount': '500.00', 'date': '2026-05-01',
        }, format='json')
        expense_id = create_resp.data['id']
        void_url   = reverse('expense-void', kwargs={'pk': expense_id})
        api_client.post(void_url)
        response = api_client.post(void_url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
