from django.db import transaction
from django.db.models import F
from .models import Merchant, MerchantBalance, LedgerEntry, LedgerEntryType, Payout, PayoutState
from rest_framework.exceptions import ValidationError

class InsufficientFunds(ValidationError):
    pass

class LedgerService:
    @staticmethod
    def hold_funds(merchant_id, amount, payout_id=None):
        """
        Locks the balance row, verifies sufficient funds, deducts from available, adds to held,
        and creates a HOLD ledger entry.
        """
        with transaction.atomic():
            # Pessimistic write lock on the balance row
            balance = MerchantBalance.objects.select_for_update().get(merchant_id=merchant_id)
            
            if balance.available_balance < amount:
                raise InsufficientFunds("Insufficient available balance.")
            
            # Atomic update using F() expressions is safe, but since we locked it, we can just mutate
            balance.available_balance -= amount
            balance.held_balance += amount
            balance.save(update_fields=['available_balance', 'held_balance'])
            
            entry = LedgerEntry.objects.create(
                merchant_id=merchant_id,
                amount=amount,
                entry_type=LedgerEntryType.HOLD,
                payout_id=payout_id
            )
            return entry

    @staticmethod
    def release_hold(merchant_id, amount, payout_id=None):
        """
        Releases held funds back to available balance.
        """
        with transaction.atomic():
            balance = MerchantBalance.objects.select_for_update().get(merchant_id=merchant_id)
            
            balance.held_balance -= amount
            balance.available_balance += amount
            balance.save(update_fields=['available_balance', 'held_balance'])
            
            entry = LedgerEntry.objects.create(
                merchant_id=merchant_id,
                amount=amount,
                entry_type=LedgerEntryType.HOLD_RELEASE,
                payout_id=payout_id
            )
            return entry

    @staticmethod
    def commit_payout(merchant_id, amount, payout_id=None):
        """
        Deducts the amount from held_balance and creates a PAYOUT_DEBIT ledger entry.
        """
        with transaction.atomic():
            balance = MerchantBalance.objects.select_for_update().get(merchant_id=merchant_id)
            
            balance.held_balance -= amount
            balance.save(update_fields=['held_balance'])
            
            entry = LedgerEntry.objects.create(
                merchant_id=merchant_id,
                amount=amount,
                entry_type=LedgerEntryType.PAYOUT_DEBIT,
                payout_id=payout_id
            )
            return entry

class PayoutService:
    @staticmethod
    def create_payout(merchant_id, bank_account_id, amount_paise, idempotency_key):
        """
        Creates a payout safely.
        Assumes idempotency has already been checked at the API layer.
        """
        with transaction.atomic():
            # 1. Create payout
            payout = Payout.objects.create(
                merchant_id=merchant_id,
                bank_account_id=bank_account_id,
                amount=amount_paise,
                state=PayoutState.PENDING,
                idempotency_key=idempotency_key
            )
            
            # 2. Hold funds
            # This locks the balance and throws if insufficient funds
            LedgerService.hold_funds(merchant_id, amount_paise, payout.id)
            
            return payout
