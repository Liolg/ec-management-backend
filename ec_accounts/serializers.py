from rest_framework import serializers
from .models import Account, Entry, Line
from .services import create_update_entry
from products.serializers import ProductItemSerializer


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'code', 'name', 'type']

class LineSerializer(serializers.ModelSerializer):
    productitem = ProductItemSerializer(allow_null=True)
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Line
        fields = ['id','account','description','value','type','productitem']

    # def validate_productitem(self, value):
    #     ser = ProductItemSerializer(data=value)
    #     if ser.is_valid(raise_exception=True):
    #         return ser.validated_data
    #     return value

class EntryReadSerializer(serializers.ModelSerializer):
    lines = LineSerializer(many=True)

    class Meta:
        model = Entry
        fields = ['id', 'date', 'description', 'reference', 'voided', 'lines']
        read_only_fields = ['voided']

class EntryWriteSerializer(serializers.ModelSerializer):
    lines = LineSerializer(many=True)

    class Meta:
        model = Entry
        fields = ['id', 'date', 'description', 'reference', 'voided', 'lines']
        read_only_fields = ['voided']
