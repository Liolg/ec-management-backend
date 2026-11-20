import pytest
from rest_framework.test import APIClient
from factory.django import DjangoModelFactory
from factory import Faker, SubFactory
from ec_accounts.models import Account, Entry, Line
from decimal import Decimal

from products.models import DirectMaterial, DirectLabor, CostSheet, Product, StockMovement

class DirectMaterialFactory(DjangoModelFactory):
    class Meta:
        model = DirectMaterial

    name = Faker('word')
    unit = Faker('word')
    cost_by_unit = Faker('random_int', min=10, max=1000)

class DirectLaborFactory(DjangoModelFactory):
    class Meta:
        model = DirectLabor

    name = Faker('word')
    time_unit = Faker('word')
    cost_by_unit = Faker('pyfloat', positive=True, max_value=100.0)

class CostSheetFactory(DjangoModelFactory):
    class Meta:
        model = CostSheet

    name = Faker('word')
    manufacturing_overhead = Faker('random_int', min=100, max=10000)
    total_manufacturing_cost = Faker('random_int', min=1000, max=20000)
    non_manufacturing_cost = Faker('random_int', min=500, max=5000)
    total_cost = Faker('random_int', min=1500, max=25000)
    profit_margin = Faker('random_int', min=5, max=50)
    selling_price = Faker('random_int', min=2000, max=30000)
    unit = Faker('word')

class ProductFactory(DjangoModelFactory):
    class Meta:
        model = Product

    name = Faker('word')
    cost_sheet = SubFactory(CostSheetFactory)

@pytest.fixture
def api_client(django_user_model):
    user = django_user_model.objects.create_user(
        username='api-test-user',
        password='api-test-password',
    )
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def unauthenticated_api_client():
    return APIClient()

@pytest.fixture
def business_config():
    from business.services import setup_business
    return setup_business('Test Company', 'USD')

class StockMovementFactory(DjangoModelFactory):
    class Meta:
        model = StockMovement

    product   = SubFactory(ProductFactory)
    qty       = Faker('random_int', min=1, max=100)
    direction = StockMovement.DIRECTION_IN
    date      = Faker('date_this_year')

class AccountFactory(DjangoModelFactory):
    class Meta:
        model = Account

    code = Faker('bothify', text='####')
    name = Faker('company')
    type = Account.ASSET

class EntryFactory(DjangoModelFactory):
    class Meta:
        model = Entry

    date = Faker('date_this_year')
    description = Faker('sentence')

class LineFactory(DjangoModelFactory):
    class Meta:
        model = Line

    entry = SubFactory(EntryFactory)
    account = SubFactory(AccountFactory)
    value = Decimal('100.00')
    type = 'D'
