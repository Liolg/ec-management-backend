from rest_framework import status, views
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Invoice
from .serializers import InvoiceSerializer

class InvoiceListView(views.APIView):
    def post(self, request):
        serializer = InvoiceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk=None):
        if pk:
            invoice = get_object_or_404(Invoice, pk=pk)
            serializer = InvoiceSerializer(invoice)
            return Response(serializer.data)
        else:
            invoices = Invoice.objects.all()
            serializer = InvoiceSerializer(invoices, many=True)
            return Response({
                "count": len(serializer.data),
                "results": serializer.data,
                "next": None,
                "previous": None,
                })

    def put(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)
        serializer = InvoiceSerializer(invoice, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)
        invoice.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
