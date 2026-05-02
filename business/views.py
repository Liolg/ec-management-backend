from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import BusinessConfig, Sale, Purchase, Expense, Payment
from .serializers import (
    BusinessConfigSerializer, SetupSerializer, BusinessConfigPatchSerializer,
    SaleSerializer, SaleCreateSerializer,
    PurchaseSerializer, PurchaseCreateSerializer,
    ExpenseSerializer, ExpenseCreateSerializer,
    PaymentSerializer, PaymentCreateSerializer,
    PeriodSerializer,
)
from .services import (
    setup_business,
    create_sale, void_sale,
    create_purchase, void_purchase,
    create_expense, void_expense,
    create_payment, void_payment,
)
from . import reports


class SetupView(APIView):

    def get(self, request):
        config = BusinessConfig.get()
        if config is None:
            return Response({'detail': 'Business not configured yet.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(BusinessConfigSerializer(config).data)

    def post(self, request):
        serializer = SetupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        config = setup_business(**serializer.validated_data)
        return Response(BusinessConfigSerializer(config).data, status=status.HTTP_201_CREATED)

    def patch(self, request):
        config = BusinessConfig.get()
        if config is None:
            return Response({'detail': 'Business not configured yet.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = BusinessConfigPatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        for attr, value in serializer.validated_data.items():
            setattr(config, attr, value)
        config.save()
        return Response(BusinessConfigSerializer(config).data)


class SaleViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Sale.objects.select_related('product', 'entry').all()
    serializer_class = SaleSerializer

    def create(self, request):
        serializer = SaleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sale = create_sale(serializer.validated_data)
        return Response(SaleSerializer(sale).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def void(self, request, pk=None):
        sale = self.get_object()
        sale = void_sale(sale)
        return Response(SaleSerializer(sale).data)


class PurchaseViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Purchase.objects.select_related('product', 'entry').all()
    serializer_class = PurchaseSerializer

    def create(self, request):
        serializer = PurchaseCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        purchase = create_purchase(serializer.validated_data)
        return Response(PurchaseSerializer(purchase).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def void(self, request, pk=None):
        purchase = self.get_object()
        purchase = void_purchase(purchase)
        return Response(PurchaseSerializer(purchase).data)


class ExpenseViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Expense.objects.select_related('entry').all()
    serializer_class = ExpenseSerializer

    def create(self, request):
        serializer = ExpenseCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        expense = create_expense(serializer.validated_data)
        return Response(ExpenseSerializer(expense).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def void(self, request, pk=None):
        expense = self.get_object()
        expense = void_expense(expense)
        return Response(ExpenseSerializer(expense).data)


class PaymentViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Payment.objects.select_related('entry').all()
    serializer_class = PaymentSerializer

    def create(self, request):
        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = create_payment(serializer.validated_data)
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def void(self, request, pk=None):
        payment = self.get_object()
        payment = void_payment(payment)
        return Response(PaymentSerializer(payment).data)


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

class ReportSummaryView(APIView):

    def get(self, request):
        period_s = PeriodSerializer(data=request.query_params)
        period_s.is_valid(raise_exception=True)
        start  = period_s.validated_data['start']
        end    = period_s.validated_data['end']
        config = BusinessConfig.get()

        revenue  = reports.get_revenue(start, end)
        expenses = reports.get_expenses(start, end)

        return Response({
            'period':       {'start': str(start) if start else None, 'end': str(end) if end else None},
            'revenue':      revenue,
            'expenses':     expenses,
            'net_profit':   revenue - expenses,
            'cash_balance': reports.get_account_balance(config.cash_account       if config else None),
            'receivables':  reports.get_account_balance(config.receivable_account if config else None),
            'payables':     reports.get_credit_balance(config.payable_account     if config else None),
        })


class ReportProfitLossView(APIView):

    def get(self, request):
        period_s = PeriodSerializer(data=request.query_params)
        period_s.is_valid(raise_exception=True)
        start = period_s.validated_data['start']
        end   = period_s.validated_data['end']

        revenue_rows   = list(reports.get_revenue_breakdown(start, end))
        expenses_rows  = list(reports.get_expenses_breakdown(start, end))
        total_revenue  = sum((r['amount'] for r in revenue_rows),  start=0)
        total_expenses = sum((r['amount'] for r in expenses_rows), start=0)

        return Response({
            'period':         {'start': str(start) if start else None, 'end': str(end) if end else None},
            'revenue':        [{'account': r['account__name'], 'amount': r['amount']} for r in revenue_rows],
            'total_revenue':  total_revenue,
            'expenses':       [{'account': r['account__name'], 'amount': r['amount']} for r in expenses_rows],
            'total_expenses': total_expenses,
            'net_profit':     total_revenue - total_expenses,
        })


class ReportInventoryView(APIView):

    def get(self, request):
        return Response(reports.get_inventory_report())
