import pytest
from django.urls import reverse
from rest_framework import status
from invoices.models import Invoice
from .factories import InvoiceFactory 
from django.test import override_settings
import json

@pytest.mark.django_db
def test_create_invoice(client):
    url=reverse("invoices:invoice-api-list")
    data = {"employee": "Lucas"}
    response=client.post(url, data=data)
    assert response.status_code == status.HTTP_201_CREATED, response.json()
    assert Invoice.objects.filter(employee='Lucas').count() == 1

@pytest.mark.django_db
def test_retrieve_invoice(client):
    invoice=InvoiceFactory()
    url=reverse("invoices:invoice-api-detail", kwargs={"pk": invoice.id})
    response=client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
            "id": invoice.id,
            "employee": invoice.employee,
        }

@pytest.mark.django_db
def test_update_invoice(client):
    invoice = InvoiceFactory()
    new_employee = "Antonio"
    url = reverse("invoices:invoice-api-detail", kwargs={"pk": invoice.id})
    data = {"employee": new_employee}
    response = client.put(url, data=data, content_type="application/json")
    assert response.status_code == status.HTTP_200_OK, response.json()
    invoice=Invoice.objects.filter(id=invoice.id).first()
    assert invoice
    assert invoice.employee==new_employee

@pytest.mark.django_db
def test_delete_invoice(client):
    invoice=InvoiceFactory()
    url=reverse("invoices:invoice-api-detail", kwargs={"pk": invoice.id})
    response=client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Invoice.objects.filter(id=invoice.id).exists()

@pytest.mark.django_db
@override_settings(REST_FRAMEWORK={"PAGE_SIZE": 10})
def test_list_invoices_with_pagination(client):
    invoices=InvoiceFactory.create_batch(10)
    url=reverse("invoices:invoice-api-list")
    response=client.get(url)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "count" in data
    assert "next" in data
    assert "previous" in data
    assert "results" in data
    assert data["count"] == 10
    assert data["next"] is None
    assert data["previous"] is None
    assert len(data["results"]) == 10
    
    returned_invoices_ids={ invoice["id"] for invoice in data["results"]}
    expected_invoices_ids={ invoice.id for invoice in invoices }
    assert returned_invoices_ids == expected_invoices_ids
    for invoice_data in data["results"]:
        assert set(invoice_data.keys()) == { "id", "employee" }
