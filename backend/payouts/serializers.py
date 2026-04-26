from rest_framework import serializers
from .models import Payout, MerchantBalance, LedgerEntry, BankAccount, PayoutState

class PayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payout
        fields = ['id', 'amount', 'state', 'bank_account', 'created_at', 'updated_at']
        read_only_fields = ['id', 'state', 'created_at', 'updated_at']

class PayoutCreateSerializer(serializers.Serializer):
    amount_paise = serializers.IntegerField(min_value=1)
    bank_account_id = serializers.UUIDField()

    def validate_bank_account_id(self, value):
        merchant = self.context['request'].merchant
        if not BankAccount.objects.filter(id=value, merchant=merchant).exists():
            raise serializers.ValidationError("Invalid bank account ID for this merchant.")
        return value

class BalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = MerchantBalance
        fields = ['available_balance', 'held_balance']

class LedgerEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LedgerEntry
        fields = ['id', 'amount', 'entry_type', 'created_at']
