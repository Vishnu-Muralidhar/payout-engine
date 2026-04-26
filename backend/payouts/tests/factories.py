import factory
from factory.django import DjangoModelFactory
from payouts.models import Merchant, BankAccount, MerchantBalance

class MerchantFactory(DjangoModelFactory):
    class Meta:
        model = Merchant
    
    name = factory.Faker('company')

class BankAccountFactory(DjangoModelFactory):
    class Meta:
        model = BankAccount
    
    merchant = factory.SubFactory(MerchantFactory)
    account_number = factory.Faker('bban')
    routing_number = factory.Faker('aba')

class MerchantBalanceFactory(DjangoModelFactory):
    class Meta:
        model = MerchantBalance

    merchant = factory.SubFactory(MerchantFactory)
    available_balance = 0
    held_balance = 0
