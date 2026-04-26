import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { CreditCard, Activity, CheckCircle, Clock, XCircle, AlertCircle } from 'lucide-react';
import clsx from 'clsx';
import { getBalance, getPayouts, createPayout } from './api';

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
  
  // Use a hardcoded test bank account ID for the MVP since we didn't build a bank account API
  const testBankAccountId = '00000000-0000-0000-0000-000000000000';

  const { data: balance, isLoading: balanceLoading, isError: balanceError } = useQuery({
    queryKey: ['balance'],
    queryFn: getBalance,
    refetchInterval: 3000,
  });

  const { data: payouts, isLoading: payoutsLoading } = useQuery({
    queryKey: ['payouts'],
    queryFn: getPayouts,
    refetchInterval: 3000,
  });

  const payoutMutation = useMutation({
    mutationFn: (amountPaise: number) => createPayout(amountPaise, testBankAccountId),
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
    payoutMutation.mutate(amountRs * 100);
  };

  return (
    <div className="min-h-screen p-8 max-w-6xl mx-auto space-y-8">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-400">
            Playto Payout Engine
          </h1>
          <p className="text-payto-muted mt-1">Merchant Dashboard</p>
        </div>
      </header>

      {/* Balance Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass-panel p-6 relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <CreditCard size={64} />
          </div>
          <h3 className="text-payto-muted font-medium mb-2">Available Balance</h3>
          {balanceLoading ? (
            <div className="h-10 w-32 bg-neutral-700 rounded animate-pulse" />
          ) : balanceError ? (
            <div className="text-red-400 flex items-center"><AlertCircle className="mr-2" /> Error loading</div>
          ) : (
            <div className="text-4xl font-bold text-white tracking-tight">
              {formatCurrency(balance?.available_balance || 0)}
            </div>
          )}
        </div>

        <div className="glass-panel p-6 relative overflow-hidden group border-orange-500/20">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <Activity size={64} />
          </div>
          <h3 className="text-orange-200/70 font-medium mb-2">Held for Processing</h3>
          {balanceLoading ? (
            <div className="h-10 w-32 bg-neutral-700 rounded animate-pulse" />
          ) : (
            <div className="text-4xl font-bold text-orange-400 tracking-tight">
              {formatCurrency(balance?.held_balance || 0)}
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Payout Request Form */}
        <div className="lg:col-span-1 space-y-6">
          <div className="glass-panel p-6">
            <h2 className="text-xl font-semibold mb-4">Request Payout</h2>
            <form onSubmit={handlePayoutSubmit} className="space-y-4">
              <div>
                <label className="block text-sm text-payto-muted mb-1">Amount (INR)</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">₹</span>
                  <input
                    type="number"
                    step="0.01"
                    min="1"
                    required
                    value={amountInput}
                    onChange={(e) => setAmountInput(e.target.value)}
                    className="w-full bg-neutral-800 border border-neutral-700 rounded-lg py-2 pl-8 pr-4 text-white focus:outline-none focus:ring-2 focus:ring-payto-accent transition-all"
                    placeholder="0.00"
                    disabled={payoutMutation.isPending}
                  />
                </div>
              </div>
              <button
                type="submit"
                disabled={payoutMutation.isPending}
                className="w-full bg-payto-accent hover:bg-payto-accent-hover text-black font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center disabled:opacity-50"
              >
                {payoutMutation.isPending ? 'Processing...' : 'Withdraw Funds'}
              </button>
              {payoutMutation.isError && (
                <p className="text-sm text-red-400 mt-2">
                  {(payoutMutation.error as any)?.response?.data?.error || 'Failed to request payout'}
                </p>
              )}
            </form>
          </div>
        </div>

        {/* Payout History */}
        <div className="lg:col-span-2">
          <div className="glass-panel p-6 min-h-[400px]">
            <h2 className="text-xl font-semibold mb-4">Recent Payouts</h2>
            
            {payoutsLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map(i => (
                  <div key={i} className="h-16 bg-neutral-800 rounded-lg animate-pulse" />
                ))}
              </div>
            ) : payouts?.length === 0 ? (
              <div className="text-center text-payto-muted py-12">
                No payouts found
              </div>
            ) : (
              <div className="space-y-3">
                {payouts?.map((payout: any) => (
                  <div key={payout.id} className="bg-neutral-800/50 rounded-lg p-4 flex items-center justify-between border border-neutral-700/50 hover:bg-neutral-800 transition-colors">
                    <div>
                      <div className="text-lg font-medium">{formatCurrency(payout.amount)}</div>
                      <div className="text-xs text-payto-muted mt-1 font-mono">
                        {new Date(payout.created_at).toLocaleString()}
                      </div>
                    </div>
                    <div>
                      <PayoutStatusBadge status={payout.state} />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function PayoutStatusBadge({ status }: { status: string }) {
  const baseClasses = "px-3 py-1 rounded-full text-xs font-medium flex items-center gap-1.5";
  
  switch (status) {
    case 'COMPLETED':
      return <span className={clsx(baseClasses, "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20")}><CheckCircle size={14}/> Completed</span>;
    case 'PROCESSING':
      return <span className={clsx(baseClasses, "bg-blue-500/10 text-blue-400 border border-blue-500/20")}><Activity size={14} className="animate-pulse"/> Processing</span>;
    case 'PENDING':
      return <span className={clsx(baseClasses, "bg-orange-500/10 text-orange-400 border border-orange-500/20")}><Clock size={14}/> Pending</span>;
    case 'FAILED':
      return <span className={clsx(baseClasses, "bg-red-500/10 text-red-400 border border-red-500/20")}><XCircle size={14}/> Failed</span>;
    default:
      return <span className={clsx(baseClasses, "bg-gray-500/10 text-gray-400")}>{status}</span>;
  }
}
