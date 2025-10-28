from rest_framework import serializers
from .models import Account, Entry, Line
from .services import create_journal_entry
from products.serializers import ProductItemSerializer


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'code', 'name', 'type']


class EntryLineSerializer(serializers.ModelSerializer):
    account = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all())
    product_item = ProductItemSerializer(source='productitem', read_only=True)

    class Meta:
        model = Line
        fields = ['id', 'account', 'description', 'debit', 'credit', 'product_item']


class EntrySerializer(serializers.ModelSerializer):
    lines = EntryLineSerializer(many=True)

    class Meta:
        model = Entry
        fields = ['id', 'date', 'description', 'reference', 'voided', 'lines']
        read_only_fields = ['id', 'voided']

    def create(self, validated_data):
        lines_data = validated_data.pop('lines')
        # preparar lista para el servicio
        prepared = []
        for ln in lines_data:
            prepared.append({
                'account': ln['account'],
                'debit': ln.get('debit', 0),
                'credit': ln.get('credit', 0),
                'description': ln.get('description', ''),
            })
        entry = create_journal_entry(date=validated_data['date'], lines=prepared, description=validated_data.get('description', ''), reference=validated_data.get('reference'))
        return entry
