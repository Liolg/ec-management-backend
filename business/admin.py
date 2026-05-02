from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import BusinessConfig, Sale, Purchase, Expense, Payment


@admin.register(BusinessConfig)
class BusinessConfigAdmin(ModelAdmin):
    list_display   = ['company_name', 'currency']
    readonly_fields = [
        'cash_account', 'receivable_account', 'payable_account',
        'revenue_account', 'cogs_account', 'inventory_account', 'expense_account',
    ]


@admin.register(Sale)
class SaleAdmin(ModelAdmin):
    list_display  = ['id', 'product', 'qty', 'total_amount', 'date', 'payment_method', 'status']
    list_filter   = ['status', 'payment_method']
    readonly_fields = ['total_amount', 'entry', 'created_at']


@admin.register(Purchase)
class PurchaseAdmin(ModelAdmin):
    list_display  = ['id', 'product', 'qty', 'total_amount', 'date', 'payment_method', 'status']
    list_filter   = ['status', 'payment_method']
    readonly_fields = ['total_amount', 'entry', 'created_at']


@admin.register(Expense)
class ExpenseAdmin(ModelAdmin):
    list_display  = ['id', 'description', 'category', 'amount', 'date', 'payment_method', 'status']
    list_filter   = ['status', 'category', 'payment_method']
    readonly_fields = ['entry', 'created_at']


@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display  = ['id', 'direction', 'amount', 'date', 'counterparty_name', 'status']
    list_filter   = ['status', 'direction']
    readonly_fields = ['entry', 'created_at']
