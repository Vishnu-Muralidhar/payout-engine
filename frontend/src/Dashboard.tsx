import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { CreditCard, Activity, CheckCircle, Clock, XCircle, AlertCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import clsx from 'clsx';
import { getBalance, getPayouts, createPayout } from './api';

/* ---------------- MOCK DATA ---------------- */

const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

const mockBalance = {
  available_balance: 97800, // ₹978
  held_balance: 0,
};

const mockPayouts = [
  {
    id: '1',
    amount: 200,
    state: 'COMPLETED',
    created_at: new Date().toISOString(),
  },
  {
    id: '2',
    amount: 1000,
    state: 'COMPLETED',
    created_at: new Date(Date.now() - 10000000).toISOString(),
  },
  {
    id: '3',
    amount: 200,
    state: 'FAILED',
    created_at: new Date(Date.now() - 20000000).toISOString(),
  },
  {
    id: '4',
    amount: 500,
    state: 'COMPLETED',
    created_at: new Date(Date.now() - 30000000).toISOString(),
  },
];

/* ---------------- HELPERS ---------------- */

const formatCurrency = (paise: number) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
  }).format(paise / 100);
};

export default function Dashboard() {
  const queryClient = useQueryClient();
  const [amountInput, setAmountInput] = useState('');

  const testBankAccountId = '00000000-0000-0000-0000-000000000000';

  /* ---------------- QUERIES ---------------- */

  const {
    data: balance,
    isLoading: balanceLoading,
    isError: balanceError,
  } = useQuery({
    queryKey: ['balance'],
    queryFn: getBalance,
    refetchInterval: 3000,
    retry: false,
  });

  const {
    data: payouts,
    isLoading: payoutsLoading,
  } = useQuery({
    queryKey: ['payouts'],
    queryFn: getPayouts,
    refetchInterval: 3000,
    retry: false,
  });

  /* ---------------- FALLBACK LOGIC ---------------- */

  const effectiveBalance = USE_MOCK || balanceError || !balance
    ? mockBalance
    : balance;

  const effectivePayouts = USE_MOCK || !payouts || payouts.length === 0
    ? mockPayouts
    : payouts;

  /* ---------------- MUTATION ---------------- */

  const payoutMutation = useMutation({
    mutationFn: (amountPaise: number) =>
      createPayout(amountPaise, testBankAccountId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['balance'] });
      queryClient.invalidateQueries({ queryKey: ['payouts'] });
      setAmountInput('');
    },
  });

  const handlePayoutSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const amountRs = parseFloat(amountInput);
    if (isNaN(amountRs) || amountRs <= 0) return;

    // MOCK MODE: don't call backend
    if (USE_MOCK) {
      console.log('Mock payout:', amountRs);
      setAmountInput('');
      return;
    }

    payoutMutation.mutate(amountRs * 100);
  };

  /* ---------------- CALCULATIONS ---------------- */

  const totalBalance =
    (effectiveBalance.available_balance || 0) +
    (effectiveBalance.held_balance || 0);

  const heldPercentage =
    totalBalance > 0
      ? ((effectiveBalance.held_balance || 0) / totalBalance) * 100
      : 0;

  const availablePercentage =
    totalBalance > 0
      ? ((effectiveBalance.available_balance || 0) / totalBalance) * 100
      : 0;

  /* ---------------- UI ---------------- */

  return (
    <div className="min-h-screen p-8 max-w-6xl mx-auto space-y-12">
      <header className="flex items-center justify-between mb-12">
        <div>
          <h1 className="text-4xl font-extrabold text-white tracking-[0.2em] uppercase">
            Payto Merchant Payment Dashboard
          </h1>
          <p className="text-[#888888] mt-2 tracking-widest text-sm uppercase">
            Payout Engine
          </p>
        </div>
      </header>

      {/* Balance Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Available */}
        <div className="glass-panel p-8 relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-opacity">
            <CreditCard size={80} />
          </div>

          <h3 className="text-[#737373] tracking-[0.1em] text-sm uppercase font-semibold mb-4">
            Available Balance
          </h3>

          {balanceLoading && !USE_MOCK ? (
            <div className="h-10 w-32 bg-[#111] rounded animate-pulse" />
          ) : (
            <>
              <div className="text-5xl font-light text-white tracking-wider">
                {formatCurrency(effectiveBalance.available_balance || 0)}
              </div>

              <div className="mt-6 h-2 w-full bg-[#111] rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${availablePercentage}%` }}
                  transition={{ duration: 1 }}
                  className="h-full bg-white rounded-full"
                />
              </div>
            </>
          )}
        </div>

        {/* Pending */}
        <div className="glass-panel p-8 relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-opacity">
            <Activity size={80} />
          </div>

          <h3 className="text-[#737373] tracking-[0.1em] text-sm uppercase font-semibold mb-4">
            Pending Execution
          </h3>

          {balanceLoading && !USE_MOCK ? (
            <div className="h-10 w-32 bg-[#111] rounded animate-pulse" />
          ) : (
            <>
              <div className="text-5xl font-light text-white tracking-wider">
                {formatCurrency(effectiveBalance.held_balance || 0)}
              </div>

              <div className="mt-6 h-2 w-full bg-[#111] rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${heldPercentage}%` }}
                  transition={{ duration: 1 }}
                  className="h-full bg-white mercury-liquid rounded-full"
                />
              </div>
            </>
          )}
        </div>
      </div>

      {/* Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">

        {/* Form */}
        <div className="lg:col-span-1">
          <div className="glass-panel p-8">
            <h2 className="text-sm text-[#888888] tracking-[0.15em] uppercase mb-6">
              Execute Order
            </h2>

            <form onSubmit={handlePayoutSubmit} className="space-y-6">
              <input
                type="number"
                value={amountInput}
                onChange={(e) => setAmountInput(e.target.value)}
                placeholder="₹ 0.00"
                className="w-full p-3 bg-[#0a0a0a] text-white rounded-xl"
              />

              <button className="w-full bg-white text-black py-3 rounded-xl">
                Withdraw
              </button>
            </form>
          </div>
        </div>

        {/* History */}
        <div className="lg:col-span-2">
          <div className="glass-panel p-8">
            <h2 className="text-sm text-[#888888] tracking-[0.15em] uppercase mb-6">
              Execution Log
            </h2>

            <div className="space-y-4">
              <AnimatePresence>
                {effectivePayouts.map((payout: any) => (
                  <motion.div
                    key={payout.id}
                    layout
                    className="flex justify-between p-4 bg-[#0c0c0c] rounded-xl"
                  >
                    <div>
                      {formatCurrency(payout.amount)}
                    </div>
                    <PayoutStatusBadge status={payout.state} />
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}

/* ---------------- STATUS BADGE ---------------- */

function PayoutStatusBadge({ status }: { status: string }) {
  switch (status) {
    case 'COMPLETED':
      return <span className="text-green-400">Completed</span>;
    case 'FAILED':
      return <span className="text-red-400">Failed</span>;
    case 'PROCESSING':
      return <span className="text-yellow-400">Processing</span>;
    default:
      return <span className="text-gray-400">{status}</span>;
  }
}
