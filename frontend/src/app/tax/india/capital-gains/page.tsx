"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  ArrowLeft,
  Coins,
  Plus,
  Trash2,
} from "lucide-react";
import { API_BASE } from "@/lib/api";

interface TransactionRow {
  id: string;
  asset_name: string;
  asset_type: "listed_equity" | "unlisted_equity" | "real_estate" | "debt_fund" | "vda_crypto";
  purchase_date: string;
  sale_date: string;
  purchase_cost: number;
  sale_value: number;
  transfer_expenses: number;
}

interface CapitalGainsSummary {
  total_stcg_taxable: number;
  total_ltcg_taxable: number;
  total_vda_taxable: number;
  ltcg_112a_exemption_claimed: number;
  stcg_tax: number;
  ltcg_tax: number;
  vda_tax: number;
  total_capital_gains_tax: number;
  effective_cess: number;
  total_tax_payable_with_cess: number;
}

export default function CapitalGainsCalculatorPage() {
  const [assessmentYear, setAssessmentYear] = useState<"2025-26" | "2024-25">("2025-26");
  const [transactions, setTransactions] = useState<TransactionRow[]>([
    {
      id: "tx-1",
      asset_name: "TCS / Infosys Shares",
      asset_type: "listed_equity",
      purchase_date: "2023-04-10",
      sale_date: "2024-11-15",
      purchase_cost: 200000,
      sale_value: 450000,
      transfer_expenses: 500,
    },
    {
      id: "tx-2",
      asset_name: "Bitcoin / Ethereum",
      asset_type: "vda_crypto",
      purchase_date: "2024-01-05",
      sale_date: "2024-08-20",
      purchase_cost: 50000,
      sale_value: 120000,
      transfer_expenses: 0,
    },
  ]);

  const [summary, setSummary] = useState<CapitalGainsSummary | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function calculateGains() {
      const payload = {
        assessment_year: assessmentYear,
        transactions: transactions.map((t) => ({
          asset_type: t.asset_type,
          purchase_date: t.purchase_date,
          sale_date: t.sale_date,
          sale_price: t.sale_value,
          purchase_price: t.purchase_cost,
          transfer_expenses: t.transfer_expenses,
        })),
      };

      try {
        const res = await fetch(`${API_BASE}/india/capital-gains/calculate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (res.ok) {
          const data = await res.json();
          if (!cancelled) {
            setSummary({
              total_stcg_taxable: data.total_stcg_taxable ?? 0,
              total_ltcg_taxable: data.total_ltcg_taxable ?? 0,
              total_vda_taxable: data.total_vda_taxable ?? 0,
              ltcg_112a_exemption_claimed: data.ltcg_112a_exemption_claimed ?? 125000,
              stcg_tax: data.stcg_tax ?? 0,
              ltcg_tax: data.ltcg_tax ?? 0,
              vda_tax: data.vda_tax ?? 0,
              total_capital_gains_tax: data.total_capital_gains_tax ?? 0,
              effective_cess: data.effective_cess ?? 0,
              total_tax_payable_with_cess: data.total_tax_payable_with_cess ?? 0,
            });
          }
        } else {
          // Client fallback computation
          let stcgGains = 0;
          let ltcgGains = 0;
          let vdaGains = 0;

          transactions.forEach((tx) => {
            const gain = tx.sale_value - tx.purchase_cost - tx.transfer_expenses;
            if (tx.asset_type === "vda_crypto") {
              vdaGains += Math.max(0, gain);
            } else if (tx.asset_type === "listed_equity") {
              // LTCG if > 12 months
              const isLong = (new Date(tx.sale_date).getTime() - new Date(tx.purchase_date).getTime()) > 365 * 24 * 3600 * 1000;
              if (isLong) ltcgGains += gain;
              else stcgGains += gain;
            } else {
              ltcgGains += gain;
            }
          });

          const exemptLtcg = Math.min(Math.max(0, ltcgGains), 125000);
          const taxableLtcg = Math.max(0, ltcgGains - exemptLtcg);
          const stcgTax = Math.max(0, stcgGains) * 0.20;
          const ltcgTax = taxableLtcg * 0.125;
          const vdaTax = vdaGains * 0.30;
          const baseTax = stcgTax + ltcgTax + vdaTax;
          const cess = baseTax * 0.04;

          if (!cancelled) {
            setSummary({
              total_stcg_taxable: Math.max(0, stcgGains),
              total_ltcg_taxable: taxableLtcg,
              total_vda_taxable: vdaGains,
              ltcg_112a_exemption_claimed: exemptLtcg,
              stcg_tax: stcgTax,
              ltcg_tax: ltcgTax,
              vda_tax: vdaTax,
              total_capital_gains_tax: baseTax,
              effective_cess: cess,
              total_tax_payable_with_cess: baseTax + cess,
            });
          }
        }
      } catch {
        // Fallback on error
      }
    }

    calculateGains();
    return () => {
      cancelled = true;
    };
  }, [transactions, assessmentYear]);

  const addTransaction = () => {
    setTransactions([
      ...transactions,
      {
        id: `tx-${Date.now()}`,
        asset_name: "Mutual Fund / Equity",
        asset_type: "listed_equity",
        purchase_date: "2023-01-01",
        sale_date: "2024-09-01",
        purchase_cost: 100000,
        sale_value: 150000,
        transfer_expenses: 0,
      },
    ]);
  };

  const removeTransaction = (id: string) => {
    setTransactions(transactions.filter((t) => t.id !== id));
  };

  const updateTransaction = (
    id: string,
    field: keyof TransactionRow,
    value: string | number
  ) => {
    setTransactions(
      transactions.map((t) => (t.id === id ? { ...t, [field]: value } : t))
    );
  };

  const formatINR = (val: number) =>
    new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(Math.round(val));

  return (
    <div className="min-h-screen bg-[#faf9f6] text-[#2f3437] font-sans antialiased selection:bg-stone-200">
      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        {/* Navigation Header */}
        <div className="mb-6">
          <Link
            href="/tax/india"
            className="inline-flex items-center text-xs text-stone-500 hover:text-stone-800 transition-colors mb-4 group"
          >
            <ArrowLeft className="w-3.5 h-3.5 mr-1 group-hover:-translate-x-0.5 transition-transform" />
            Back to India Tax Hub
          </Link>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-3xl">📈</span>
              <div>
                <h1 className="text-2xl font-bold text-stone-900 tracking-tight">
                  India Capital Gains Tax Calculator
                </h1>
                <p className="text-sm text-stone-500">
                  Compute STCG (111A @ 20%), LTCG (112A @ 12.5% with ₹1.25L exemption), and VDA (115BBH @ 30%).
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <select
                value={assessmentYear}
                onChange={(e) => setAssessmentYear(e.target.value as "2025-26" | "2024-25")}
                aria-label="Select Assessment Year"
                className="bg-white border border-stone-300 rounded-lg text-xs font-semibold px-3 py-1.5 text-stone-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-emerald-600"
              >
                <option value="2025-26">AY 2025-26 (Budget 2024 Rates)</option>
                <option value="2024-25">AY 2024-25 (Pre-Budget Rates)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Transactions Table & Controls */}
        <div className="space-y-6">
          <div className="bg-white border border-stone-200/80 rounded-xl p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-bold text-stone-800 flex items-center gap-2">
                <Coins className="w-4 h-4 text-emerald-600" />
                Asset Transactions & Trades
              </span>
              <button
                onClick={addTransaction}
                className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200/60 px-3 py-1.5 rounded-lg transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
                Add Asset
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead>
                  <tr className="border-b border-stone-200 text-stone-500 font-semibold uppercase tracking-wider">
                    <th className="pb-2">Asset Name</th>
                    <th className="pb-2">Category</th>
                    <th className="pb-2">Buy Date</th>
                    <th className="pb-2">Sell Date</th>
                    <th className="pb-2 text-right">Buy Cost</th>
                    <th className="pb-2 text-right">Sale Price</th>
                    <th className="pb-2 text-right">Gain / Loss</th>
                    <th className="pb-2 text-center">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-stone-100">
                  {transactions.map((tx) => {
                    const gain = tx.sale_value - tx.purchase_cost - tx.transfer_expenses;
                    return (
                      <tr key={tx.id} className="hover:bg-stone-50/60 transition-colors">
                        <td className="py-2.5 pr-2">
                          <input
                            type="text"
                            value={tx.asset_name}
                            onChange={(e) => updateTransaction(tx.id, "asset_name", e.target.value)}
                            className="border border-stone-200 rounded px-2 py-1 text-xs w-36 font-medium text-stone-800"
                          />
                        </td>
                        <td className="py-2.5 pr-2">
                          <select
                            value={tx.asset_type}
                            onChange={(e) => updateTransaction(tx.id, "asset_type", e.target.value)}
                            className="border border-stone-200 rounded px-2 py-1 text-xs bg-white text-stone-700 font-medium"
                          >
                            <option value="listed_equity">Listed Equity / MF</option>
                            <option value="unlisted_equity">Unlisted Shares</option>
                            <option value="real_estate">Real Estate</option>
                            <option value="debt_fund">Debt Mutual Fund</option>
                            <option value="vda_crypto">Crypto / VDA</option>
                          </select>
                        </td>
                        <td className="py-2.5 pr-2">
                          <input
                            type="date"
                            value={tx.purchase_date}
                            onChange={(e) => updateTransaction(tx.id, "purchase_date", e.target.value)}
                            className="border border-stone-200 rounded px-1.5 py-1 text-xs text-stone-700 font-mono"
                          />
                        </td>
                        <td className="py-2.5 pr-2">
                          <input
                            type="date"
                            value={tx.sale_date}
                            onChange={(e) => updateTransaction(tx.id, "sale_date", e.target.value)}
                            className="border border-stone-200 rounded px-1.5 py-1 text-xs text-stone-700 font-mono"
                          />
                        </td>
                        <td className="py-2.5 pr-2 text-right">
                          <input
                            type="number"
                            value={tx.purchase_cost}
                            onChange={(e) => updateTransaction(tx.id, "purchase_cost", Number(e.target.value))}
                            className="border border-stone-200 rounded px-2 py-1 text-xs w-24 text-right font-medium text-stone-800"
                          />
                        </td>
                        <td className="py-2.5 pr-2 text-right">
                          <input
                            type="number"
                            value={tx.sale_value}
                            onChange={(e) => updateTransaction(tx.id, "sale_value", Number(e.target.value))}
                            className="border border-stone-200 rounded px-2 py-1 text-xs w-24 text-right font-medium text-stone-800"
                          />
                        </td>
                        <td className={`py-2.5 pr-2 text-right font-bold ${gain >= 0 ? "text-emerald-700" : "text-rose-600"}`}>
                          {formatINR(gain)}
                        </td>
                        <td className="py-2.5 text-center">
                          <button
                            onClick={() => removeTransaction(tx.id)}
                            className="text-stone-400 hover:text-rose-600 p-1 transition-colors"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Results Summary Card */}
          {summary && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white border border-stone-200/80 rounded-xl p-5 shadow-sm space-y-2">
                <span className="text-xs font-semibold text-stone-500 uppercase tracking-wider block">
                  STCG (Section 111A @ 20%)
                </span>
                <div className="text-xl font-bold text-stone-900">
                  {formatINR(summary.total_stcg_taxable)}
                </div>
                <div className="text-xs text-rose-600 font-medium">
                  Tax: {formatINR(summary.stcg_tax)}
                </div>
              </div>

              <div className="bg-white border border-stone-200/80 rounded-xl p-5 shadow-sm space-y-2">
                <span className="text-xs font-semibold text-stone-500 uppercase tracking-wider block">
                  LTCG (Section 112A @ 12.5%)
                </span>
                <div className="text-xl font-bold text-stone-900">
                  {formatINR(summary.total_ltcg_taxable)}
                </div>
                <div className="text-xs text-stone-500 flex justify-between">
                  <span>Exemption: {formatINR(summary.ltcg_112a_exemption_claimed)}</span>
                  <span className="text-rose-600 font-medium">Tax: {formatINR(summary.ltcg_tax)}</span>
                </div>
              </div>

              <div className="bg-gradient-to-br from-emerald-500/10 via-emerald-500/5 to-transparent border border-emerald-500/20 rounded-xl p-5 shadow-sm space-y-2">
                <span className="text-xs font-semibold text-emerald-800 uppercase tracking-wider block">
                  Total Tax Payable (with 4% Cess)
                </span>
                <div className="text-2xl font-bold text-emerald-950">
                  {formatINR(summary.total_tax_payable_with_cess)}
                </div>
                <div className="text-xs text-emerald-800/80 font-medium">
                  Base Tax: {formatINR(summary.total_capital_gains_tax)} + Cess: {formatINR(summary.effective_cess)}
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
