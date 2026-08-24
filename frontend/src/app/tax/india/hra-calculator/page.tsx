"use client";

import Link from "next/link";
import { useEffect, useState, useId } from "react";
import {
  ArrowLeft,
  Home,
  ShieldCheck,
} from "lucide-react";
import { API_BASE } from "@/lib/api";

interface HRAExemptionData {
  basic_salary: number;
  hra_received: number;
  annual_rent_paid: number;
  is_metro: boolean;
  actual_hra_received: number;
  rent_paid_excess_of_ten_percent_basic: number;
  metro_or_non_metro_limit: number;
  exempt_hra_amount: number;
  taxable_hra_amount: number;
  statutory_section: string;
}

export default function HRAExemptionCalculatorPage() {
  const basicInputId = useId();
  const hraInputId = useId();
  const rentInputId = useId();

  const [basicSalary, setBasicSalary] = useState<number>(600000);
  const [hraReceived, setHraReceived] = useState<number>(240000);
  const [annualRentPaid, setAnnualRentPaid] = useState<number>(300000);
  const [isMetro, setIsMetro] = useState<boolean>(true);
  const [result, setResult] = useState<HRAExemptionData | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function fetchHRA() {
      const payload = {
        basic_salary: basicSalary,
        hra_received: hraReceived,
        annual_rent_paid: annualRentPaid,
        is_metro: isMetro,
      };

      try {
        const res = await fetch(`${API_BASE}/india/salary/hra-exemption`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (res.ok) {
          const data = await res.json();
          if (!cancelled) setResult(data);
        } else {
          // Local statutory fallback
          const limit1 = hraReceived;
          const limit2 = Math.max(0, annualRentPaid - basicSalary * 0.1);
          const limit3 = basicSalary * (isMetro ? 0.5 : 0.4);
          const exempt = Math.min(limit1, limit2, limit3);
          const taxable = Math.max(0, hraReceived - exempt);

          if (!cancelled) {
            setResult({
              basic_salary: basicSalary,
              hra_received: hraReceived,
              annual_rent_paid: annualRentPaid,
              is_metro: isMetro,
              actual_hra_received: limit1,
              rent_paid_excess_of_ten_percent_basic: limit2,
              metro_or_non_metro_limit: limit3,
              exempt_hra_amount: exempt,
              taxable_hra_amount: taxable,
              statutory_section: "Section 10(13A) read with Rule 2A",
            });
          }
        }
      } catch {
        // Fallback
      }
    }

    fetchHRA();
    return () => {
      cancelled = true;
    };
  }, [basicSalary, hraReceived, annualRentPaid, isMetro]);

  const formatINR = (val: number) =>
    new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(Math.round(val));

  return (
    <div className="min-h-screen bg-[#faf9f6] text-[#2f3437] font-sans antialiased selection:bg-stone-200">
      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
        {/* Header */}
        <div className="mb-6">
          <Link
            href="/tax/india"
            className="inline-flex items-center text-xs text-stone-500 hover:text-stone-800 transition-colors mb-4 group"
          >
            <ArrowLeft className="w-3.5 h-3.5 mr-1 group-hover:-translate-x-0.5 transition-transform" />
            Back to India Tax Hub
          </Link>
          <div className="flex items-center gap-3">
            <span className="text-3xl">🏠</span>
            <div>
              <h1 className="text-2xl font-bold text-stone-900 tracking-tight">
                HRA Exemption Calculator (Section 10(13A))
              </h1>
              <p className="text-sm text-stone-500">
                Calculate statutory House Rent Allowance exemption under Rule 2A of the Income Tax Rules.
              </p>
            </div>
          </div>
        </div>

        {/* Layout Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Controls */}
          <div className="lg:col-span-6 space-y-6">
            <div className="bg-white border border-stone-200/80 rounded-xl p-6 shadow-sm space-y-5">
              <span className="text-sm font-semibold text-stone-800 flex items-center gap-1.5 border-b border-stone-100 pb-3">
                <Home className="w-4 h-4 text-emerald-600" />
                Salary & Rent Details
              </span>

              {/* Basic Salary */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs">
                  <label htmlFor={basicInputId} className="font-medium text-stone-700">Annual Basic Salary + DA</label>
                  <span className="font-bold text-stone-900">{formatINR(basicSalary)}</span>
                </div>
                <input
                  id={basicInputId}
                  type="number"
                  value={basicSalary}
                  onChange={(e) => setBasicSalary(Math.max(0, Number(e.target.value)))}
                  className="w-full px-3 py-2 border border-stone-300 rounded-lg text-sm font-medium focus:ring-2 focus:ring-emerald-600 focus:outline-none"
                />
              </div>

              {/* HRA Received */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs">
                  <label htmlFor={hraInputId} className="font-medium text-stone-700">Annual HRA Received</label>
                  <span className="font-bold text-stone-900">{formatINR(hraReceived)}</span>
                </div>
                <input
                  id={hraInputId}
                  type="number"
                  value={hraReceived}
                  onChange={(e) => setHraReceived(Math.max(0, Number(e.target.value)))}
                  className="w-full px-3 py-2 border border-stone-300 rounded-lg text-sm font-medium focus:ring-2 focus:ring-emerald-600 focus:outline-none"
                />
              </div>

              {/* Annual Rent Paid */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs">
                  <label htmlFor={rentInputId} className="font-medium text-stone-700">Total Annual Rent Paid</label>
                  <span className="font-bold text-stone-900">{formatINR(annualRentPaid)}</span>
                </div>
                <input
                  id={rentInputId}
                  type="number"
                  value={annualRentPaid}
                  onChange={(e) => setAnnualRentPaid(Math.max(0, Number(e.target.value)))}
                  className="w-full px-3 py-2 border border-stone-300 rounded-lg text-sm font-medium focus:ring-2 focus:ring-emerald-600 focus:outline-none"
                />
              </div>

              {/* City Selection */}
              <div className="space-y-2 pt-2 border-t border-stone-100">
                <span className="text-xs font-semibold text-stone-700 block">Accommodation Location</span>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    onClick={() => setIsMetro(true)}
                    className={`p-3 rounded-lg border text-left transition-all ${
                      isMetro
                        ? "border-emerald-600 bg-emerald-50/50 text-emerald-950 ring-1 ring-emerald-600"
                        : "border-stone-200 hover:border-stone-300 text-stone-700"
                    }`}
                  >
                    <span className="text-xs font-bold block">Metro City (50%)</span>
                    <span className="text-[11px] text-stone-500 block">Delhi, Mumbai, Kolkata, Chennai</span>
                  </button>
                  <button
                    onClick={() => setIsMetro(false)}
                    className={`p-3 rounded-lg border text-left transition-all ${
                      !isMetro
                        ? "border-emerald-600 bg-emerald-50/50 text-emerald-950 ring-1 ring-emerald-600"
                        : "border-stone-200 hover:border-stone-300 text-stone-700"
                    }`}
                  >
                    <span className="text-xs font-bold block">Non-Metro City (40%)</span>
                    <span className="text-[11px] text-stone-500 block">Bangalore, Hyderabad, Pune, etc.</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Results Summary */}
          <div className="lg:col-span-6 space-y-6">
            {result && (
              <div className="bg-white border border-stone-200/80 rounded-xl p-6 shadow-sm space-y-6">
                {/* Hero Result */}
                <div className="bg-gradient-to-br from-emerald-500/10 via-emerald-500/5 to-transparent border border-emerald-500/20 rounded-xl p-5">
                  <span className="text-xs font-semibold text-emerald-800 uppercase tracking-wider block mb-1">
                    Exempt HRA Amount
                  </span>
                  <div className="text-3xl font-bold text-emerald-950">
                    {formatINR(result.exempt_hra_amount)}
                  </div>
                  <div className="mt-2 text-xs text-stone-600 flex items-center justify-between">
                    <span>Taxable HRA: <strong className="text-rose-700">{formatINR(result.taxable_hra_amount)}</strong></span>
                    <span className="text-stone-400">Monthly Exemption: <strong>{formatINR(result.exempt_hra_amount / 12)}</strong></span>
                  </div>
                </div>

                {/* 3-Limit Step Comparison */}
                <div className="space-y-3">
                  <h2 className="text-xs font-bold uppercase tracking-wider text-stone-600">
                    Rule 2A Three Statutory Limits (Least is Exempt)
                  </h2>
                  <div className="space-y-2 text-xs">
                    <div className="p-3 bg-stone-50 rounded-lg flex items-center justify-between">
                      <div>
                        <span className="font-semibold text-stone-800 block">1. Actual HRA Received</span>
                        <span className="text-[11px] text-stone-500">Total HRA provided by employer</span>
                      </div>
                      <span className="font-mono font-semibold text-stone-900">{formatINR(result.actual_hra_received)}</span>
                    </div>

                    <div className="p-3 bg-stone-50 rounded-lg flex items-center justify-between">
                      <div>
                        <span className="font-semibold text-stone-800 block">2. Rent Paid - 10% of Basic Salary</span>
                        <span className="text-[11px] text-stone-500">{formatINR(annualRentPaid)} - 10% of {formatINR(basicSalary)}</span>
                      </div>
                      <span className="font-mono font-semibold text-stone-900">{formatINR(result.rent_paid_excess_of_ten_percent_basic)}</span>
                    </div>

                    <div className="p-3 bg-stone-50 rounded-lg flex items-center justify-between">
                      <div>
                        <span className="font-semibold text-stone-800 block">3. {isMetro ? "50%" : "40%"} of Basic Salary</span>
                        <span className="text-[11px] text-stone-500">{isMetro ? "Metro City Rate" : "Non-Metro Rate"}</span>
                      </div>
                      <span className="font-mono font-semibold text-stone-900">{formatINR(result.metro_or_non_metro_limit)}</span>
                    </div>
                  </div>
                </div>

                {/* Legal Note */}
                <div className="p-3 bg-stone-50 border border-stone-200/60 rounded-lg text-xs text-stone-600">
                  <div className="flex items-center gap-1.5 font-semibold text-stone-800 mb-1">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                    <span>Statutory Note</span>
                  </div>
                  <p>
                    HRA exemption under Section 10(13A) is available only under the <strong>Old Tax Regime</strong>. Under Section 115BAC (New Tax Regime), HRA exemption cannot be claimed.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
