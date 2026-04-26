import os
import django
from django.db.models import Sum

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from payouts.models import Merchant, MerchantBalance, LedgerEntry, LedgerEntryType

def run_reconciliation():
    merchants = Merchant.objects.all()
    
    for merchant in merchants:
        print(f"Reconciling {merchant.name} ({merchant.id})...")
        
        balance = MerchantBalance.objects.get(merchant=merchant)
        
        # Calculate derived available balance
        credits = LedgerEntry.objects.filter(merchant=merchant, entry_type=LedgerEntryType.CREDIT).aggregate(Sum('amount'))['amount__sum'] or 0
        payouts = LedgerEntry.objects.filter(merchant=merchant, entry_type=LedgerEntryType.PAYOUT_DEBIT).aggregate(Sum('amount'))['amount__sum'] or 0
        holds = LedgerEntry.objects.filter(merchant=merchant, entry_type=LedgerEntryType.HOLD).aggregate(Sum('amount'))['amount__sum'] or 0
        hold_releases = LedgerEntry.objects.filter(merchant=merchant, entry_type=LedgerEntryType.HOLD_RELEASE).aggregate(Sum('amount'))['amount__sum'] or 0
        
        derived_available = credits - payouts - (holds - hold_releases)
        derived_held = holds - hold_releases
        
        is_available_valid = derived_available == balance.available_balance
        is_held_valid = derived_held == balance.held_balance
        
        print(f"  Available: {balance.available_balance} | Derived: {derived_available} | Valid: {is_available_valid}")
        print(f"  Held:      {balance.held_balance} | Derived: {derived_held} | Valid: {is_held_valid}")
        
        if not (is_available_valid and is_held_valid):
            print(f"  [ERROR] Invariant mismatch for merchant {merchant.name}!")
        else:
            print("  [OK] Invariants match.")
            
if __name__ == '__main__':
    run_reconciliation()
