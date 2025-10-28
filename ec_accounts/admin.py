from django.contrib import admin
from .models import Account, Entry, Line

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'type')
    search_fields = ('code', 'name')

class EcAccountLineInline(admin.TabularInline):
    model = Line
    extra = 0

@admin.register(Entry)
class EcAccountEntryAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'reference', 'voided')
    inlines = [EcAccountLineInline]

@admin.register(Line)
class EntryLineAdmin(admin.ModelAdmin):
    list_display = ('entry', 'account', 'description', 'debit', 'credit')
