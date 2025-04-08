from factory.django import DjangoModelFactory
from factory.faker import Faker
from invoices.models import Invoice
class InvoiceFactory(DjangoModelFactory):
    class Meta:
        model=Invoice
    employee=Faker('sentence', nb_words=4)
