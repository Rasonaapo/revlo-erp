from django.contrib import admin
from .models import *
# Register your models here


@admin.register(AccountCategory)
class AccountCategoryAdmin(admin.ModelAdmin):
    list_display = ('category_type', 'category_detail', )

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('account_name', 'account_number', 'account_category', 'balance', 'parent_account', 'bank', 'active', )

@admin.register(FinancialYear)
class FinancialYearAdmin(admin.ModelAdmin):
    list_display = ('start_date', 'end_date', 'status')
    search_fields = ('start_date', 'end_date')
    list_filter = ('status',)

@admin.register(TransactionCategory)
class TransactionCategoryAdmin(admin.ModelAdmin):
    list_display = ('type', 'detail', 'level')
    search_fields = ('type', 'detail')
    list_filter = ('level',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('date', 'description', 'amount', 'category', 'account', 'status', 'reference', 'cheque_number', 'bank', 'payroll', 'loan', 'sale', 'purchase_order', 'financial_year', )
    search_fields = ('category', 'description', 'reference')
    list_filter = ('date', 'category', 'status', 'category')

@admin.register(Ledger)
class LedgerAdmin(admin.ModelAdmin):
    list_display = ('account', 'transaction', 'amount', 'entry')
    search_fields = ('account', 'transaction')
    list_filter = ('account', 'transaction')