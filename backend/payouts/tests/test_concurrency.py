import pytest
import threading
import uuid
from django.db import connection
from django.test import TransactionTestCase
from payouts.models import Merchant, MerchantBalance, BankAccount, Payout, LedgerEntry, LedgerEntryType
from payouts.services import PayoutService, InsufficientFunds
from payouts.tests.factories import MerchantFactory, BankAccountFactory, MerchantBalanceFactory

class TestConcurrency(TransactionTestCase):
    """
    We use TransactionTestCase because normal TestCase wraps everything in a transaction,
    which deadlocks when multiple threads try to run concurrently against it.
    """
    
    def setUp(self):
        self.merchant = MerchantFactory()
        self.bank_account = BankAccountFactory(merchant=self.merchant)
        self.balance = MerchantBalanceFactory(merchant=self.merchant, available_balance=100)

    def test_concurrent_payout_requests(self):
        """
        Scenario: Merchant has 100 rupees.
        Two simultaneous 60 rupee payout requests.
        Exactly one succeeds. One must fail cleanly.
        """
        success_count = 0
        failure_count = 0
        exceptions = []

        def make_payout_request(idemp_key):
            nonlocal success_count, failure_count
            try:
                # We need a new database connection per thread
                connection.close()
                PayoutService.create_payout(
                    merchant_id=self.merchant.id,
                    bank_account_id=self.bank_account.id,
                    amount_paise=60,
                    idempotency_key=idemp_key
                )
                success_count += 1
            except InsufficientFunds:
                failure_count += 1
            except Exception as e:
                exceptions.append(e)

        # Create two threads to fire simultaneously
        t1 = threading.Thread(target=make_payout_request, args=(uuid.uuid4(),))
        t2 = threading.Thread(target=make_payout_request, args=(uuid.uuid4(),))

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        # Assertions
        assert not exceptions, f"Unexpected exceptions occurred: {exceptions}"
        assert success_count == 1, "Exactly one payout should succeed"
        assert failure_count == 1, "Exactly one payout should fail due to insufficient funds"

        # Verify database invariants
        self.balance.refresh_from_db()
        assert self.balance.available_balance == 40
        assert self.balance.held_balance == 60

        assert Payout.objects.count() == 1
        payout = Payout.objects.first()
        assert payout.amount == 60

        assert LedgerEntry.objects.count() == 1
        entry = LedgerEntry.objects.first()
        assert entry.amount == 60
        assert entry.entry_type == LedgerEntryType.HOLD
        assert entry.payout_id == payout.id
