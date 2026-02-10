from rest_framework import serializers
from .models import Account, Entry, Line
from .services import create_update_entry
from products.serializers import ProductItemSerializer
from products.models import ProductItem


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'code', 'name', 'type']

class LineListSerializer(serializers.ListSerializer):
    productitem = ProductItemSerializer(allow_null=True)
    class Meta:
        model = Line
        fields=['__all__']
    def validate(self, data):
        ids = [item.get("id") for item in data if item.get("id")]

        if ids:
            existing_ids = set(
                Line.objects.filter(id__in=ids).values_list("id", flat=True)
            )
            missing_ids = set(ids) - existing_ids
            if missing_ids:
                raise serializers.ValidationError(
                    f"Lines with id(s) {missing_ids} do not exist"
                )
        product_ids = []
        for item in data:
            pi = item.get("productitem")
            if pi is None:
                continue
            pid = pi.get("id")
            if pid:
                product_ids.append(pid)
        if product_ids:
            existing_product_ids = set(
                ProductItem.objects.filter(id__in=product_ids).values_list("id", flat=True)
            )
            missing_product_ids = set(product_ids) - existing_product_ids
            if missing_product_ids:
                raise serializers.ValidationError(
                    {"productitem": f"ProductItem id(s) {missing_product_ids} do not exist"}
                )
        return data
    def create(self, validated_data):
        print(validated_data)

        # books = [Book(**item) for item in validated_data]
        # return Book.objects.bulk_create(books)
    def update(self, instance, validated_data):
        print(self,instance,validated_data)


class LineSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    productitem = ProductItemSerializer(allow_null=True, required=False)
    class Meta:
        model = Line
        fields = ['id','account','description','value','type','productitem']
        list_serializer_class = LineListSerializer

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
    def create(self, validated_data):
        print(validated_data)

    def update(self, instance, validated_data):
        print('-'*30)
        for (key, value) in validated_data.items():
            print(key, value)
        return instance
