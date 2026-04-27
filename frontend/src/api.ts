import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const MERCHANT_ID = '1c01fc52-6303-40b8-a161-f38f4e7f2647';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'X-Merchant-Id': MERCHANT_ID,
  },
});

export const getBalance = async () => {
  const { data } = await apiClient.get('/balance/');
  return data;
};

export const getPayouts = async () => {
  const { data } = await apiClient.get('/payouts/');
  return data;
};

// ✅ FIX: idempotency key is now passed from caller
export const createPayout = async (
  amountPaise: number,
  bankAccountId: string,
  idempotencyKey: string
) => {
  const { data } = await apiClient.post(
    '/payouts/',
    {
      amount_paise: amountPaise,
      bank_account_id: bankAccountId,
    },
    {
      headers: {
        'Idempotency-Key': idempotencyKey,
      },
    }
  );
  return data;
};
