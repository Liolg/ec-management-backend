from rest_framework import serializers
from invoices.models import Invoice

class InvoiceSerializer(serializers.Serializer):
    id = serializers.IntegerField(label = "Invoice ID", required = False)
    employee = serializers.CharField(max_length = 255)

    def create(self, validated_data):
        return Invoice.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.employee = validated_data.get("employee", instance.employee)
        instance.save()
        return instance
