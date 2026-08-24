"use client";

import Link from "next/link";
import { useEffect, useState, useId } from "react";
import {
  ArrowLeft,
  Calendar,
  ShieldCheck,
  Clock,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";
import { API_BASE } from "@/lib/api";

interface ScheduleItem {
  installment_name: string;
  due_date: string;
  cumulative_percentage_required: number;
  cumulative_amount_required: number;
  incremental_amount_required: number;
  amount_paid: number;
  shortfall: number;
}

interface AdvanceTaxResult {
  net_tax_liability: number;
  is_advance_tax_applicable: boolean;
  schedule: ScheduleItem[];
  interest_234a: number;
  interest_234b: number;
  interest_234c: number;
  late_filing_fee_234f: number;
  total_interest_and_penalty: number;
  total_amount_payable: number;
}

export default function IndiaAdvanceTaxPage() {
  const taxInputId = useId();
  const tdsInputId = useId();
  const q1InputId = useId();
  const q2InputId = useId();
  const q3InputId = useId();
  const q4InputId = useId();
  const delayAInputId = useId();
  const delayBInputId = useId();

  const [totalTaxAssessed, setTotalTaxAssessed] = useState<number>(250000);
  const [tdsCredits, setTdsCredits] = useState<number>(50000);
  const [q1Paid, setQ1Paid] = useState<number>(30000);
  const [q2Paid, setQ2Paid] = useState<number>(60000);
  const [q3Paid, setQ3Paid] = useState<number>(60000);
  const [q4Paid, setQ4Paid] = useState<number>(50000);
  const [delay234A, setDelay234A] = useState<number>(0);
  const [delay234B, setDelay234B] = useState<number>(0);
  const [result, setResult] = useState<AdvanceTaxResult | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function calculateAdvanceTax() {
      try {
        const res = await fetch(`${API_BASE}/api/v1/india/advance-tax/calculate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            total_tax_assessed: totalTaxAssessed,
            tds_tcs_credits: tdsCredits,
            q1_paid_by_jun15: q1Paid,
            q2_paid_by_sep15: q2Paid,
            q3_paid_by_dec15: q3Paid,
            q4_paid_by_mar15: q4Paid,
            months_delay_filing_234a: delay234A,
            months_delay_payment_234b: delay234B,
            is_return_late_234f: delay234A > 0,
            total_taxable_income: totalTaxAssessed * 3.33,
          }),
        });

        if (res.ok) {
          const data = await res.json();
          if (!cancelled) {
            setResult({
              net_tax_liability: Number(data.net_tax_liability),
              is_advance_tax_applicable: Boolean(data.is_advance_tax_applicable),
              schedule: (data.schedule || []).map((s: {
                installment_name: string;
                due_date: string;
                cumulative_percentage_required: number | string;
                cumulative_amount_required: number | string;
                incremental_amount_required: number | string;
                amount_paid: number | string;
                shortfall: number | string;
              }) => ({
                installment_name: s.installment_name,
                due_date: s.due_date,
                cumulative_percentage_required: Number(s.cumulative_percentage_required),
                cumulative_amount_required: Number(s.cumulative_amount_required),
                incremental_amount_required: Number(s.incremental_amount_required),
                amount_paid: Number(s.amount_paid),
                shortfall: Number(s.shortfall),
              })),
              interest_234a: Number(data.interest_234a),
              interest_234b: Number(data.interest_234b),
              interest_234c: Number(data.interest_234c),
              late_filing_fee_234f: Number(data.late_filing_fee_234f),
              total_interest_and_penalty: Number(data.total_interest_and_penalty),
              total_amount_payable: Number(data.total_amount_payable),
            });
          }
        }
      } catch {
        // network fallback
      }
    }

    calculateAdvanceTax();
    return () => {
      cancelled = true;
    };
  }, [totalTaxAssessed, tdsCredits, q1Paid, q2Paid, q3Paid, q4Paid, delay234A, delay234B]);

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
          <div className="flex items-center gap-3">
            <span className="text-3xl">🗓️</span>
            <div>
              <h1 className="text-2xl font-bold text-stone-900 tracking-tight">
                Advance Tax & Section 234A/B/C Calculator
              </h1>
              <p className="text-sm text-stone-500">
                Plan statutory quarterly installments (15%, 45%, 75%, 100%) and compute late interest under Sections 234A, 234B, and 234C.
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column: Inputs & Installment Paid Record */}
          <div className="lg:col-span-7 space-y-6">
            {/* Tax Liability Base */}
            <div className="bg-white border border-stone-200 rounded-xl p-5 shadow-xs">
              <h2 className="text-sm font-semibold text-stone-900 uppercase tracking-wider mb-4 flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                Annual Tax & TDS Credits
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label htmlFor={taxInputId} className="block text-xs font-semibold text-stone-700 mb-1">
                    Total Estimated Annual Tax (₹)
                  </label>
                  <input
                    id={taxInputId}
                    type="number"
                    value={totalTaxAssessed || ""}
                    onChange={(e) => setTotalTaxAssessed(Number(e.target.value) || 0)}
                    className="w-full bg-stone-50 border border-stone-300 rounded-lg px-3 py-2 text-sm font-medium text-stone-800 focus:outline-none focus:ring-2 focus:ring-emerald-600 focus:bg-white"
                  />
                  <p className="text-[11px] text-stone-400 mt-1">Tax assessed on total estimated income</p>
                </div>
                <div>
                  <label htmlFor={tdsInputId} className="block text-xs font-semibold text-stone-700 mb-1">
                    TDS / TCS / Other Credits (₹)
                  </label>
                  <input
                    id={tdsInputId}
                    type="number"
                    value={tdsCredits || ""}
                    onChange={(e) => setTdsCredits(Number(e.target.value) || 0)}
                    className="w-full bg-stone-50 border border-stone-300 rounded-lg px-3 py-2 text-sm font-medium text-stone-800 focus:outline-none focus:ring-2 focus:ring-emerald-600 focus:bg-white"
                  />
                  <p className="text-[11px] text-stone-400 mt-1">Taxes already deducted by employer or clients</p>
                </div>
              </div>
            </div>

            {/* Quarterly Payments Made */}
            <div className="bg-white border border-stone-200 rounded-xl p-5 shadow-xs">
              <h2 className="text-sm font-semibold text-stone-900 uppercase tracking-wider mb-4 flex items-center gap-2">
                <Calendar className="w-4 h-4 text-blue-600" />
                Actual Advance Tax Payments Deposited
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label htmlFor={q1InputId} className="block text-xs font-semibold text-stone-700 mb-1">
                    Q1: Deposited by 15 June (₹)
                  </label>
                  <input
                    id={q1InputId}
                    type="number"
                    value={q1Paid || ""}
                    onChange={(e) => setQ1Paid(Number(e.target.value) || 0)}
                    className="w-full bg-stone-50 border border-stone-300 rounded-lg px-3 py-2 text-sm font-medium text-stone-800 focus:outline-none focus:ring-2 focus:ring-emerald-600 focus:bg-white"
                  />
                  <p className="text-[11px] text-stone-400 mt-1">Target: min 15% of net tax</p>
                </div>
                <div>
                  <label htmlFor={q2InputId} className="block text-xs font-semibold text-stone-700 mb-1">
                    Q2: Deposited by 15 Sept (₹)
                  </label>
                  <input
                    id={q2InputId}
                    type="number"
                    value={q2Paid || ""}
                    onChange={(e) => setQ2Paid(Number(e.target.value) || 0)}
                    className="w-full bg-stone-50 border border-stone-300 rounded-lg px-3 py-2 text-sm font-medium text-stone-800 focus:outline-none focus:ring-2 focus:ring-emerald-600 focus:bg-white"
                  />
                  <p className="text-[11px] text-stone-400 mt-1">Target: min 45% cumulative</p>
                </div>
                <div>
                  <label htmlFor={q3InputId} className="block text-xs font-semibold text-stone-700 mb-1">
                    Q3: Deposited by 15 Dec (₹)
                  </label>
                  <input
                    id={q3InputId}
                    type="number"
                    value={q3Paid || ""}
                    onChange={(e) => setQ3Paid(Number(e.target.value) || 0)}
                    className="w-full bg-stone-50 border border-stone-300 rounded-lg px-3 py-2 text-sm font-medium text-stone-800 focus:outline-none focus:ring-2 focus:ring-emerald-600 focus:bg-white"
                  />
                  <p className="text-[11px] text-stone-400 mt-1">Target: min 75% cumulative</p>
                </div>
                <div>
                  <label htmlFor={q4InputId} className="block text-xs font-semibold text-stone-700 mb-1">
                    Q4: Deposited by 15 Mar (₹)
                  </label>
                  <input
                    id={q4InputId}
                    type="number"
                    value={q4Paid || ""}
                    onChange={(e) => setQ4Paid(Number(e.target.value) || 0)}
                    className="w-full bg-stone-50 border border-stone-300 rounded-lg px-3 py-2 text-sm font-medium text-stone-800 focus:outline-none focus:ring-2 focus:ring-emerald-600 focus:bg-white"
                  />
                  <p className="text-[11px] text-stone-400 mt-1">Target: 100% full payment</p>
                </div>
              </div>
            </div>

            {/* Delay in Filing / Assessment */}
            <div className="bg-white border border-stone-200 rounded-xl p-5 shadow-xs">
              <h2 className="text-sm font-semibold text-stone-900 uppercase tracking-wider mb-4 flex items-center gap-2">
                <Clock className="w-4 h-4 text-amber-600" />
                Return Filing & Delay Parameters
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label htmlFor={delayAInputId} className="block text-xs font-semibold text-stone-700 mb-1">
                    Months Delay in Return Filing (Sec 234A)
                  </label>
                  <input
                    id={delayAInputId}
                    type="number"
                    min="0"
                    max="36"
                    value={delay234A}
                    onChange={(e) => setDelay234A(Number(e.target.value) || 0)}
                    className="w-full bg-stone-50 border border-stone-300 rounded-lg px-3 py-2 text-sm font-medium text-stone-800 focus:outline-none focus:ring-2 focus:ring-emerald-600 focus:bg-white"
                  />
                  <p className="text-[11px] text-stone-400 mt-1">1% per month on outstanding tax past July 31</p>
                </div>
                <div>
                  <label htmlFor={delayBInputId} className="block text-xs font-semibold text-stone-700 mb-1">
                    Months Delay in Payment Past Mar 31 (Sec 234B)
                  </label>
                  <input
                    id={delayBInputId}
                    type="number"
                    min="0"
                    max="36"
                    value={delay234B}
                    onChange={(e) => setDelay234B(Number(e.target.value) || 0)}
                    className="w-full bg-stone-50 border border-stone-300 rounded-lg px-3 py-2 text-sm font-medium text-stone-800 focus:outline-none focus:ring-2 focus:ring-emerald-600 focus:bg-white"
                  />
                  <p className="text-[11px] text-stone-400 mt-1">1% per month if &lt;90% paid before April 1</p>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Schedule & Interest Summary */}
          <div className="lg:col-span-5 space-y-6">
            {/* Net Liability & Threshold Banner */}
            <div className="bg-white border border-stone-200 rounded-xl p-5 shadow-xs">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-stone-500 uppercase tracking-wider">
                  Net Advance Tax Liability
                </span>
                {result?.is_advance_tax_applicable ? (
                  <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                    <AlertCircle className="w-3 h-3" />
                    Applicable (Net &gt; ₹10,000)
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                    <CheckCircle2 className="w-3 h-3" />
                    Exempt (Net ≤ ₹10,000)
                  </span>
                )}
              </div>
              <div className="text-2xl font-bold text-stone-900 tracking-tight mb-2">
                {result ? formatINR(result.net_tax_liability) : "₹0"}
              </div>
              <p className="text-xs text-stone-500 leading-relaxed">
                Under Section 208 of the Income-tax Act, advance tax is mandatory if total estimated tax liability after TDS/TCS exceeds ₹10,000.
              </p>
            </div>

            {/* Installment Compliance Table */}
            <div className="bg-white border border-stone-200 rounded-xl p-5 shadow-xs">
              <h3 className="text-xs font-semibold text-stone-900 uppercase tracking-wider mb-3">
                Quarterly Installment Schedule
              </h3>
              <div className="space-y-3">
                {result?.schedule.map((item, idx) => (
                  <div
                    key={idx}
                    className="p-3 bg-stone-50 rounded-lg border border-stone-200 flex items-center justify-between text-xs"
                  >
                    <div>
                      <div className="font-semibold text-stone-900">{item.installment_name}</div>
                      <div className="text-[11px] text-stone-500">
                        Due: {item.due_date} ({item.cumulative_percentage_required}%)
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold text-stone-800">
                        Paid: {formatINR(item.amount_paid)}
                      </div>
                      <div className="text-[11px] text-stone-500">
                        Req: {formatINR(item.cumulative_amount_required)}
                      </div>
                      {item.shortfall > 0 && (
                        <div className="text-[10px] text-red-600 font-medium">
                          Shortfall: {formatINR(item.shortfall)}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Interest & Penalty Summary Card */}
            <div className="bg-stone-900 text-white rounded-xl p-5 shadow-sm space-y-4">
              <h3 className="text-xs font-semibold text-stone-300 uppercase tracking-wider">
                Interest & Penalties (Chapter XVII-F)
              </h3>
              <div className="space-y-2.5 text-xs">
                <div className="flex justify-between items-center text-stone-300">
                  <span>Sec 234C (Quarterly Deferment Interest @ 1%)</span>
                  <span className="font-semibold text-white">
                    {result ? formatINR(result.interest_234c) : "₹0"}
                  </span>
                </div>
                <div className="flex justify-between items-center text-stone-300">
                  <span>Sec 234B (Default in Payment &lt;90% @ 1%/mo)</span>
                  <span className="font-semibold text-white">
                    {result ? formatINR(result.interest_234b) : "₹0"}
                  </span>
                </div>
                <div className="flex justify-between items-center text-stone-300">
                  <span>Sec 234A (Delay in Return Filing @ 1%/mo)</span>
                  <span className="font-semibold text-white">
                    {result ? formatINR(result.interest_234a) : "₹0"}
                  </span>
                </div>
                {result && result.late_filing_fee_234f > 0 && (
                  <div className="flex justify-between items-center text-stone-300">
                    <span>Sec 234F (Late Filing Fee)</span>
                    <span className="font-semibold text-amber-400">
                      {formatINR(result.late_filing_fee_234f)}
                    </span>
                  </div>
                )}
                <div className="pt-3 border-t border-stone-800 flex justify-between items-center text-sm font-bold">
                  <span className="text-emerald-400">Total Tax & Interest Payable</span>
                  <span className="text-emerald-400 text-lg">
                    {result ? formatINR(result.total_amount_payable) : "₹0"}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
