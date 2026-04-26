import pytest
import uuid
from django.urls import reverse
from payouts.models import Payout, IdempotencyRecord
from payouts.tests.factories import BankAccountFactory, MerchantBalanceFactory

pytestmark = pytest.mark.django_db

def test_idempotent_payout_creation(auth_client):
    client, merchant = auth_client
    bank_account = BankAccountFactory(merchant=merchant)
    MerchantBalanceFactory(merchant=merchant, available_balance=1000)

    url = reverse('payout-list-create')
    data = {
        'amount_paise': 500,
        'bank_account_id': str(bank_account.id)
    }
    idemp_key = str(uuid.uuid4())
    headers = {'HTTP_IDEMPOTENCY_KEY': idemp_key}

    # First request
    response1 = client.post(url, data, format='json', **headers)
    print(response1.status_code)
    print(response1.content)
    print(response1.json())
    assert response1.status_code == 201
    
    # Second request with the same idempotency key
    response2 = client.post(url, data, format='json', **headers)
    assert response2.status_code == 201

    # Assertions
    assert response1.json() == response2.json()
    assert Payout.objects.count() == 1
    assert IdempotencyRecord.objects.count() == 1
    
def test_missing_idempotency_key(auth_client):
    client, merchant = auth_client
    bank_account = BankAccountFactory(merchant=merchant)
    
    url = reverse('payout-list-create')
    data = {'amount_paise': 500, 'bank_account_id': str(bank_account.id)}
    
    response = client.post(url, data, format='json')
    assert response.status_code == 400
    assert "Idempotency-Key header is required" in response.json()['error']
