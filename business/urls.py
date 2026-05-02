from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    SetupView,
    SaleViewSet, PurchaseViewSet, ExpenseViewSet, PaymentViewSet,
    ReportSummaryView, ReportProfitLossView, ReportInventoryView,
)

router = DefaultRouter()
router.register(r'sales',     SaleViewSet,     basename='sale')
router.register(r'purchases', PurchaseViewSet, basename='purchase')
router.register(r'expenses',  ExpenseViewSet,  basename='expense')
router.register(r'payments',  PaymentViewSet,  basename='payment')

urlpatterns = router.urls + [
    path('setup/',               SetupView.as_view(),           name='business-setup'),
    path('reports/summary/',     ReportSummaryView.as_view(),   name='report-summary'),
    path('reports/profit-loss/', ReportProfitLossView.as_view(),name='report-profit-loss'),
    path('reports/inventory/',   ReportInventoryView.as_view(), name='report-inventory'),
]
