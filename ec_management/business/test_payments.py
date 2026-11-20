import pytest
from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from business.models import Payment

PAYMENTS_URL = reverse('payment-list')


@pytest.mark.django_db
class TestCreatePayment:

    def test_received_payment_returns_201(self, api_client, business_config):
        response = api_client.post(PAYMENTS_URL, {
            'direction': 'received', 'amount': '500.00',
            'date': '2026-05-01', 'counterparty_name': 'Client A',
        }, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_received_payment_debits_cash(self, api_client, business_config):
        api_client.post(PAYMENTS_URL, {
            'direction': 'received', 'amount': '300.00', 'date': '2026-05-01',
        }, format='json')
        payment    = Payment.objects.first()
        debit_line = payment.entry.lines.get(type='D')
        assert debit_line.account == business_config.cash_account
        assert debit_line.value == Decimal('300.00')

    def test_received_payment_credits_receivable(self, api_client, business_config):
        api_client.post(PAYMENTS_URL, {
            'direction': 'received', 'amount': '300.00', 'date': '2026-05-01',
        }, format='json')
        payment     = Payment.objects.first()
        credit_line = payment.entry.lines.get(type='C')
        assert credit_line.account == business_config.receivable_account

    def test_made_payment_debits_payable(self, api_client, business_config):
        api_client.post(PAYMENTS_URL, {
            'direction': 'made', 'amount': '200.00', 'date': '2026-05-01',
        }, format='json')
        payment    = Payment.objects.first()
        debit_line = payment.entry.lines.get(type='D')
        assert debit_line.account == business_config.payable_account

    def test_made_payment_credits_cash(self, api_client, business_config):
        api_client.post(PAYMENTS_URL, {
            'direction': 'made', 'amount': '200.00', 'date': '2026-05-01',
        }, format='json')
        payment     = Payment.objects.first()
        credit_line = payment.entry.lines.get(type='C')
        assert credit_line.account == business_config.cash_account

    def test_invalid_direction_returns_400(self, api_client, business_config):
        response = api_client.post(PAYMENTS_URL, {
            'direction': 'wrong', 'amount': '100.00', 'date': '2026-05-01',
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_fails_without_business_config(self, api_client):
        response = api_client.post(PAYMENTS_URL, {
            'direction': 'received', 'amount': '100.00', 'date': '2026-05-01',
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_payment_linked_to_sale(self, api_client, business_config):
        from conftest import ProductFactory
        product     = ProductFactory()
        sale_resp   = api_client.post(reverse('sale-list'), {
            'product': product.id, 'qty': 1, 'unit_price': '100.00', 'date': '2026-05-01',
            'payment_method': 'credit',
        }, format='json')
        sale_id  = sale_resp.data['id']
        response = api_client.post(PAYMENTS_URL, {
            'direction': 'received', 'amount': '100.00',
            'date': '2026-05-01', 'related_sale': sale_id,
        }, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['related_sale'] == sale_id

    def test_received_payment_rejects_purchase_link(self, api_client, business_config):
        from conftest import ProductFactory
        product = ProductFactory()
        purchase = api_client.post(reverse('purchase-list'), {
            'product': product.pk, 'qty': 1, 'unit_cost': '10.00',
            'date': '2026-05-01', 'payment_method': 'credit',
        }, format='json')

        response = api_client.post(PAYMENTS_URL, {
            'direction': 'received', 'amount': '10.00',
            'date': '2026-05-01', 'related_purchase': purchase.data['id'],
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_non_positive_amount_is_rejected(self, api_client, business_config):
        response = api_client.post(PAYMENTS_URL, {
            'direction': 'received', 'amount': '0.00', 'date': '2026-05-01',
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestVoidPayment:

    def test_void_sets_status_voided(self, api_client, business_config):
        create_resp = api_client.post(PAYMENTS_URL, {
            'direction': 'received', 'amount': '100.00', 'date': '2026-05-01',
        }, format='json')
        payment_id = create_resp.data['id']
        response   = api_client.post(reverse('payment-void', kwargs={'pk': payment_id}))
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'voided'

    def test_void_marks_entry_voided(self, api_client, business_config):
        create_resp = api_client.post(PAYMENTS_URL, {
            'direction': 'made', 'amount': '50.00', 'date': '2026-05-01',
        }, format='json')
        payment_id = create_resp.data['id']
        api_client.post(reverse('payment-void', kwargs={'pk': payment_id}))
        payment = Payment.objects.get(pk=payment_id)
        assert payment.entry.voided is True

    def test_void_twice_returns_400(self, api_client, business_config):
        create_resp = api_client.post(PAYMENTS_URL, {
            'direction': 'received', 'amount': '75.00', 'date': '2026-05-01',
        }, format='json')
        payment_id = create_resp.data['id']
        void_url   = reverse('payment-void', kwargs={'pk': payment_id})
        api_client.post(void_url)
        response = api_client.post(void_url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
