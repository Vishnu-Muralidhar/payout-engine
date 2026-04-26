# EXPLAINER

### 1. The Ledger
**Balance Update / Calculation:**
```python
# From backend/payouts/services.py
balance = MerchantBalance.objects.select_for_update().get(merchant_id=merchant_id)
if balance.available_balance < amount:
    raise InsufficientFunds("Insufficient available balance.")

balance.available_balance -= amount
balance.held_balance += amount
balance.save(update_fields=['available_balance', 'held_balance'])

LedgerEntry.objects.create(
    merchant_id=merchant_id, amount=amount, entry_type=LedgerEntryType.HOLD, payout_id=payout_id
)
```
**Why model it this way?**
Instead of dynamically calculating the balance on the fly using expensive `SUM(credits) - SUM(debits)` queries (which becomes a bottleneck at scale), we use a **CQRS / Event Sourcing** hybrid approach. We maintain a rolling `MerchantBalance` table for O(1) read/write lookups, and we insert an immutable `LedgerEntry` (the event) to maintain a strict, append-only financial audit log.

### 2. The Lock
**Code:**
```python
# From backend/payouts/services.py
balance = MerchantBalance.objects.select_for_update().get(merchant_id=merchant_id)
```
**Database Primitive:**
This relies on PostgreSQL's **Pessimistic Row-Level Locking** (`SELECT ... FOR UPDATE`). When Server A reaches this line, Postgres locks that specific row. If Server B tries to process a concurrent payout for the same merchant, Postgres halts Server B until Server A commits or rolls back its transaction. This guarantees that two concurrent \$100 payouts against a $150 balance will strictly process sequentially, safely rejecting the second one without overdrawing the account.

### 3. The Idempotency
**How it knows it has seen a key before:**
The frontend generates a unique UUID every time the user clicks the "Request Payout" button. This UUID is sent as the `Idempotency-Key` header in every API request. The backend attempts to look up an `IdempotencyRecord` by `(merchant, key)`. If it exists, it intercepts the request and instantly returns the saved HTTP response.

**What happens if the first request is in-flight when the second arrives?**
```python
class IdempotencyRecord(models.Model):
    # ...
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['merchant', 'key'], name='unique_idempotency_record')
        ]
```
If the first request is still processing inside its `transaction.atomic()` block, the `IdempotencyRecord` hasn't been committed yet. The second request won't find it in the initial `SELECT` check. However, when the second request reaches `IdempotencyRecord.objects.create(...)`, PostgreSQL will enforce the `UniqueConstraint` and throw an `IntegrityError`, successfully blocking the duplicate payout at the database level.

### 4. The State Machine
**The Check:**
In `models.py`, the `state` field is protected by `django-fsm`.
```python
state = FSMField(default=PayoutState.PENDING, choices=PayoutState.choices, protected=True)

@transition(field=state, source=PayoutState.PROCESSING, target=PayoutState.COMPLETED)
def mark_completed(self):
    pass
```
Because of the `@transition` decorator, `mark_completed()` explicitly requires the source state to be `PROCESSING`. If a payout is already in a `FAILED` state, attempting to call `payout.mark_completed()` will raise a `TransitionNotAllowed` exception, strictly blocking illegal state jumps.

### 5. The AI Audit
**The Bug:** The AI initially wrote code in the Celery worker that assigned the state string directly:
```python
# AI's original code
payout.state = PayoutState.PROCESSING
payout.save(update_fields=['state', 'updated_at'])
```
**What I caught:** Because the `state` field was initialized as an `FSMField(protected=True)`, Django-FSM blocks direct assignment. The AI's code threw an `AttributeError: Direct state modification is not allowed` inside the Celery worker. Because this exception was unhandled, the worker silently aborted the task, leaving the payout permanently stuck in `PENDING`.
**The Fix:** I replaced the direct assignments with the FSM transition methods to safely move the state machine forward:
```python
# Corrected code
payout.mark_processing()
payout.save(update_fields=['state', 'updated_at'])
```


