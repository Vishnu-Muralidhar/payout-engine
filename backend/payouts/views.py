import json
from rest_framework import status, views
from rest_framework.response import Response
from django.db import transaction
from .models import Merchant, IdempotencyRecord, Payout, MerchantBalance
from .serializers import PayoutCreateSerializer, PayoutSerializer, BalanceSerializer
from .services import PayoutService, InsufficientFunds
from .tasks import process_payout_task

class PayoutView(views.APIView):
    def get(self, request):
        merchant = request.merchant
        # print("merchant------------------: ", merchant)
        if not merchant:
            return Response(
                {"error": "Merchant not found"},
                status=400
            )
        payouts = Payout.objects.filter(merchant=merchant).order_by('-created_at')[:50]
        return Response(PayoutSerializer(payouts, many=True).data)

    def post(self, request):
        print(request.headers)
        idempotency_key = request.headers.get("Idempotency-Key")
        print("idempotency key: ", idempotency_key)
        if not idempotency_key:
            print("here..")
            return Response(
                {"error": "Idempotency-Key header is required"},
                status=400
            )

        merchant = request.merchant
        print("merchant------------------: ", merchant)
        if not merchant:
            return Response(
                {"error": "Merchant not found"},
                status=400
            )

        with transaction.atomic(): #psql select_for_update() acquires a row-level lock
            record = (
                IdempotencyRecord.objects
                .select_for_update()
                .filter(merchant=merchant, key=idempotency_key)
                .first()
            )

            if record:
                return Response(
                    record.response_body,
                    status=record.response_status
                )

            serializer = PayoutCreateSerializer(
                data=request.data,
                context={"request": request}
            )
            if not serializer.is_valid():
                print("serializer errors:", serializer.errors)
                return Response(serializer.errors, status=400)

            payout = PayoutService.create_payout(
                merchant_id=merchant.id,
                bank_account_id=serializer.validated_data["bank_account_id"],
                amount_paise=serializer.validated_data["amount_paise"],
                idempotency_key=idempotency_key
            )

            response_body = json.loads(
                json.dumps(
                    PayoutSerializer(payout).data,
                    default=str
                )
            )

            IdempotencyRecord.objects.create(
                merchant=merchant,
                key=idempotency_key,
                response_status=201,
                response_body=response_body
            )

        process_payout_task.delay(str(payout.id)) #Async call to Celery task (fire and forget)

        return Response(response_body, status=201)



        
class BalanceView(views.APIView):
    def get(self, request):
        # Example: Set merchant from the authenticated user
        merchant = getattr(request, 'merchant', None)
        if not merchant:
            return Response({"error": "Merchant not found"}, status=400)

        balance = MerchantBalance.objects.get(merchant=merchant)
        return Response(BalanceSerializer(balance).data)
