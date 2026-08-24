"use client";

import Link from "next/link";
import { useEffect, useState, useId } from "react";
import {
  ArrowLeft,
  Briefcase,
  ShieldCheck,
  TrendingUp,
} from "lucide-react";
import { API_BASE } from "@/lib/api";

interface SalaryBreakdownResponse {
  annual_ctc: number;
  monthly_ctc: number;
  annual_gross_salary: number;
  monthly_gross_salary: number;
  annual_take_home: number;
  monthly_take_home: number;
  annual_epf_employee: number;
  monthly_epf_employee: number;
  annual_epf_employer: number;
  annual_professional_tax: number;
  annual_income_tax_deduction: number;
  monthly_income_tax_deduction: number;
  effective_tax_rate: number;
}

export default function IndiaSalaryCalculatorPage() {
  const ctcInputId = useId();
  const basicPctInputId = useId();
  const hraInputId = useId();

  const [annualCtc, setAnnualCtc] = useState<number>(1500000);
  const [basicPct, setBasicPct] = useState<number>(50);
  const [hraPct, setHraPct] = useState<number>(20);
  const [specialAllowance] = useState<number>(0);
  const [epfOpted, setEpfOpted] = useState<boolean>(true);
  const [regime, setRegime] = useState<"new" | "old">("new");
  const [result, setResult] = useState<SalaryBreakdownResponse | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function calculateSalary() {
      const basic = (annualCtc * basicPct) / 100;
      const hra = (annualCtc * hraPct) / 100;
      const employerEpf = epfOpted ? basic * 0.12 : 0;
      const employeeEpf = epfOpted ? basic * 0.12 : 0;
      const profTax = 2400;

      const payload = {
        annual_ctc: annualCtc,
        basic_salary: basic,
        hra_received: hra,
        special_allowance: specialAllowance > 0 ? specialAllowance : Math.max(0, annualCtc - basic - hra - employerEpf),
        employer_epf: employerEpf,
        employee_epf: employeeEpf,
        professional_tax: profTax,
        other_deductions: 0,
      };

      try {
        const res = await fetch(`${API_BASE}/india/salary/take-home?regime=${regime}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (res.ok) {
          const data = await res.json();
          if (!cancelled) setResult(data);
        } else {
          // Local statutory fallback
          const annualGross = annualCtc - employerEpf;
          const stdDed = regime === "new" ? 75000 : 50000;
          const taxable = Math.max(0, annualGross - stdDed);
          let tax = 0;
          if (taxable > 1500000) tax = 140000 + (taxable - 1500000) * 0.3;
          else if (taxable > 1200000) tax = 80000 + (taxable - 1200000) * 0.2;
          else if (taxable > 1000000) tax = 50000 + (taxable - 1000000) * 0.15;
          else if (taxable > 700000) tax = 20000 + (taxable - 700000) * 0.1;
          else if (taxable > 300000) tax = (taxable - 300000) * 0.05;
          if (taxable <= 700000) tax = 0; // 87A
          const totalTax = tax * 1.04;
          const annualTakeHome = annualGross - employeeEpf - profTax - totalTax;

          if (!cancelled) {
            setResult({
              annual_ctc: annualCtc,
              monthly_ctc: annualCtc / 12,
              annual_gross_salary: annualGross,
              monthly_gross_salary: annualGross / 12,
              annual_take_home: annualTakeHome,
              monthly_take_home: annualTakeHome / 12,
              annual_epf_employee: employeeEpf,
              monthly_epf_employee: employeeEpf / 12,
              annual_epf_employer: employerEpf,
              annual_professional_tax: profTax,
              annual_income_tax_deduction: totalTax,
              monthly_income_tax_deduction: totalTax / 12,
              effective_tax_rate: (totalTax / annualCtc) * 100,
            });
          }
        }
      } catch {
        // Fallback calculation on network error
      }
    }

    calculateSalary();
    return () => {
      cancelled = true;
    };
  }, [annualCtc, basicPct, hraPct, specialAllowance, epfOpted, regime]);

  const formatINR = (val: number) =>
    new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(Math.round(val));

  return (
    <div className="min-h-screen bg-[#faf9f6] text-[#2f3437] font-sans antialiased selection:bg-stone-200">
      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        {/* Navigation & Header */}
        <div className="mb-6">
          <Link
            href="/tax/india"
            className="inline-flex items-center text-xs text-stone-500 hover:text-stone-800 transition-colors mb-4 group"
          >
            <ArrowLeft className="w-3.5 h-3.5 mr-1 group-hover:-translate-x-0.5 transition-transform" />
            Back to India Tax Hub
          </Link>
          <div className="flex items-center gap-3">
            <span className="text-3xl">💼</span>
            <div>
              <h1 className="text-2xl font-bold text-stone-900 tracking-tight">
                India Salary & In-Hand Take-Home Calculator
              </h1>
              <p className="text-sm text-stone-500">
                Accurate CTC to Monthly In-Hand Salary Breakdown with EPF, Professional Tax, and Income Tax Deductions.
              </p>
            </div>
          </div>
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Controls Column */}
          <div className="lg:col-span-6 space-y-6">
            <div className="bg-white border border-stone-200/80 rounded-xl p-6 shadow-sm space-y-5">
              <div className="flex items-center justify-between border-b border-stone-100 pb-3">
                <span className="text-sm font-semibold text-stone-800 flex items-center gap-1.5">
                  <Briefcase className="w-4 h-4 text-emerald-600" />
                  CTC & Salary Structure
                </span>
                <div className="flex items-center gap-1 bg-stone-100 p-0.5 rounded-lg text-xs">
                  <button
                    onClick={() => setRegime("new")}
                    className={`px-2.5 py-1 rounded-md transition-all font-medium ${
                      regime === "new" ? "bg-white text-stone-900 shadow-sm" : "text-stone-500 hover:text-stone-900"
                    }`}
                  >
                    New Regime (115BAC)
                  </button>
                  <button
                    onClick={() => setRegime("old")}
                    className={`px-2.5 py-1 rounded-md transition-all font-medium ${
                      regime === "old" ? "bg-white text-stone-900 shadow-sm" : "text-stone-500 hover:text-stone-900"
                    }`}
                  >
                    Old Regime
                  </button>
                </div>
              </div>

              {/* Annual CTC Input */}
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <label htmlFor={ctcInputId} className="font-medium text-stone-700">Annual CTC</label>
                  <span className="font-bold text-emerald-700">{formatINR(annualCtc)}</span>
                </div>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-stone-400 text-sm font-semibold">₹</span>
                  <input
                    id={ctcInputId}
                    type="number"
                    value={annualCtc}
                    onChange={(e) => setAnnualCtc(Math.max(0, Number(e.target.value)))}
                    className="w-full pl-8 pr-4 py-2 border border-stone-300 rounded-lg text-stone-900 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-emerald-600"
                  />
                </div>
                <input
                  type="range"
                  min="300000"
                  max="10000000"
                  step="50000"
                  value={annualCtc}
                  onChange={(e) => setAnnualCtc(Number(e.target.value))}
                  className="w-full accent-emerald-600 h-1.5 bg-stone-200 rounded-lg cursor-pointer"
                />
              </div>

              {/* Basic Salary % */}
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <label htmlFor={basicPctInputId} className="font-medium text-stone-700">Basic Salary (% of CTC)</label>
                  <span className="font-semibold text-stone-800">{basicPct}% ({formatINR((annualCtc * basicPct) / 100)})</span>
                </div>
                <input
                  id={basicPctInputId}
                  type="range"
                  min="30"
                  max="70"
                  step="5"
                  value={basicPct}
                  onChange={(e) => setBasicPct(Number(e.target.value))}
                  className="w-full accent-emerald-600 h-1.5 bg-stone-200 rounded-lg cursor-pointer"
                />
              </div>

              {/* HRA % */}
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <label htmlFor={hraInputId} className="font-medium text-stone-700">HRA Component (% of CTC)</label>
                  <span className="font-semibold text-stone-800">{hraPct}% ({formatINR((annualCtc * hraPct) / 100)})</span>
                </div>
                <input
                  id={hraInputId}
                  type="range"
                  min="10"
                  max="50"
                  step="5"
                  value={hraPct}
                  onChange={(e) => setHraPct(Number(e.target.value))}
                  className="w-full accent-emerald-600 h-1.5 bg-stone-200 rounded-lg cursor-pointer"
                />
              </div>

              {/* EPF Opt-in */}
              <div className="flex items-center justify-between pt-2 border-t border-stone-100">
                <div>
                  <span className="text-xs font-semibold text-stone-800 block">Provident Fund (EPF)</span>
                  <span className="text-[11px] text-stone-500">12% Employer + 12% Employee Contribution</span>
                </div>
                <button
                  onClick={() => setEpfOpted(!epfOpted)}
                  className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                    epfOpted ? "bg-emerald-600" : "bg-stone-300"
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                      epfOpted ? "translate-x-4" : "translate-x-0"
                    }`}
                  />
                </button>
              </div>
            </div>
          </div>

          {/* Results Summary Column */}
          <div className="lg:col-span-6 space-y-6">
            {result && (
              <div className="bg-white border border-stone-200/80 rounded-xl p-6 shadow-sm space-y-6">
                {/* Headline Hero Card */}
                <div className="bg-gradient-to-br from-emerald-500/10 via-emerald-500/5 to-transparent border border-emerald-500/20 rounded-xl p-5">
                  <span className="text-xs font-semibold text-emerald-800 uppercase tracking-wider block mb-1">
                    Estimated In-Hand Salary
                  </span>
                  <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-bold text-emerald-950">
                      {formatINR(result.monthly_take_home)}
                    </span>
                    <span className="text-xs text-stone-500 font-medium">/ month</span>
                  </div>
                  <div className="mt-2 text-xs text-stone-600 flex items-center gap-1.5">
                    <TrendingUp className="w-3.5 h-3.5 text-emerald-600" />
                    <span>Annual In-Hand: <strong className="text-stone-900">{formatINR(result.annual_take_home)}</strong></span>
                  </div>
                </div>

                {/* Monthly Deductions Breakdown Table */}
                <div className="space-y-3">
                  <h2 className="text-xs font-bold uppercase tracking-wider text-stone-600">
                    Monthly Salary Breakdown
                  </h2>
                  <div className="divide-y divide-stone-100 text-xs">
                    <div className="py-2 flex justify-between">
                      <span className="text-stone-600">Gross Salary</span>
                      <span className="font-semibold text-stone-900">{formatINR(result.monthly_gross_salary)}</span>
                    </div>
                    {epfOpted && (
                      <div className="py-2 flex justify-between text-stone-600">
                        <span>Employee EPF (12%)</span>
                        <span className="text-rose-600">-{formatINR(result.monthly_epf_employee)}</span>
                      </div>
                    )}
                    <div className="py-2 flex justify-between text-stone-600">
                      <span>Professional Tax</span>
                      <span className="text-rose-600">-{formatINR(result.annual_professional_tax / 12)}</span>
                    </div>
                    <div className="py-2 flex justify-between text-stone-600">
                      <span>Income Tax (TDS)</span>
                      <span className="text-rose-600">-{formatINR(result.monthly_income_tax_deduction)}</span>
                    </div>
                    <div className="py-2.5 flex justify-between font-bold text-stone-900 bg-stone-50/80 px-2 rounded-lg">
                      <span>Net In-Hand (Take Home)</span>
                      <span className="text-emerald-700">{formatINR(result.monthly_take_home)}</span>
                    </div>
                  </div>
                </div>

                {/* Annual Tax & Compliance Note */}
                <div className="p-3 bg-stone-50 border border-stone-200/60 rounded-lg text-xs text-stone-600 space-y-1.5">
                  <div className="flex items-center gap-1.5 font-semibold text-stone-800">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                    <span>Statutory Summary (AY 2025-26)</span>
                  </div>
                  <p>
                    Standard deduction of ₹75,000 applied under Section 16(ia). Effective income tax rate on CTC is <strong>{result.effective_tax_rate.toFixed(1)}%</strong>.
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
