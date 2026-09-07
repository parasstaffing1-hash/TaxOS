"use client";

import Link from "next/link";
import { useEffect, useState, useId } from "react";
import {
  AlertCircle,
  ArrowLeft,
  Briefcase,
  CheckCircle2,
  HelpCircle,
  ShieldCheck,
  TrendingUp,
} from "lucide-react";
import { API_BASE } from "@/lib/api";

interface SalaryBreakdownResponse {
  annual_ctc: number;
  basic_salary: number;
  hra: number;
  special_allowance: number;
  other_allowances: number;
  bonus: number;
  employer_epf: number;
  employer_nps: number;
  gratuity_provision: number;
  gross_salary: number;
  employee_epf: number;
  professional_tax: number;
  annual_income_tax: number;
  total_employee_deductions: number;
  annual_take_home: number;
  monthly_take_home: number;
  monthly_gross_salary: number;
  applied_regime: string;
  hra_exemption_amount: number;
}

export default function IndiaSalaryCalculatorPage() {
  const ctcInputId = useId();
  const basicPctInputId = useId();
  const hraInputId = useId();

  const [annualCtc, setAnnualCtc] = useState<number>(1500000);
  const [basicPct, setBasicPct] = useState<number>(40);
  const [hraPct, setHraPct] = useState<number>(20);
  const [regime, setRegime] = useState<"new" | "old">("new");
  const [result, setResult] = useState<SalaryBreakdownResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const calculateSalary = () => {
    if (annualCtc < 0) {
      setErrorMessage("CTC amount cannot be negative.");
      setResult(null);
      setLoading(false);
      return;
    }

    const controller = new AbortController();
    setLoading(true);
    setErrorMessage(null);

    const payload = {
      annual_ctc: annualCtc,
      basic_percentage: basicPct / 100,
      hra_percentage: hraPct / 100,
      is_metro_city: true,
      actual_rent_paid_annually: 0,
      lta_claimed: 0,
      employer_nps_percentage: 0,
      professional_tax_annual: 2400,
      bonus_annual: 0,
      food_other_allowances: 0,
    };

    fetch(`${API_BASE}/india/salary/take-home?regime=${regime}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: controller.signal,
      body: JSON.stringify(payload),
    })
      .then(async (res) => {
        if (!res.ok) {
          const err = await res.json().catch(() => null);
          throw new Error(err?.detail || `Calculation API returned status ${res.status}`);
        }
        return res.json() as Promise<SalaryBreakdownResponse>;
      })
      .then((data) => {
        setResult(data);
        setErrorMessage(null);
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setResult(null);
        setErrorMessage(
          error instanceof Error
            ? error.message
            : "TaxOS calculation engine is currently unavailable."
        );
      })
      .finally(() => {
        setLoading(false);
      });

    return () => controller.abort();
  };

  useEffect(() => {
    const cancel = calculateSalary();
    return () => {
      if (cancel) cancel();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [annualCtc, basicPct, hraPct, regime]);

  const formatINR = (val: number) =>
    new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(Math.round(val));

  return (
    <div className="min-h-screen bg-[#fffefa] text-[#37352f]">
      {/* Header */}
      <header className="sticky top-0 z-20 flex h-14 items-center justify-between border-b border-[#f0eee9] bg-white/90 px-4 sm:px-6 backdrop-blur-md">
        <div className="flex items-center gap-2 sm:gap-3">
          <Link
            href="/tax"
            className="flex items-center gap-1.5 text-xs text-[#78736b] hover:text-[#37352f] transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" /> All Tax Tools
          </Link>
          <span className="text-[#d2cfc8]">/</span>
          <span className="text-xs font-semibold text-[#37352f]">
            Salary & Take-Home Calculator
          </span>
          <span
            className={`hidden sm:inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium ${
              result
                ? "bg-[#eaf3eb] text-[#4f6f54]"
                : loading
                ? "bg-[#f5f4f1] text-[#8f8a81]"
                : "bg-[#fdf0ed] text-[#a15c38]"
            }`}
          >
            {result && <CheckCircle2 className="h-3 w-3" />}
            {result
              ? "Official Tax Engine"
              : loading
              ? "Syncing…"
              : "API Disconnected"}
          </span>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 sm:px-6 py-6 sm:py-8">
        {/* Navigation & Header */}
        <div className="mb-6 sm:mb-8">
          <div className="flex items-center gap-2 text-xs font-medium text-[#4f6f54]">
            <span className="inline-block h-2 w-2 rounded-full bg-[#4f6f54]" />
            CTC to In-Hand Salary Breakdown Engine
          </div>
          <h1 className="mt-1 text-2xl sm:text-3xl font-bold tracking-tight text-[#1e221f]">
            India Salary & Take-Home Pay Calculator
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-[#78736b]">
            Accurate CTC to Monthly In-Hand Salary Breakdown with EPF, Professional Tax,
            and Income Tax Deductions.
          </p>
        </div>

        {/* Error Alert */}
        {errorMessage && (
          <div className="mb-6 flex items-start justify-between gap-3 rounded-xl border border-[#f3d0c9] bg-[#fff5f3] p-4 text-xs text-[#9d3c26]">
            <div className="flex items-start gap-2">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              <div>
                <span className="font-semibold">Calculation Engine Notice:</span>{" "}
                {errorMessage}
              </div>
            </div>
            <button
              type="button"
              onClick={calculateSalary}
              className="shrink-0 rounded-md bg-[#9d3c26] px-2.5 py-1 text-[11px] font-medium text-white hover:bg-[#832e1c]"
            >
              Retry
            </button>
          </div>
        )}

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Controls Column */}
          <div className="lg:col-span-6 space-y-5">
            <div className="bg-white border border-[#e8e6e1] rounded-2xl p-5 shadow-sm space-y-5">
              <div className="flex items-center justify-between border-b border-[#f0eee9] pb-3">
                <span className="text-sm font-semibold text-[#37352f] flex items-center gap-1.5">
                  <Briefcase className="w-4 h-4 text-[#4f6f54]" />
                  CTC & Salary Structure
                </span>
                <div className="flex items-center gap-1 bg-[#f5f4f1] p-0.5 rounded-lg text-xs">
                  <button
                    type="button"
                    onClick={() => setRegime("new")}
                    className={`px-2.5 py-1 rounded-md transition-all font-medium ${
                      regime === "new"
                        ? "bg-white text-[#2f3430] shadow-sm font-semibold"
                        : "text-[#78736b] hover:text-[#2f3430]"
                    }`}
                  >
                    New Regime (115BAC)
                  </button>
                  <button
                    type="button"
                    onClick={() => setRegime("old")}
                    className={`px-2.5 py-1 rounded-md transition-all font-medium ${
                      regime === "old"
                        ? "bg-white text-[#2f3430] shadow-sm font-semibold"
                        : "text-[#78736b] hover:text-[#2f3430]"
                    }`}
                  >
                    Old Regime
                  </button>
                </div>
              </div>

              {/* Annual CTC Input */}
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <label htmlFor={ctcInputId} className="font-medium text-[#4f4b44]">
                    Annual Cost to Company (CTC)
                  </label>
                  <span className="font-bold text-[#4f6f54]">{formatINR(annualCtc)}</span>
                </div>
                <div className="relative">
                  <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#9c978f] text-sm font-semibold">
                    ₹
                  </span>
                  <input
                    id={ctcInputId}
                    type="number"
                    min="0"
                    step="50000"
                    value={annualCtc || ""}
                    onChange={(e) => setAnnualCtc(Math.max(0, Number(e.target.value)))}
                    className="w-full pl-8 pr-4 py-2 border border-[#e0ded9] rounded-xl text-[#37352f] text-xs font-medium outline-none focus:border-[#2f3430]"
                  />
                </div>
                <input
                  type="range"
                  min="300000"
                  max="10000000"
                  step="50000"
                  value={annualCtc}
                  onChange={(e) => setAnnualCtc(Number(e.target.value))}
                  className="w-full accent-[#2f3430] cursor-pointer"
                />
              </div>

              {/* Basic Salary % */}
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <label htmlFor={basicPctInputId} className="font-medium text-[#4f4b44]">
                    Basic Salary (% of CTC)
                  </label>
                  <span className="font-semibold text-[#2f3430]">
                    {basicPct}% ({formatINR((annualCtc * basicPct) / 100)})
                  </span>
                </div>
                <input
                  id={basicPctInputId}
                  type="range"
                  min="30"
                  max="70"
                  step="5"
                  value={basicPct}
                  onChange={(e) => setBasicPct(Number(e.target.value))}
                  className="w-full accent-[#2f3430] cursor-pointer"
                />
              </div>

              {/* HRA % */}
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <label htmlFor={hraInputId} className="font-medium text-[#4f4b44]">
                    HRA Component (% of CTC)
                  </label>
                  <span className="font-semibold text-[#2f3430]">
                    {hraPct}% ({formatINR((annualCtc * hraPct) / 100)})
                  </span>
                </div>
                <input
                  id={hraInputId}
                  type="range"
                  min="10"
                  max="50"
                  step="5"
                  value={hraPct}
                  onChange={(e) => setHraPct(Number(e.target.value))}
                  className="w-full accent-[#2f3430] cursor-pointer"
                />
              </div>
            </div>
          </div>

          {/* Results Summary Column */}
          <div className="lg:col-span-6 space-y-5">
            {result ? (
              <div className="bg-white border border-[#e8e6e1] rounded-2xl p-5 shadow-sm space-y-5">
                {/* Headline Hero Card */}
                <div className="bg-[#f5f9f5] border border-[#dbe6dc] rounded-2xl p-5">
                  <span className="text-xs font-semibold text-[#4f6f54] uppercase tracking-wider block mb-1">
                    Estimated In-Hand Salary
                  </span>
                  <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-bold text-[#2f3430]">
                      {formatINR(Number(result.monthly_take_home))}
                    </span>
                    <span className="text-xs text-[#78736b] font-medium">/ month</span>
                  </div>
                  <div className="mt-2 text-xs text-[#5f6b61] flex items-center gap-1.5">
                    <TrendingUp className="w-3.5 h-3.5 text-[#4f6f54]" />
                    <span>
                      Annual In-Hand:{" "}
                      <strong className="text-[#2f3430]">
                        {formatINR(Number(result.annual_take_home))}
                      </strong>
                    </span>
                  </div>
                </div>

                {/* Monthly Deductions Breakdown Table */}
                <div className="space-y-3">
                  <h2 className="text-xs font-bold uppercase tracking-wider text-[#78736b]">
                    Monthly Paycheck Breakdown
                  </h2>
                  <div className="divide-y divide-[#f7f6f3] text-xs">
                    <div className="py-2 flex justify-between">
                      <span className="text-[#78736b]">Monthly Gross Salary</span>
                      <span className="font-semibold text-[#2f3430]">
                        {formatINR(Number(result.monthly_gross_salary))}
                      </span>
                    </div>
                    <div className="py-2 flex justify-between text-[#78736b]">
                      <span className="flex items-center gap-1">
                        Employee EPF (12% Basic)
                        <HelpCircle className="h-3 w-3 text-[#9c978f]" />
                      </span>
                      <span className="text-[#a15c38]">
                        -{formatINR(Number(result.employee_epf) / 12)}
                      </span>
                    </div>
                    <div className="py-2 flex justify-between text-[#78736b]">
                      <span>Professional Tax</span>
                      <span className="text-[#a15c38]">
                        -{formatINR(Number(result.professional_tax) / 12)}
                      </span>
                    </div>
                    <div className="py-2 flex justify-between text-[#78736b]">
                      <span>Income Tax TDS (Est.)</span>
                      <span className="text-[#a15c38]">
                        -{formatINR(Number(result.annual_income_tax) / 12)}
                      </span>
                    </div>
                    <div className="py-2.5 flex justify-between font-bold text-[#2f3430] bg-[#faf9f7] px-3 rounded-xl">
                      <span>Net Monthly In-Hand</span>
                      <span className="text-[#4f6f54]">
                        {formatINR(Number(result.monthly_take_home))}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Annual Retirals & Tax Summary */}
                <div className="p-4 bg-[#faf9f7] border border-[#e8e6e1] rounded-xl text-xs text-[#78736b] space-y-1.5">
                  <div className="flex items-center gap-1.5 font-semibold text-[#2f3430]">
                    <ShieldCheck className="w-4 h-4 text-[#4f6f54]" />
                    <span>Statutory Tax Engine Summary</span>
                  </div>
                  <p>
                    Employer EPF of {formatINR(Number(result.employer_epf))} and gratuity provision
                    are accounted for in your CTC. Standard deduction u/s 16(ia) is applied.
                  </p>
                </div>
              </div>
            ) : loading ? (
              <div className="bg-white border border-[#e8e6e1] rounded-2xl p-8 text-center text-xs text-[#78736b] shadow-sm">
                Calculating salary breakdown…
              </div>
            ) : null}
          </div>
        </div>
      </main>
    </div>
  );
}
