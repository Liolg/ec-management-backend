from django.contrib import admin
from .models import Account, Entry, Line
from unfold.admin import ModelAdmin, TabularInline

@admin.register(Account)
class AccountAdmin(ModelAdmin):
    list_display = ('code', 'name', 'type')
    search_fields = ('code', 'name')

class EcAccountLineInline(TabularInline):
    model = Line
    extra = 0

@admin.register(Entry)
class EcAccountEntryAdmin(ModelAdmin):
    list_display = ('id', 'date', 'reference', 'voided')
    inlines = [EcAccountLineInline]

@admin.register(Line)
class EntryLineAdmin(ModelAdmin):
    list_display = ('id','entry', 'account', 'description', 'value', 'type')
