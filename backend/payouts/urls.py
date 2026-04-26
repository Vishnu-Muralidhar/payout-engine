from django.urls import path
from .views import PayoutView, BalanceView

urlpatterns = [
    path('payouts/', PayoutView.as_view(), name='payout-list-create'),
    path('balance/', BalanceView.as_view(), name='balance'),
]
