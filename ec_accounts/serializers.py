from rest_framework import serializers
from .models import Account, Entry, Line
from .services import validate_lines_balance, update_entry, create_entry
from products.serializers import ProductItemSerializer
from products.models import ProductItem, Product


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'code', 'name', 'type']

class LineListSerializer(serializers.ListSerializer):

    def validate(self, data):
        validate_lines_balance(data)
        lines_ids = [item.get("id") for item in data if item.get("id")]
        if lines_ids:
            existing_ids = set(
                Line.objects.filter(id__in=lines_ids).values_list("id", flat=True)
            )
            missing_ids = set(lines_ids) - existing_ids
            if missing_ids:
                raise serializers.ValidationError(
                    f"Lines with id(s) {missing_ids} do not exist"
                )
        product_items_ids = []
        products_ids=[]
        for line in data:
            product_item = line.get("product_item")
            if product_item is None:
                continue
            product_item_id = product_item.get("id")
            product_id = product_item.get("product")
            if product_item_id:
                product_items_ids.append(product_item_id)
            if product_id:
                products_ids.append(product_id)
        if product_items_ids:
            existing_product_items = set(
                ProductItem.objects.filter(id__in=product_items_ids).values_list("id", flat=True)
            )
            missing_product_items = set(product_items_ids) - existing_product_items
            if missing_product_items:
                raise serializers.ValidationError(
                    {"product_item": f"ProductItem id(s) {missing_product_items} do not exist"}
                )
        if products_ids:
            existing_products = set(
                Product.objects.filter(id__in=products_ids).values_list("id", flat=True)
            )
            missing_products = set(products_ids) - existing_products
            if missing_products:
                raise serializers.ValidationError(
                    {"product_item": f"Product id(s) {missing_products} do not exist"}
                )
        return data

class LineSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    product_item = ProductItemSerializer(required=False)

    class Meta:
        model = Line
        fields = ['id','account','description','value','type','product_item']
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
        entry=create_entry(validated_data)
        return entry

    def update(self, instance, validated_data):
        entry=update_entry(instance, data=validated_data)
        return entry
