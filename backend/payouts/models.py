import uuid
from django.db import models
from django.utils import timezone
from django_fsm import FSMField, transition

class Merchant(models.Model): 
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class BankAccount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, related_name='bank_accounts')
    account_number = models.CharField(max_length=50)
    routing_number = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.merchant.name} - {self.account_number}"

class MerchantBalance(models.Model): #Links this balance directly to exactly one Merchant.
    merchant = models.OneToOneField(Merchant, on_delete=models.CASCADE, primary_key=True, related_name='balance')
    available_balance = models.BigIntegerField(default=0, help_text="Available balance in paise")
    held_balance = models.BigIntegerField(default=0, help_text="Held balance in paise") #Money that is currently locked because a payout is processing.

    def __str__(self):
        return f"{self.merchant.name} Balance"

class LedgerEntryType(models.TextChoices):
    CREDIT = 'CREDIT', 'Credit'
    HOLD = 'HOLD', 'Hold'
    HOLD_RELEASE = 'HOLD_RELEASE', 'Hold Release'
    PAYOUT_DEBIT = 'PAYOUT_DEBIT', 'Payout Debit'

class LedgerEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, related_name='ledger_entries')
    amount = models.BigIntegerField(help_text="Amount in paise")
    entry_type = models.CharField(max_length=20, choices=LedgerEntryType.choices)
    payout_id = models.UUIDField(null=True, blank=True, help_text="Reference to the related payout, if any")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at'] # ORDER BY created_at DESC

    def __str__(self):
        return f"{self.merchant.name} - {self.entry_type} - {self.amount}"

class PayoutState(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    PROCESSING = 'PROCESSING', 'Processing'
    COMPLETED = 'COMPLETED', 'Completed'
    FAILED = 'FAILED', 'Failed'

class Payout(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, related_name='payouts')
    bank_account = models.ForeignKey(BankAccount, on_delete=models.PROTECT, related_name='payouts')
    amount = models.BigIntegerField(help_text="Amount in paise")
    
    state = FSMField(default=PayoutState.PENDING, choices=PayoutState.choices, protected=True)
    
    idempotency_key = models.UUIDField()
    retry_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['merchant', 'idempotency_key'], name='unique_merchant_idempotency_key')
        ] #UNIQUE(merchant, idempotency_key) 
        ordering = ['-created_at']

    @transition(field=state, source=PayoutState.PENDING, target=PayoutState.PROCESSING)
    def mark_processing(self):
        pass

    @transition(field=state, source=PayoutState.PROCESSING, target=PayoutState.COMPLETED)
    def mark_completed(self):
        pass

    @transition(field=state, source=PayoutState.PROCESSING, target=PayoutState.FAILED)
    def mark_failed(self):
        pass

    def __str__(self):
        return f"Payout {self.id} - {self.state}"

class IdempotencyRecord(models.Model):
    key = models.UUIDField(primary_key=True)
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE)
    response_status = models.IntegerField()
    response_body = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['merchant', 'key'], name='unique_idempotency_record')
        ]

    def __str__(self):
        return f"Idempotency {self.key} for {self.merchant.name}"
