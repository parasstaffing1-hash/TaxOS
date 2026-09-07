"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  AlertCircle,
  ArrowLeft,
  Briefcase,
  CheckCircle2,
  HelpCircle,
  Info,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import { API_BASE } from "@/lib/api";

interface RegimeComparisonResponse {
  financial_year: string;
  assessment_year: string;
  gross_total_income: number | string;
  old_regime_deductions: number | string;
  old_regime_taxable_income: number | string;
  old_regime_base_tax: number | string;
  old_regime_rebate_87a: number | string;
  old_regime_surcharge: number | string;
  old_regime_cess: number | string;
  old_regime_total_tax: number | string;
  new_regime_deductions: number | string;
  new_regime_taxable_income: number | string;
  new_regime_base_tax: number | string;
  new_regime_rebate_87a: number | string;
  new_regime_surcharge: number | string;
  new_regime_cess: number | string;
  new_regime_total_tax: number | string;
  recommended_regime: "new" | "old";
  tax_savings: number | string;
  break_even_deductions_needed: number | string;
  summary_explanation: string;
}

const PRESET_SALARIES = [
  { label: "₹6 Lakh", value: 600000 },
  { label: "₹10 Lakh", value: 1000000 },
  { label: "₹15 Lakh", value: 1500000 },
  { label: "₹25 Lakh", value: 2500000 },
  { label: "₹50 Lakh", value: 5000000 },
];

export default function IndiaIncomeTaxCalculatorPage() {
  const [assessmentYear, setAssessmentYear] = useState<"2025-26" | "2024-25">("2025-26");
  const [grossSalary, setGrossSalary] = useState<number>(1200000);
  const [housePropertyLoss, setHousePropertyLoss] = useState<number>(0);
  const [sec80c, setSec80c] = useState<number>(150000);
  const [sec80d, setSec80d] = useState<number>(25000);
  const [sec80ccd1b, setSec80ccd1b] = useState<number>(50000);
  const [otherIncome, setOtherIncome] = useState<number>(0);

  const [comparison, setComparison] = useState<RegimeComparisonResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [activeTooltip, setActiveTooltip] = useState<string | null>(null);

  const fetchCalculation = () => {
    if (grossSalary < 0 || otherIncome < 0) {
      setErrorMessage("Income amounts cannot be negative.");
      setComparison(null);
      setLoading(false);
      return;
    }

    const controller = new AbortController();
    setLoading(true);
    setErrorMessage(null);

    const financialYear = assessmentYear === "2025-26" ? "2024-25" : "2023-24";
    const hpIncome = housePropertyLoss > 0 ? -Math.abs(housePropertyLoss) : 0;

    fetch(`${API_BASE}/india/income-tax/compare-regimes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: controller.signal,
      body: JSON.stringify({
        financial_year: financialYear,
        assessment_year: assessmentYear,
        salary_income: grossSalary,
        house_property_income: hpIncome,
        other_sources_income: otherIncome,
        section_80c: sec80c,
        section_80d_self: sec80d,
        section_80ccd_1b: sec80ccd1b,
        section_80ccd_2: 0,
      }),
    })
      .then(async (response) => {
        if (!response.ok) {
          const errData = await response.json().catch(() => null);
          throw new Error(
            errData?.detail || `Calculation API error (${response.status})`
          );
        }
        return response.json() as Promise<RegimeComparisonResponse>;
      })
      .then((data) => {
        setComparison(data);
        setErrorMessage(null);
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setComparison(null);
        setErrorMessage(
          error instanceof Error
            ? error.message
            : "TaxOS calculation engine is currently unavailable. Please verify backend status."
        );
      })
      .finally(() => {
        setLoading(false);
      });

    return () => controller.abort();
  };

  useEffect(() => {
    const cancel = fetchCalculation();
    return () => {
      if (cancel) cancel();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    assessmentYear,
    grossSalary,
    housePropertyLoss,
    otherIncome,
    sec80c,
    sec80d,
    sec80ccd1b,
  ]);

  const handleReset = () => {
    setGrossSalary(1200000);
    setSec80c(150000);
    setSec80d(25000);
    setSec80ccd1b(50000);
    setHousePropertyLoss(0);
    setOtherIncome(0);
  };

  const newTax = comparison ? Number(comparison.new_regime_total_tax) : 0;
  const oldTax = comparison ? Number(comparison.old_regime_total_tax) : 0;
  const savings = comparison ? Number(comparison.tax_savings) : 0;
  const isNewRecommended = comparison?.recommended_regime === "new";

  const newMonthlyTax = Math.round(newTax / 12);
  const oldMonthlyTax = Math.round(oldTax / 12);

  const totalIncome = grossSalary + otherIncome;
  const newMonthlyTakeHome = Math.round(Math.max(0, totalIncome - newTax) / 12);
  const oldMonthlyTakeHome = Math.round(Math.max(0, totalIncome - oldTax) / 12);

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
            Income Tax Calculator
          </span>
          <span
            className={`hidden sm:inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium ${
              comparison
                ? "bg-[#eaf3eb] text-[#4f6f54]"
                : loading
                ? "bg-[#f5f4f1] text-[#8f8a81]"
                : "bg-[#fdf0ed] text-[#a15c38]"
            }`}
          >
            {comparison && <CheckCircle2 className="h-3 w-3" />}
            {comparison
              ? "Official Tax Engine"
              : loading
              ? "Syncing…"
              : "API Disconnected"}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleReset}
            className="flex items-center gap-1 rounded-lg border border-[#e8e6e1] bg-white px-2.5 py-1 text-xs text-[#78736b] hover:bg-[#faf9f7] transition"
          >
            <RotateCcw className="h-3 w-3" /> Reset
          </button>
        </div>
      </header>

      {/* Main Container */}
      <main className="mx-auto max-w-[1140px] px-4 sm:px-6 py-6 sm:py-8">
        {/* Title and Intro */}
        <div className="mb-6 sm:mb-8">
          <div className="flex items-center gap-2 text-xs font-medium text-[#4f6f54]">
            <span className="inline-block h-2 w-2 rounded-full bg-[#4f6f54]" />
            New Regime (Section 115BAC) vs Old Regime Comparison · AY {assessmentYear}
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight sm:text-3xl text-[#1e221f]">
            India Income Tax Calculator & Regime Planner
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-[#78736b]">
            Accurately calculate your income tax, compare Old vs New Tax Regimes, standard
            deductions, Section 87A rebate, and view your monthly in-hand take-home salary.
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
              onClick={fetchCalculation}
              className="shrink-0 rounded-md bg-[#9d3c26] px-2.5 py-1 text-[11px] font-medium text-white hover:bg-[#832e1c]"
            >
              Retry
            </button>
          </div>
        )}

        {/* Layout: Inputs on Left, Results on Right */}
        <div className="grid gap-6 lg:grid-cols-12">
          {/* Left Column: Inputs (7 cols) */}
          <div className="space-y-5 lg:col-span-7">
            {/* Assessment Year Selection */}
            <div className="rounded-2xl border border-[#e8e6e1] bg-[#faf9f7] p-4 sm:p-5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold uppercase tracking-wider text-[#78736b]">
                  Select Assessment Year (AY)
                </label>
                <span className="text-[11px] text-[#9c978f]">
                  FY {assessmentYear === "2025-26" ? "2024-25" : "2023-24"}
                </span>
              </div>
              <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setAssessmentYear("2025-26")}
                  className={`rounded-xl p-3 text-left transition ${
                    assessmentYear === "2025-26"
                      ? "bg-[#2f3430] text-white shadow-sm"
                      : "border border-[#e0ded9] bg-white text-[#78736b] hover:bg-[#f2f1ed]"
                  }`}
                >
                  <div className="text-xs font-semibold">AY 2025-26 (Current)</div>
                  <div className={`mt-0.5 text-[11px] ${assessmentYear === "2025-26" ? "text-[#d0ded2]" : "text-[#9c978f]"}`}>
                    Budget 2024 Slabs · ₹75,000 Standard Deduction
                  </div>
                </button>
                <button
                  type="button"
                  onClick={() => setAssessmentYear("2024-25")}
                  className={`rounded-xl p-3 text-left transition ${
                    assessmentYear === "2024-25"
                      ? "bg-[#2f3430] text-white shadow-sm"
                      : "border border-[#e0ded9] bg-white text-[#78736b] hover:bg-[#f2f1ed]"
                  }`}
                >
                  <div className="text-xs font-semibold">AY 2024-25 (Previous)</div>
                  <div className={`mt-0.5 text-[11px] ${assessmentYear === "2024-25" ? "text-[#d0ded2]" : "text-[#9c978f]"}`}>
                    Finance Act 2023 · ₹50,000 Standard Deduction
                  </div>
                </button>
              </div>
            </div>

            {/* Income Inputs */}
            <div className="rounded-2xl border border-[#e8e6e1] bg-white p-5 shadow-sm">
              <div className="flex items-center justify-between border-b border-[#f0eee9] pb-3">
                <h2 className="text-sm font-semibold tracking-tight text-[#37352f]">
                  1. Annual Income Details
                </h2>
                <span className="text-xs text-[#9c978f]">Heads of Income</span>
              </div>

              <div className="mt-4 space-y-4">
                {/* Gross Salary Input & Slider */}
                <div>
                  <div className="flex justify-between text-xs">
                    <span className="font-medium text-[#4f4b44]">
                      Annual Gross Salary / CTC
                    </span>
                    <span className="font-semibold text-[#2f3430]">
                      ₹{grossSalary.toLocaleString("en-IN")}
                    </span>
                  </div>
                  <input
                    type="range"
                    min="300000"
                    max="5000000"
                    step="25000"
                    value={grossSalary}
                    onChange={(e) => setGrossSalary(Number(e.target.value))}
                    className="mt-2 w-full accent-[#2f3430] cursor-pointer"
                  />
                  {/* Preset Quick Chips */}
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {PRESET_SALARIES.map((preset) => (
                      <button
                        key={preset.value}
                        type="button"
                        onClick={() => setGrossSalary(preset.value)}
                        className={`rounded-lg px-2.5 py-1 text-[11px] font-medium transition ${
                          grossSalary === preset.value
                            ? "bg-[#2f3430] text-white"
                            : "border border-[#e8e6e1] bg-[#faf9f7] text-[#78736b] hover:bg-[#f0eee9]"
                        }`}
                      >
                        {preset.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Other Income */}
                <div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-medium text-[#4f4b44] flex items-center gap-1">
                      Other Income (Interest, Dividends, Freelance)
                      <button
                        type="button"
                        onClick={() =>
                          setActiveTooltip(
                            activeTooltip === "other" ? null : "other"
                          )
                        }
                        className="text-[#9c978f] hover:text-[#37352f]"
                      >
                        <HelpCircle className="h-3.5 w-3.5" />
                      </button>
                    </span>
                    <span className="font-semibold text-[#2f3430]">
                      ₹{otherIncome.toLocaleString("en-IN")}
                    </span>
                  </div>
                  {activeTooltip === "other" && (
                    <div className="mt-1.5 rounded-lg bg-[#faf9f7] p-2.5 text-[11px] text-[#6b665e] border border-[#e8e6e1]">
                      Include savings account interest, fixed deposit interest, dividends, and freelance income taxed at slab rates.
                    </div>
                  )}
                  <input
                    type="number"
                    min="0"
                    step="5000"
                    value={otherIncome || ""}
                    placeholder="0"
                    onChange={(e) =>
                      setOtherIncome(Math.max(0, Number(e.target.value)))
                    }
                    className="mt-1.5 w-full rounded-xl border border-[#e0ded9] px-3.5 py-2 text-xs text-[#37352f] outline-none transition focus:border-[#2f3430]"
                  />
                </div>
              </div>
            </div>

            {/* Deductions & Exemptions */}
            <div className="rounded-2xl border border-[#e8e6e1] bg-white p-5 shadow-sm">
              <div className="flex items-center justify-between border-b border-[#f0eee9] pb-3">
                <div>
                  <h2 className="text-sm font-semibold tracking-tight text-[#37352f]">
                    2. Deductions & Exemptions
                  </h2>
                  <p className="text-[11px] text-[#78736b]">
                    Applied to Old Regime to reduce your taxable income
                  </p>
                </div>
                <span className="rounded bg-[#f5f4f1] px-2 py-0.5 text-[10px] font-medium text-[#78736b]">
                  Chapter VI-A
                </span>
              </div>

              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                {/* 80C */}
                <div>
                  <label className="text-xs font-medium text-[#4f4b44] flex items-center justify-between">
                    <span>Section 80C (Max ₹1.5L)</span>
                    <span className="text-[10px] text-[#9c978f]">EPF/PPF/ELSS/LIC</span>
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="150000"
                    step="5000"
                    value={sec80c || ""}
                    placeholder="Max 150000"
                    onChange={(e) =>
                      setSec80c(
                        Math.min(150000, Math.max(0, Number(e.target.value)))
                      )
                    }
                    className="mt-1.5 w-full rounded-xl border border-[#e0ded9] px-3.5 py-2 text-xs outline-none transition focus:border-[#2f3430]"
                  />
                </div>

                {/* 80D */}
                <div>
                  <label className="text-xs font-medium text-[#4f4b44] flex items-center justify-between">
                    <span>Section 80D (Health Ins.)</span>
                    <span className="text-[10px] text-[#9c978f]">Self & Parents</span>
                  </label>
                  <input
                    type="number"
                    min="0"
                    step="5000"
                    value={sec80d || ""}
                    placeholder="e.g. 25000"
                    onChange={(e) =>
                      setSec80d(Math.max(0, Number(e.target.value)))
                    }
                    className="mt-1.5 w-full rounded-xl border border-[#e0ded9] px-3.5 py-2 text-xs outline-none transition focus:border-[#2f3430]"
                  />
                </div>

                {/* 80CCD(1B) NPS */}
                <div>
                  <label className="text-xs font-medium text-[#4f4b44] flex items-center justify-between">
                    <span>Section 80CCD(1B) (NPS)</span>
                    <span className="text-[10px] text-[#9c978f]">Max ₹50,000</span>
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="50000"
                    step="5000"
                    value={sec80ccd1b || ""}
                    placeholder="Max 50000"
                    onChange={(e) =>
                      setSec80ccd1b(
                        Math.min(50000, Math.max(0, Number(e.target.value)))
                      )
                    }
                    className="mt-1.5 w-full rounded-xl border border-[#e0ded9] px-3.5 py-2 text-xs outline-none transition focus:border-[#2f3430]"
                  />
                </div>

                {/* Home Loan Loss Section 24(b) */}
                <div>
                  <label className="text-xs font-medium text-[#4f4b44] flex items-center justify-between">
                    <span>Home Loan Interest (24b)</span>
                    <span className="text-[10px] text-[#9c978f]">Max ₹2,00,000</span>
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="200000"
                    step="5000"
                    value={housePropertyLoss || ""}
                    placeholder="Max 200000"
                    onChange={(e) =>
                      setHousePropertyLoss(
                        Math.min(200000, Math.max(0, Number(e.target.value)))
                      )
                    }
                    className="mt-1.5 w-full rounded-xl border border-[#e0ded9] px-3.5 py-2 text-xs outline-none transition focus:border-[#2f3430]"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Comparative Results (5 cols) */}
          <div className="space-y-5 lg:col-span-5">
            {/* Recommendation Banner */}
            <div className="rounded-2xl border border-[#dbe6dc] bg-[#f5f9f5] p-5 shadow-sm">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[#4f6f54]">
                <Sparkles className="h-4 w-4" /> Optimal Tax Recommendation
              </div>
              <div className="mt-2 text-xl sm:text-2xl font-bold tracking-tight text-[#2f3430]">
                {comparison
                  ? isNewRecommended
                    ? "New Tax Regime (Section 115BAC)"
                    : "Old Tax Regime"
                  : loading
                  ? "Calculating Optimal Regime…"
                  : "Calculation Pending"}
              </div>
              <p className="mt-1.5 text-xs text-[#5f6b61] leading-relaxed">
                {comparison ? (
                  <>
                    <span>{comparison.summary_explanation}</span>
                    {savings > 0 && (
                      <span className="mt-1.5 block font-semibold text-[#2f3430]">
                        Net annual tax savings: ₹{savings.toLocaleString("en-IN")}
                      </span>
                    )}
                  </>
                ) : loading ? (
                  "Analyzing tax slabs with official statutory rules…"
                ) : (
                  "Enter your income to compare regimes."
                )}
              </p>
            </div>

            {/* Monthly Take-Home & Tax Highlight Cards */}
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-2xl border border-[#e8e6e1] bg-white p-4 shadow-sm">
                <div className="flex items-center gap-1.5 text-[11px] font-medium text-[#78736b]">
                  <TrendingUp className="h-3.5 w-3.5 text-[#4f6f54]" /> Monthly In-Hand
                </div>
                <div className="mt-1.5 text-lg sm:text-xl font-bold text-[#2f3430]">
                  {comparison
                    ? `₹${(isNewRecommended ? newMonthlyTakeHome : oldMonthlyTakeHome).toLocaleString("en-IN")}`
                    : "—"}
                </div>
                <span className="text-[10px] text-[#9c978f]">
                  Under {isNewRecommended ? "New Regime" : "Old Regime"}
                </span>
              </div>

              <div className="rounded-2xl border border-[#e8e6e1] bg-white p-4 shadow-sm">
                <div className="flex items-center gap-1.5 text-[11px] font-medium text-[#78736b]">
                  <Briefcase className="h-3.5 w-3.5 text-[#a15c38]" /> Monthly Tax
                </div>
                <div className="mt-1.5 text-lg sm:text-xl font-bold text-[#2f3430]">
                  {comparison
                    ? `₹${(isNewRecommended ? newMonthlyTax : oldMonthlyTax).toLocaleString("en-IN")}`
                    : "—"}
                </div>
                <span className="text-[10px] text-[#9c978f]">
                  ₹{Math.round(isNewRecommended ? newTax : oldTax).toLocaleString("en-IN")} annual
                </span>
              </div>
            </div>

            {/* Side by Side Comparison Table */}
            <div className="overflow-hidden rounded-2xl border border-[#e8e6e1] bg-white shadow-sm">
              <div className="grid grid-cols-2 border-b border-[#e8e6e1] bg-[#faf9f7] text-center text-xs font-semibold text-[#78736b]">
                <div className="py-3 border-r border-[#e8e6e1] flex items-center justify-center gap-1.5">
                  New Regime (115BAC)
                  {isNewRecommended && (
                    <span className="rounded bg-[#eaf3eb] px-1.5 py-0.5 text-[9px] font-bold text-[#4f6f54]">
                      BETTER
                    </span>
                  )}
                </div>
                <div className="py-3 flex items-center justify-center gap-1.5">
                  Old Regime
                  {!isNewRecommended && comparison && (
                    <span className="rounded bg-[#eaf3eb] px-1.5 py-0.5 text-[9px] font-bold text-[#4f6f54]">
                      BETTER
                    </span>
                  )}
                </div>
              </div>

              <div className="divide-y divide-[#f7f6f3] text-xs">
                {/* Total Deductions */}
                <div className="grid grid-cols-2 p-3 text-center">
                  <div className="border-r border-[#f7f6f3]">
                    <span className="block text-[10px] text-[#9c978f]">
                      Total Deductions
                    </span>
                    <span className="font-semibold text-[#2f3430]">
                      {comparison
                        ? `₹${Number(
                            comparison.new_regime_deductions
                          ).toLocaleString("en-IN")}`
                        : "—"}
                    </span>
                  </div>
                  <div>
                    <span className="block text-[10px] text-[#9c978f]">
                      Total Deductions
                    </span>
                    <span className="font-semibold text-[#2f3430]">
                      {comparison
                        ? `₹${Number(
                            comparison.old_regime_deductions
                          ).toLocaleString("en-IN")}`
                        : "—"}
                    </span>
                  </div>
                </div>

                {/* Taxable Income */}
                <div className="grid grid-cols-2 p-3 text-center">
                  <div className="border-r border-[#f7f6f3]">
                    <span className="block text-[10px] text-[#9c978f]">
                      Taxable Income
                    </span>
                    <span className="font-semibold text-[#2f3430]">
                      {comparison
                        ? `₹${Number(
                            comparison.new_regime_taxable_income
                          ).toLocaleString("en-IN")}`
                        : "—"}
                    </span>
                  </div>
                  <div>
                    <span className="block text-[10px] text-[#9c978f]">
                      Taxable Income
                    </span>
                    <span className="font-semibold text-[#2f3430]">
                      {comparison
                        ? `₹${Number(
                            comparison.old_regime_taxable_income
                          ).toLocaleString("en-IN")}`
                        : "—"}
                    </span>
                  </div>
                </div>

                {/* Section 87A Rebate */}
                <div className="grid grid-cols-2 p-3 text-center">
                  <div className="border-r border-[#f7f6f3]">
                    <span className="block text-[10px] text-[#9c978f]">
                      Section 87A Rebate
                    </span>
                    <span className="font-semibold text-[#4f6f54]">
                      {comparison
                        ? Number(comparison.new_regime_rebate_87a) > 0
                          ? `-₹${Number(
                              comparison.new_regime_rebate_87a
                            ).toLocaleString("en-IN")}`
                          : "₹0"
                        : "—"}
                    </span>
                  </div>
                  <div>
                    <span className="block text-[10px] text-[#9c978f]">
                      Section 87A Rebate
                    </span>
                    <span className="font-semibold text-[#4f6f54]">
                      {comparison
                        ? Number(comparison.old_regime_rebate_87a) > 0
                          ? `-₹${Number(
                              comparison.old_regime_rebate_87a
                            ).toLocaleString("en-IN")}`
                          : "₹0"
                        : "—"}
                    </span>
                  </div>
                </div>

                {/* Total Tax Payable Highlight */}
                <div className="grid grid-cols-2 p-3 text-center bg-[#faf9f7]">
                  <div className="border-r border-[#e8e6e1]">
                    <span className="block text-[10px] text-[#78736b]">
                      Total Annual Tax
                    </span>
                    <span className="text-base font-bold text-[#2f3430]">
                      {comparison ? `₹${newTax.toLocaleString("en-IN")}` : "—"}
                    </span>
                  </div>
                  <div>
                    <span className="block text-[10px] text-[#78736b]">
                      Total Annual Tax
                    </span>
                    <span className="text-base font-bold text-[#2f3430]">
                      {comparison ? `₹${oldTax.toLocaleString("en-IN")}` : "—"}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Break-even Insights */}
            {comparison && Number(comparison.break_even_deductions_needed) > 0 && (
              <div className="rounded-2xl border border-[#e8e6e1] bg-white p-4 text-xs text-[#5f5b53] shadow-sm">
                <div className="flex items-center gap-1.5 font-semibold text-[#37352f]">
                  <Info className="h-4 w-4 text-[#78736b]" /> Break-even Insight
                </div>
                <p className="mt-1.5 leading-relaxed text-[#78736b]">
                  You would need total deductions of at least{" "}
                  <strong className="text-[#2f3430]">
                    ₹{Number(comparison.break_even_deductions_needed).toLocaleString("en-IN")}
                  </strong>{" "}
                  for the Old Regime to match the New Regime.
                </p>
              </div>
            )}

            {/* Statutory Law Rules & Explanations */}
            <div className="rounded-2xl border border-[#e8e6e1] bg-white p-4 shadow-sm">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-[#37352f]">
                <ShieldCheck className="h-4 w-4 text-[#4f6f54]" /> Statutory Sourcing & Rules
              </div>
              <ul className="mt-2 space-y-1.5 text-[11px] text-[#78736b]">
                <li className="flex items-center gap-1.5">
                  <CheckCircle2 className="h-3 w-3 text-[#4f6f54] shrink-0" />
                  <span>
                    <strong>New Regime:</strong> Slabs u/s 115BAC(1A) with ₹75k std. deduction for AY {assessmentYear}
                  </span>
                </li>
                <li className="flex items-center gap-1.5">
                  <CheckCircle2 className="h-3 w-3 text-[#4f6f54] shrink-0" />
                  <span>
                    <strong>Section 87A:</strong> Full rebate up to ₹7 Lakhs taxable income under New Regime
                  </span>
                </li>
                <li className="flex items-center gap-1.5">
                  <CheckCircle2 className="h-3 w-3 text-[#4f6f54] shrink-0" />
                  <span>
                    <strong>Cess:</strong> 4% Health & Education Cess applied strictly per Finance Act rules
                  </span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
