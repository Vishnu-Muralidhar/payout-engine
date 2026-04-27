import uuid
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from payouts.models import Merchant, Ledger, Payout


class Command(BaseCommand):
    help = "Seed demo data for payout system"

    MERCHANT_ID = uuid.UUID("1c01fc52-6303-40b8-a161-f38f4e7f2647")

    def handle(self, *args, **kwargs):
        with transaction.atomic():
            self.stdout.write("🌱 Seeding demo data...")

            merchant = self.create_merchant()
            self.create_or_update_ledger(merchant)
            self.create_payouts(merchant)

            self.stdout.write(self.style.SUCCESS("✅ Seed data created successfully!"))

    # ---------------------------
    # Merchant
    # ---------------------------
    def create_merchant(self):
        merchant, created = Merchant.objects.get_or_create(
            id=self.MERCHANT_ID,
            defaults={
                "name": "Demo Merchant",
            },
        )

        if created:
            self.stdout.write("✔ Created merchant")
        else:
            self.stdout.write("✔ Merchant already exists")

        return merchant

    # ---------------------------
    # Ledger
    # ---------------------------
    def create_or_update_ledger(self, merchant):
        ledger, _ = Ledger.objects.update_or_create(
            merchant=merchant,
            defaults={
                "available_balance": 100_000,  # ₹1000
                "held_balance": 20_000,        # ₹200 pending
            },
        )

        self.stdout.write("✔ Ledger initialized")

        return ledger

    # ---------------------------
    # Payouts
    # ---------------------------
    def create_payouts(self, merchant):
        # Prevent duplicate seeding
        if Payout.objects.filter(merchant=merchant).exists():
            self.stdout.write("✔ Payouts already exist, skipping...")
            return

        now = timezone.now()

        payouts_data = [
            {
                "amount": 10_000,
                "state": "COMPLETED",
                "created_at": now - timezone.timedelta(minutes=30),
            },
            {
                "amount": 20_000,
                "state": "PROCESSING",
                "created_at": now - timezone.timedelta(minutes=10),
            },
            {
                "amount": 5_000,
                "state": "FAILED",
                "created_at": now - timezone.timedelta(minutes=5),
            },
            {
                "amount": 15_000,
                "state": "PENDING",
                "created_at": now - timezone.timedelta(minutes=1),
            },
        ]

        payout_objects = []

        for data in payouts_data:
            payout_objects.append(
                Payout(
                    merchant=merchant,
                    amount=data["amount"],
                    state=data["state"],
                    created_at=data["created_at"],
                    idempotency_key=str(uuid.uuid4()),  # realistic
                )
            )

        Payout.objects.bulk_create(payout_objects)

        self.stdout.write("✔ Sample payouts created")
