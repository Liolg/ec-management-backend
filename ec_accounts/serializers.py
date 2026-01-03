from rest_framework import serializers
from .models import Account, Entry, Line
from .services import create_update_entry
from products.serializers import ProductItemSerializer


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'code', 'name', 'type']

class LineSerializer(serializers.ModelSerializer):
    # account = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all())
    # product_item = ProductItemSerializer(source='productitem', read_only=True)
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Line
        fields = ['id', 'account', 'description', 'value', 'type',]

class EntrySerializer(serializers.ModelSerializer):
    lines = LineSerializer(many=True)

    class Meta:
        model = Entry
        fields = ['id', 'date', 'description', 'reference', 'voided', 'lines']
        read_only_fields = ['voided']
