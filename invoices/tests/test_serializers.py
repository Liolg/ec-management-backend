import pytest
from invoices.models import Invoice
from invoices.serializers import InvoiceSerializer

@pytest.mark.django_db
def test_valid_invoice_serializer():
    valid_data = {
            "employee": "Alfred"
        }
    serializer = InvoiceSerializer(data = valid_data)
    assert serializer.is_valid()
    invoice = serializer.save()
    assert Invoice.objects.count() == 1
    created_movie = Invoice.objects.get()
    assert created_movie.employee == valid_data["employee"]

@pytest.mark.django_db
def test_invalid_invoice_serialicer():
    invalid_data = {}
    serializer = InvoiceSerializer(data = invalid_data)
    assert not serializer.is_valid()
    assert "employee" in serializer.errors

@pytest.mark.django_db
def test_serialize_invoice_instance():
    invoice = Invoice.objects.create(employee="Juan")
    serializer = InvoiceSerializer(invoice)
    assert serializer.data == {
            "id": invoice.id,
            "employee": invoice.employee
            }
