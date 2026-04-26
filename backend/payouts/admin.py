from django.contrib import admin
from .models import Merchant, BankAccount, MerchantBalance, LedgerEntry, Payout, IdempotencyRecord

@admin.register(Merchant)
class MerchantAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at')

@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'merchant', 'account_number')
    list_filter = ('merchant',)

@admin.register(MerchantBalance)
class MerchantBalanceAdmin(admin.ModelAdmin):
    list_display = ('merchant', 'available_balance', 'held_balance')
    readonly_fields = ('merchant',)

@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ('id', 'merchant', 'entry_type', 'amount', 'created_at')
    list_filter = ('merchant', 'entry_type')
    readonly_fields = ('id', 'created_at')

@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ('id', 'merchant', 'bank_account', 'amount', 'state', 'created_at', 'updated_at')
    list_filter = ('merchant', 'state')
    readonly_fields = ('id', 'created_at', 'updated_at')

@admin.register(IdempotencyRecord)
class IdempotencyRecordAdmin(admin.ModelAdmin):
    list_display = ('key', 'merchant', 'response_status', 'created_at')
    list_filter = ('merchant',)
