from rest_framework import serializers
from ec_accounts.models import Account
from ec_accounts.serializers import AccountSerializer
from products.models import Product
from .models import BusinessConfig, Sale, Purchase, Expense, Payment, PAYMENT_CHOICES


# ---------------------------------------------------------------------------
# BusinessConfig
# ---------------------------------------------------------------------------

class BusinessConfigSerializer(serializers.ModelSerializer):
    cash_account       = AccountSerializer()
    receivable_account = AccountSerializer()
    payable_account    = AccountSerializer()
    revenue_account    = AccountSerializer()
    cogs_account       = AccountSerializer(allow_null=True)
    inventory_account  = AccountSerializer()
    expense_account    = AccountSerializer()

    class Meta:
        model  = BusinessConfig
        fields = [
            'company_name', 'currency',
            'cash_account', 'receivable_account', 'payable_account',
            'revenue_account', 'cogs_account', 'inventory_account', 'expense_account',
        ]


class SetupSerializer(serializers.Serializer):
    company_name = serializers.CharField(max_length=100)
    currency     = serializers.CharField(max_length=10, default='USD')


class BusinessConfigPatchSerializer(serializers.Serializer):
    company_name       = serializers.CharField(max_length=100, required=False)
    currency           = serializers.CharField(max_length=10, required=False)
    cash_account       = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all(), required=False)
    receivable_account = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all(), required=False)
    payable_account    = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all(), required=False)
    revenue_account    = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all(), required=False)
    cogs_account       = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all(), required=False, allow_null=True)
    inventory_account  = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all(), required=False)
    expense_account    = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all(), required=False)


# ---------------------------------------------------------------------------
# Sales
# ---------------------------------------------------------------------------

class SaleSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model  = Sale
        fields = [
            'id', 'product', 'product_name', 'qty', 'unit_price', 'total_amount',
            'date', 'customer_name', 'payment_method', 'status', 'entry', 'created_at',
        ]


class SaleCreateSerializer(serializers.Serializer):
    product        = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    qty            = serializers.IntegerField(min_value=1)
    unit_price     = serializers.DecimalField(max_digits=18, decimal_places=2, required=False, allow_null=True, default=None)
    date           = serializers.DateField()
    customer_name  = serializers.CharField(max_length=100, required=False, allow_blank=True, default='')
    payment_method = serializers.ChoiceField(choices=PAYMENT_CHOICES, default='cash')


# ---------------------------------------------------------------------------
# Purchases
# ---------------------------------------------------------------------------

class PurchaseSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model  = Purchase
        fields = [
            'id', 'product', 'product_name', 'qty', 'unit_cost', 'total_amount',
            'date', 'supplier_name', 'payment_method', 'status', 'entry', 'created_at',
        ]


class PurchaseCreateSerializer(serializers.Serializer):
    product        = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    qty            = serializers.IntegerField(min_value=1)
    unit_cost      = serializers.DecimalField(max_digits=18, decimal_places=2)
    date           = serializers.DateField()
    supplier_name  = serializers.CharField(max_length=100, required=False, allow_blank=True, default='')
    payment_method = serializers.ChoiceField(choices=PAYMENT_CHOICES, default='cash')


# ---------------------------------------------------------------------------
# Expenses
# ---------------------------------------------------------------------------

class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Expense
        fields = ['id', 'description', 'category', 'amount', 'date', 'payment_method', 'status', 'entry', 'created_at']


class ExpenseCreateSerializer(serializers.Serializer):
    description    = serializers.CharField(max_length=200)
    category       = serializers.ChoiceField(choices=Expense.CATEGORY_CHOICES, default='other')
    amount         = serializers.DecimalField(max_digits=18, decimal_places=2)
    date           = serializers.DateField()
    payment_method = serializers.ChoiceField(choices=PAYMENT_CHOICES, default='cash')


# ---------------------------------------------------------------------------
# Payments
# ---------------------------------------------------------------------------

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Payment
        fields = [
            'id', 'direction', 'amount', 'date', 'counterparty_name',
            'related_sale', 'related_purchase', 'status', 'entry', 'created_at',
        ]


class PaymentCreateSerializer(serializers.Serializer):
    direction         = serializers.ChoiceField(choices=Payment.DIRECTION_CHOICES)
    amount            = serializers.DecimalField(max_digits=18, decimal_places=2)
    date              = serializers.DateField()
    counterparty_name = serializers.CharField(max_length=100, required=False, allow_blank=True, default='')
    related_sale      = serializers.PrimaryKeyRelatedField(queryset=Sale.objects.all(), required=False, allow_null=True, default=None)
    related_purchase  = serializers.PrimaryKeyRelatedField(queryset=Purchase.objects.all(), required=False, allow_null=True, default=None)


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

class PeriodSerializer(serializers.Serializer):
    start = serializers.DateField(required=False, allow_null=True, default=None)
    end   = serializers.DateField(required=False, allow_null=True, default=None)

    def validate(self, data):
        start = data.get('start')
        end   = data.get('end')
        if start and end and start > end:
            raise serializers.ValidationError({'start': 'start must be before or equal to end.'})
        return data
