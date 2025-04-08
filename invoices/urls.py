from django.urls import path
from invoices.api import InvoiceListView

app_name = "invoices"
urlpatterns = [
        path("invoices/", InvoiceListView.as_view(), name="invoice-api-list"),
        path("invoices/<int:pk>/", InvoiceListView.as_view(), name="invoice-api-detail"),
        ]
