from .models import Merchant

class MerchantAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        merchant_id = request.headers.get("X-Merchant-Id")

        if merchant_id:
            try:
                request.merchant = Merchant.objects.get(id=merchant_id)
            except Merchant.DoesNotExist:
                request.merchant = None
        else:
            request.merchant = None

        return self.get_response(request)
