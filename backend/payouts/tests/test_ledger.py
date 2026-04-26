import pytest
from payouts.models import PayoutState, LedgerEntryType, LedgerEntry
from payouts.services import LedgerService
from payouts.tests.factories import MerchantFactory, MerchantBalanceFactory
from django.db.models import Sum

pytestmark = pytest.mark.django_db

def test_ledger_invariants_hold_and_release():
    merchant = MerchantFactory()
    balance = MerchantBalanceFactory(merchant=merchant, available_balance=1000)

    # Apply Hold
    LedgerService.hold_funds(merchant.id, 200)
    
    balance.refresh_from_db()
    assert balance.available_balance == 800
    assert balance.held_balance == 200

    # Release Hold
    LedgerService.release_hold(merchant.id, 200)

    balance.refresh_from_db()
    assert balance.available_balance == 1000
    assert balance.held_balance == 0

    holds = LedgerEntry.objects.filter(entry_type=LedgerEntryType.HOLD).aggregate(Sum('amount'))['amount__sum'] or 0
    releases = LedgerEntry.objects.filter(entry_type=LedgerEntryType.HOLD_RELEASE).aggregate(Sum('amount'))['amount__sum'] or 0
    assert holds == releases

def test_ledger_invariants_commit():
    merchant = MerchantFactory()
    balance = MerchantBalanceFactory(merchant=merchant, available_balance=1000)

    # Apply Hold
    LedgerService.hold_funds(merchant.id, 500)
    
    # Commit Payout
    LedgerService.commit_payout(merchant.id, 500)

    balance.refresh_from_db()
    assert balance.available_balance == 500
    assert balance.held_balance == 0

    debits = LedgerEntry.objects.filter(entry_type=LedgerEntryType.PAYOUT_DEBIT).aggregate(Sum('amount'))['amount__sum'] or 0
    assert debits == 500
