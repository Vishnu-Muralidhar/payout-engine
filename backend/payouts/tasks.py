import time
import random
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from .models import Payout, PayoutState
from .services import LedgerService

@shared_task(bind=True, max_retries=3) #to mark the function as a celery background task and for retry mechanism
def process_payout_task(self, payout_id_str):
    """
    Simulates external settlement logic for a payout.
    Note on concurrency task:
    skip_locked=True: This is a brilliant concurrency trick. If you have 10 worker servers running, 
    and two workers try to grab the exact same task, the first one locks it. 
    The second worker sees it's locked and simply skips it and returns, preventing duplicate work.
    """
    with transaction.atomic():
        # Fetch the payout safely using SKIP LOCKED
        payout = Payout.objects.select_for_update(skip_locked=True).filter(
            id=payout_id_str, state=PayoutState.PENDING
        ).first()

        if not payout:
            # If not found or locked by another worker, just return
            return

        # Mark as processing
        payout.mark_processing()
        payout.save(update_fields=['state', 'updated_at'])

    # Simulate network latency to payment gateway (not inside transaction)
    time.sleep(random.uniform(0.5, 2.0))

    # Simulate outcome: 70% success, 20% fail, 10% stuck (exception, simulating timeout)
    outcome = random.random()
    if outcome < 0.10:
        # Simulate stuck processing (will be picked up by sweeper)
        raise Exception("Simulated timeout/stuck connection to payment gateway")

    with transaction.atomic():
        # Re-fetch for final state transition
        payout = Payout.objects.select_for_update().get(id=payout_id_str)
        
        if payout.state != PayoutState.PROCESSING:
            return

        if outcome < 0.80: # 70% success (0.1 to 0.8)
            # Success
            LedgerService.commit_payout(payout.merchant_id, payout.amount, payout.id)
            payout.mark_completed()
        else: # 20% fail (0.8 to 1.0)
            # Fail - refund
            LedgerService.release_hold(payout.merchant_id, payout.amount, payout.id)
            payout.mark_failed()

        payout.save(update_fields=['state', 'updated_at'])

"""
The sweep_stuck_payouts_task is never called using .delay() anywhere in your code. Instead,
we explicitly handed control of it to the Beat scheduler inside settings.py
"""
@shared_task
def sweep_stuck_payouts_task():
    """
    Finds Payouts stuck in PROCESSING for >30 seconds.
    Retries them up to 3 times, then marks as FAILED and refunds.
    """
    cutoff_time = timezone.now() - timedelta(seconds=30)
    
    stuck_payouts = Payout.objects.filter(
        state=PayoutState.PROCESSING,
        updated_at__lt=cutoff_time
    )

    for payout in stuck_payouts:
        with transaction.atomic():
            p = Payout.objects.select_for_update(skip_locked=True).filter(id=payout.id).first()
            if not p:
                continue
            
            if p.retry_count < 3:
                p.retry_count += 1
                p.save(update_fields=['retry_count', 'updated_at'])
                # Enqueue a retry task
                process_payout_task.apply_async(args=[str(p.id)], countdown=30 * p.retry_count)
            else:
                # Max retries exceeded, force failure
                LedgerService.release_hold(p.merchant_id, p.amount, p.id)
                p.mark_failed()
                p.save(update_fields=['state', 'updated_at'])
