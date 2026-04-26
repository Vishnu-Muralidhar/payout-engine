import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { CreditCard, Activity, CheckCircle, Clock, XCircle, AlertCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
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

  // Calculate percentages for liquid bar
  const totalBalance = (balance?.available_balance || 0) + (balance?.held_balance || 0);
  const heldPercentage = totalBalance > 0 ? ((balance?.held_balance || 0) / totalBalance) * 100 : 0;
  const availablePercentage = totalBalance > 0 ? ((balance?.available_balance || 0) / totalBalance) * 100 : 0;

  return (
    <div className="min-h-screen p-8 max-w-6xl mx-auto space-y-12">
      <header className="flex items-center justify-between mb-12">
        <div>
          <h1 className="text-4xl font-extrabold text-white tracking-[0.2em] uppercase">
            Payto Merchant Payment Dashboard
          </h1>
          <p className="text-[#888888] mt-2 tracking-widest text-sm uppercase">Payout Engine</p>
        </div>
      </header>

      {/* Balance Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="glass-panel p-8 relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-opacity">
            <CreditCard size={80} />
          </div>
          <h3 className="text-[#737373] tracking-[0.1em] text-sm uppercase font-semibold mb-4">Available Balance</h3>
          {balanceLoading ? (
            <div className="h-10 w-32 bg-[#111] rounded animate-pulse" />
          ) : balanceError ? (
            <div className="text-red-400 flex items-center"><AlertCircle className="mr-2" /> Error loading</div>
          ) : (
            <>
              <div className="text-5xl font-light text-white tracking-wider">
                {formatCurrency(balance?.available_balance || 0)}
              </div>
              {/* Liquid Progress Bar */}
              <div className="mt-6 h-2 w-full bg-[#111] rounded-full overflow-hidden">
                <motion.div 
                  initial={{ width: 0 }}
                  animate={{ width: `${availablePercentage}%` }}
                  transition={{ duration: 1, ease: "easeOut" }}
                  className="h-full bg-white rounded-full"
                />
              </div>
            </>
          )}
        </div>

        <div className="glass-panel p-8 relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-opacity">
            <Activity size={80} />
          </div>
          <h3 className="text-[#737373] tracking-[0.1em] text-sm uppercase font-semibold mb-4">Pending Execution</h3>
          {balanceLoading ? (
            <div className="h-10 w-32 bg-[#111] rounded animate-pulse" />
          ) : (
            <>
              <div className="text-5xl font-light text-white tracking-wider">
                {formatCurrency(balance?.held_balance || 0)}
              </div>
              {/* Liquid Progress Bar with Mercury effect */}
              <div className="mt-6 h-2 w-full bg-[#111] rounded-full overflow-hidden">
                <motion.div 
                  initial={{ width: 0 }}
                  animate={{ width: `${heldPercentage}%` }}
                  transition={{ duration: 1, ease: "easeOut" }}
                  className="h-full bg-white mercury-liquid rounded-full"
                />
              </div>
            </>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
        
        {/* Payout Request Form */}
        <div className="lg:col-span-1 space-y-6">
          <div className="glass-panel p-8">
            <h2 className="text-sm text-[#888888] tracking-[0.15em] uppercase font-semibold mb-6">Execute Order</h2>
            <form onSubmit={handlePayoutSubmit} className="space-y-6">
              <div>
                <label className="block text-xs text-[#555555] tracking-widest uppercase mb-2">Amount (INR)</label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 text-[#555]">₹</span>
                  <input
                    type="number"
                    step="0.01"
                    min="1"
                    required
                    value={amountInput}
                    onChange={(e) => setAmountInput(e.target.value)}
                    className="w-full bg-[#0a0a0a] border border-white/5 rounded-xl py-3 pl-10 pr-4 text-white focus:outline-none focus:border-white/20 focus:bg-[#111] transition-all font-light tracking-wider"
                    placeholder="0.00"
                    disabled={payoutMutation.isPending}
                  />
                </div>
              </div>
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                type="submit"
                disabled={payoutMutation.isPending}
                className="w-full bg-white hover:bg-gray-200 text-black font-semibold tracking-widest uppercase text-sm py-3.5 rounded-xl transition-colors flex items-center justify-center disabled:opacity-50"
              >
                {payoutMutation.isPending ? 'Processing...' : 'Withdraw'}
              </motion.button>
              {payoutMutation.isError && (
                <p className="text-xs tracking-wide text-red-400 mt-3">
                  {(payoutMutation.error as any)?.response?.data?.error || 'Execution failed.'}
                </p>
              )}
            </form>
          </div>
        </div>

        {/* Payout History */}
        <div className="lg:col-span-2">
          <div className="glass-panel p-8 min-h-[400px]">
            <h2 className="text-sm text-[#888888] tracking-[0.15em] uppercase font-semibold mb-6">Execution Log</h2>
            
            {payoutsLoading ? (
              <div className="space-y-4">
                {[1, 2, 3].map(i => (
                  <div key={i} className="h-20 bg-[#0c0c0c] rounded-xl animate-pulse" />
                ))}
              </div>
            ) : payouts?.length === 0 ? (
              <div className="text-center text-[#555] tracking-widest uppercase text-sm py-16">
                No executions found
              </div>
            ) : (
              <div className="space-y-4">
                <AnimatePresence>
                  {payouts?.map((payout: any) => (
                    <motion.div 
                      key={payout.id} 
                      layout
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      whileHover={{ scale: 1.02 }}
                      className={clsx(
                        "magnetic-row flex items-center justify-between relative overflow-hidden",
                        payout.state === 'COMPLETED' ? "gold-shimmer" : ""
                      )}
                    >
                      <div className="relative z-10">
                        <div className="text-xl font-light tracking-wider text-white">
                          {formatCurrency(payout.amount)}
                        </div>
                        <div className="text-[10px] text-[#555] mt-1 tracking-widest uppercase">
                          {new Date(payout.created_at).toLocaleString()}
                        </div>
                      </div>
                      <div className="relative z-10">
                        <PayoutStatusBadge status={payout.state} />
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function PayoutStatusBadge({ status }: { status: string }) {
  const baseClasses = "px-3 py-1 rounded-full text-[10px] tracking-widest uppercase font-semibold flex items-center gap-1.5 border";
  
  switch (status) {
    case 'COMPLETED':
      return <span className={clsx(baseClasses, "bg-white/5 text-white border-white/20 shadow-[0_0_10px_rgba(255,255,255,0.1)]")}><CheckCircle size={12}/> Completed</span>;
    case 'PROCESSING':
      return <span className={clsx(baseClasses, "bg-transparent text-[#888] border-[#333]")}><Activity size={12} className="animate-pulse"/> Processing</span>;
    case 'PENDING':
      return <span className={clsx(baseClasses, "bg-transparent text-[#555] border-[#222]")}><Clock size={12}/> Pending</span>;
    case 'FAILED':
      return <span className={clsx(baseClasses, "bg-red-500/5 text-red-400 border-red-500/20")}><XCircle size={12}/> Failed</span>;
    default:
      return <span className={clsx(baseClasses, "bg-transparent text-[#555] border-[#222]")}>{status}</span>;
  }
}
