import pytest
from payouts.tests.factories import MerchantFactory

@pytest.fixture
def auth_client(client, monkeypatch):
    merchant = MerchantFactory()

    from payouts import views

    original_post = views.PayoutView.post

    def patched_post(self, request, *args, **kwargs):
        request.merchant = merchant
        return original_post(self, request, *args, **kwargs)

    monkeypatch.setattr(
        views.PayoutView,
        "post",
        patched_post
    )

    return client, merchant