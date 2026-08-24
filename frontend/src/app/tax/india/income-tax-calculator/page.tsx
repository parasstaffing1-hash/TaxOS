"use client";

import Link from "next/link";
import { useEffect, useState, useMemo } from "react";
import {
  ArrowLeft,
  RotateCcw,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { API_BASE } from "@/lib/api";

interface BackendComparison {
  old_regime_taxable_income: number;
  old_regime_base_tax: number;
  old_regime_rebate_87a: number;
  old_regime_cess: number;
  old_regime_total_tax: number;
  new_regime_taxable_income: number;
  new_regime_base_tax: number;
  new_regime_rebate_87a: number;
  new_regime_cess: number;
  new_regime_total_tax: number;
  recommended_regime: "old" | "new";
  tax_savings: number;
}

export default function IndiaIncomeTaxCalculatorPage() {
  const [assessmentYear, setAssessmentYear] = useState<"2025-26" | "2024-25">("2025-26");
  const [grossSalary, setGrossSalary] = useState<number>(1200000);
  const [housePropertyLoss, setHousePropertyLoss] = useState<number>(0);
  const [sec80c, setSec80c] = useState<number>(150000);
  const [sec80d, setSec80d] = useState<number>(25000);
  const [sec80ccd1b, setSec80ccd1b] = useState<number>(50000);
  const employerNps = 0;
  const [otherIncome, setOtherIncome] = useState<number>(0);

  // Dynamic calculation logic using exact Indian statutory rules (matching the backend engine)
  const calculation = useMemo(() => {
    // 1. New Regime Calculation
    const stdDedNew = assessmentYear === "2025-26" ? 75000 : 50000;
    const netSalaryNew = Math.max(0, grossSalary - stdDedNew);
    const gtiNew = netSalaryNew + otherIncome;
    // Only 80CCD(2) Employer NPS is allowed in New Regime
    const taxableNew = Math.max(0, gtiNew - employerNps);

    // New Slabs (AY 2025-26 vs AY 2024-25)
    let taxNew = 0;
    if (assessmentYear === "2025-26") {
      // 0-3L: 0%, 3-7L: 5%, 7-10L: 10%, 10-12L: 15%, 12-15L: 20%, >15L: 30%
      if (taxableNew > 1500000) {
        taxNew = 20000 + 30000 + 30000 + 60000 + (taxableNew - 1500000) * 0.3;
      } else if (taxableNew > 1200000) {
        taxNew = 20000 + 30000 + 30000 + (taxableNew - 1200000) * 0.2;
      } else if (taxableNew > 1000000) {
        taxNew = 20000 + 30000 + (taxableNew - 1000000) * 0.15;
      } else if (taxableNew > 700000) {
        taxNew = 20000 + (taxableNew - 700000) * 0.1;
      } else if (taxableNew > 300000) {
        taxNew = (taxableNew - 300000) * 0.05;
      }
    } else {
      // AY 2024-25 Slabs: 0-3L: 0, 3-6L: 5%, 6-9L: 10%, 9-12L: 15%, 12-15L: 20%, >15L: 30%
      if (taxableNew > 1500000) {
        taxNew = 15000 + 30000 + 45000 + 60000 + (taxableNew - 1500000) * 0.3;
      } else if (taxableNew > 1200000) {
        taxNew = 15000 + 30000 + 45000 + (taxableNew - 1200000) * 0.2;
      } else if (taxableNew > 900000) {
        taxNew = 15000 + 30000 + (taxableNew - 900000) * 0.15;
      } else if (taxableNew > 600000) {
        taxNew = 15000 + (taxableNew - 600000) * 0.1;
      } else if (taxableNew > 300000) {
        taxNew = (taxableNew - 300000) * 0.05;
      }
    }

    // 87A Rebate & Marginal Relief in New Regime
    let rebate87aNew = 0;
    if (taxableNew <= 700000) {
      rebate87aNew = taxNew;
      taxNew = 0;
    } else if (taxableNew <= 727777 && taxNew > (taxableNew - 700000)) {
      // Marginal Relief: Tax payable cannot exceed excess income over 7L
      const excessIncome = taxableNew - 700000;
      rebate87aNew = taxNew - excessIncome;
      taxNew = excessIncome;
    }

    const cessNew = taxNew * 0.04;
    const totalTaxNew = Math.round(taxNew + cessNew);

    // 2. Old Regime Calculation
    const stdDedOld = 50000;
    const netSalaryOld = Math.max(0, grossSalary - stdDedOld);
    const effectiveHpLoss = Math.min(200000, housePropertyLoss);
    const gtiOld = netSalaryOld - effectiveHpLoss + otherIncome;

    const eligible80c = Math.min(150000, sec80c);
    const eligible80d = Math.min(75000, sec80d);
    const eligible80ccd1b = Math.min(50000, sec80ccd1b);
    const totalDeductionsOld = eligible80c + eligible80d + eligible80ccd1b + employerNps;
    const taxableOld = Math.max(0, gtiOld - totalDeductionsOld);

    let taxOld = 0;
    if (taxableOld > 1000000) {
      taxOld = 12500 + 100000 + (taxableOld - 1000000) * 0.3;
    } else if (taxableOld > 500000) {
      taxOld = 12500 + (taxableOld - 500000) * 0.2;
    } else if (taxableOld > 250000) {
      taxOld = (taxableOld - 250000) * 0.05;
    }

    let rebate87aOld = 0;
    if (taxableOld <= 500000) {
      rebate87aOld = taxOld;
      taxOld = 0;
    }

    const cessOld = taxOld * 0.04;
    const totalTaxOld = Math.round(taxOld + cessOld);

    const isNewBetter = totalTaxNew <= totalTaxOld;
    const savings = Math.abs(totalTaxOld - totalTaxNew);

    return {
      newRegime: {
        stdDeduction: stdDedNew,
        taxableIncome: taxableNew,
        baseTax: taxNew + rebate87aNew,
        rebate87a: rebate87aNew,
        cess: cessNew,
        totalTax: totalTaxNew,
      },
      oldRegime: {
        stdDeduction: stdDedOld,
        totalDeductions: totalDeductionsOld,
        taxableIncome: taxableOld,
        baseTax: taxOld + rebate87aOld,
        rebate87a: rebate87aOld,
        cess: cessOld,
        totalTax: totalTaxOld,
      },
      recommendedRegime: isNewBetter ? "New Tax Regime" : "Old Tax Regime",
      savings,
    };
  }, [
    assessmentYear,
    grossSalary,
    housePropertyLoss,
    sec80c,
    sec80d,
    sec80ccd1b,
    employerNps,
    otherIncome,
  ]);

  const [backendComparison, setBackendComparison] = useState<BackendComparison | null>(null);
  const [backendState, setBackendState] = useState<"idle" | "loading" | "ready" | "error">("idle");

  useEffect(() => {
    const controller = new AbortController();
    setBackendState("loading");
    const financialYear = assessmentYear === "2025-26" ? "2024-25" : "2023-24";
    fetch(`${API_BASE}/india/income-tax/compare-regimes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: controller.signal,
      body: JSON.stringify({
        financial_year: financialYear,
        assessment_year: assessmentYear,
        salary_income: grossSalary,
        house_property_income: housePropertyLoss,
        other_sources_income: otherIncome,
        section_80c: sec80c,
        section_80d_self: sec80d,
        section_80ccd_1b: sec80ccd1b,
        section_80ccd_2: employerNps,
      }),
    })
      .then(async (response) => {
        if (!response.ok) throw new Error(`Tax API request failed (${response.status})`);
        return response.json() as Promise<BackendComparison>;
      })
      .then((result) => {
        setBackendComparison(result);
        setBackendState("ready");
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setBackendComparison(null);
        setBackendState("error");
      });
    return () => controller.abort();
  }, [assessmentYear, grossSalary, housePropertyLoss, otherIncome, sec80c, sec80d, sec80ccd1b, employerNps]);

  const displayCalculation = useMemo(() => {
    if (!backendComparison) return calculation;
    return {
      ...calculation,
      recommendedRegime: backendComparison.recommended_regime === "new" ? "New Tax Regime" : "Old Tax Regime",
      savings: Number(backendComparison.tax_savings),
      newRegime: {
        ...calculation.newRegime,
        taxableIncome: Number(backendComparison.new_regime_taxable_income),
        baseTax: Number(backendComparison.new_regime_base_tax),
        rebate87a: Number(backendComparison.new_regime_rebate_87a),
        cess: Number(backendComparison.new_regime_cess),
        totalTax: Number(backendComparison.new_regime_total_tax),
      },
      oldRegime: {
        ...calculation.oldRegime,
        taxableIncome: Number(backendComparison.old_regime_taxable_income),
        baseTax: Number(backendComparison.old_regime_base_tax),
        rebate87a: Number(backendComparison.old_regime_rebate_87a),
        cess: Number(backendComparison.old_regime_cess),
        totalTax: Number(backendComparison.old_regime_total_tax),
      },
    };
  }, [backendComparison, calculation]);

  return (
    <div className="min-h-screen bg-[#fffefa] text-[#37352f]">
      {/* Header */}
      <header className="sticky top-0 z-20 flex h-14 items-center justify-between border-b border-[#f0eee9] bg-white/90 px-6 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <Link href="/tax" className="flex items-center gap-1.5 text-xs text-[#78736b] hover:text-[#37352f]">
            <ArrowLeft className="h-3.5 w-3.5" /> All Tools
          </Link>
          <span className="text-[#d2cfc8]">/</span>
          <span className="text-xs font-semibold text-[#37352f]">India Income Tax Calculator</span>
          <span className={`hidden rounded-full px-2 py-0.5 text-[10px] font-medium sm:inline ${
            backendState === "ready"
              ? "bg-[#eaf3eb] text-[#4f6f54]"
              : backendState === "error"
                ? "bg-[#fdf0ed] text-[#a15c38]"
                : "bg-[#f5f4f1] text-[#8f8a81]"
          }`}>
            {backendState === "ready" ? "API verified" : backendState === "loading" ? "Syncing…" : "Local preview"}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => {
              setGrossSalary(1200000);
              setSec80c(150000);
              setSec80d(25000);
              setSec80ccd1b(50000);
              setHousePropertyLoss(0);
            }}
            className="flex items-center gap-1 rounded-md border border-[#e8e6e1] bg-white px-2.5 py-1 text-xs text-[#78736b] hover:bg-[#faf9f7]"
          >
            <RotateCcw className="h-3 w-3" /> Reset
          </button>
        </div>
      </header>

      {/* Main Container */}
      <main className="mx-auto max-w-[1140px] px-6 py-8">
        {/* Title */}
        <div className="mb-8">
          <div className="flex items-center gap-2 text-xs font-medium text-[#6f9476]">
            <span className="inline-block h-2 w-2 rounded-full bg-[#6f9476]" />
            Section 115BAC & Old Regime Engine · AY {assessmentYear}
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight sm:text-3xl">
            India Income Tax & Regime Comparator
          </h1>
          <p className="mt-1 text-xs text-[#78736b]">
            Simulate your income, compare New vs Old tax slabs, standard deductions, Section 87A rebate, and marginal relief.
          </p>
        </div>

        {/* Layout: Inputs on Left, Results on Right */}
        <div className="grid gap-8 lg:grid-cols-12">
          {/* Left Column: Inputs (7 cols) */}
          <div className="space-y-6 lg:col-span-7">
            {/* Assessment Year Toggle */}
            <div className="rounded-xl border border-[#e8e6e1] bg-[#faf9f7] p-4">
              <label className="text-xs font-semibold uppercase tracking-wider text-[#78736b]">
                Assessment Year (AY)
              </label>
              <div className="mt-2 flex gap-2">
                <button
                  type="button"
                  onClick={() => setAssessmentYear("2025-26")}
                  className={`flex-1 rounded-lg py-2 text-xs font-medium transition ${
                    assessmentYear === "2025-26"
                      ? "bg-[#2f3430] text-white shadow-sm"
                      : "border border-[#e0ded9] bg-white text-[#78736b] hover:bg-[#f2f1ed]"
                  }`}
                >
                  AY 2025-26 (Budget 2024 Slabs · ₹75k S/D)
                </button>
                <button
                  type="button"
                  onClick={() => setAssessmentYear("2024-25")}
                  className={`flex-1 rounded-lg py-2 text-xs font-medium transition ${
                    assessmentYear === "2024-25"
                      ? "bg-[#2f3430] text-white shadow-sm"
                      : "border border-[#e0ded9] bg-white text-[#78736b] hover:bg-[#f2f1ed]"
                  }`}
                >
                  AY 2024-25 (Finance Act 2023 · ₹50k S/D)
                </button>
              </div>
            </div>

            {/* Income Inputs */}
            <div className="rounded-xl border border-[#e8e6e1] bg-white p-5 shadow-sm">
              <h2 className="text-sm font-semibold tracking-tight text-[#37352f]">
                1. Gross Income Heads
              </h2>
              <div className="mt-4 space-y-4">
                <div>
                  <div className="flex justify-between text-xs">
                    <span className="font-medium text-[#4f4b44]">Annual Gross Salary (CTC)</span>
                    <span className="font-semibold text-[#2f3430]">₹{grossSalary.toLocaleString("en-IN")}</span>
                  </div>
                  <input
                    type="range"
                    min="300000"
                    max="5000000"
                    step="25000"
                    value={grossSalary}
                    onChange={(e) => setGrossSalary(Number(e.target.value))}
                    className="mt-2 w-full accent-[#2f3430]"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-xs">
                    <span className="font-medium text-[#4f4b44]">Other Income (Bank Interest, Dividends, etc.)</span>
                    <span className="font-semibold text-[#2f3430]">₹{otherIncome.toLocaleString("en-IN")}</span>
                  </div>
                  <input
                    type="number"
                    value={otherIncome}
                    onChange={(e) => setOtherIncome(Math.max(0, Number(e.target.value)))}
                    className="mt-1.5 w-full rounded-md border border-[#e0ded9] px-3 py-1.5 text-xs text-[#37352f] outline-none"
                  />
                </div>
              </div>
            </div>

            {/* Chapter VI-A Deductions */}
            <div className="rounded-xl border border-[#e8e6e1] bg-white p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold tracking-tight text-[#37352f]">
                  2. Deductions & Exemptions (Old Regime Focus)
                </h2>
                <span className="text-[11px] text-[#9c978f]">Chapter VI-A</span>
              </div>

              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="text-xs font-medium text-[#4f4b44]">Section 80C (EPF, PPF, ELSS, LIC)</label>
                  <input
                    type="number"
                    value={sec80c}
                    onChange={(e) => setSec80c(Math.min(150000, Math.max(0, Number(e.target.value))))}
                    className="mt-1 w-full rounded-md border border-[#e0ded9] px-3 py-1.5 text-xs outline-none"
                    placeholder="Max ₹1,50,000"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-[#4f4b44]">Section 80D (Health Insurance)</label>
                  <input
                    type="number"
                    value={sec80d}
                    onChange={(e) => setSec80d(Math.max(0, Number(e.target.value)))}
                    className="mt-1 w-full rounded-md border border-[#e0ded9] px-3 py-1.5 text-xs outline-none"
                    placeholder="Self & Parents"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-[#4f4b44]">Section 80CCD(1B) (NPS Self)</label>
                  <input
                    type="number"
                    value={sec80ccd1b}
                    onChange={(e) => setSec80ccd1b(Math.min(50000, Math.max(0, Number(e.target.value))))}
                    className="mt-1 w-full rounded-md border border-[#e0ded9] px-3 py-1.5 text-xs outline-none"
                    placeholder="Max ₹50,000"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-[#4f4b44]">Home Loan Interest Loss (Self-Occupied)</label>
                  <input
                    type="number"
                    value={housePropertyLoss}
                    onChange={(e) => setHousePropertyLoss(Math.min(200000, Math.max(0, Number(e.target.value))))}
                    className="mt-1 w-full rounded-md border border-[#e0ded9] px-3 py-1.5 text-xs outline-none"
                    placeholder="Max ₹2,00,000"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Comparative Results (5 cols) */}
          <div className="space-y-6 lg:col-span-5">
            {/* Recommendation Card */}
            <div className="rounded-xl border border-[#dbe6dc] bg-[#f5f9f5] p-5 shadow-sm">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[#4f6f54]">
                <Sparkles className="h-4 w-4" /> Optimal Tax Recommendation
              </div>
              <div className="mt-2 text-2xl font-bold tracking-tight text-[#2f3430]">
                {displayCalculation.recommendedRegime}
              </div>
              <p className="mt-1 text-xs text-[#5f6b61]">
                {displayCalculation.savings > 0 ? (
                  <>
                    You save <strong className="text-[#2f3430]">₹{displayCalculation.savings.toLocaleString("en-IN")}</strong> in tax by choosing the {displayCalculation.recommendedRegime}.
                  </>
                ) : (
                  "Both regimes yield identical tax liability. New Regime recommended for streamlined compliance."
                )}
              </p>
            </div>

            {/* Side by Side Comparison Table */}
            <div className="overflow-hidden rounded-xl border border-[#e8e6e1] bg-white shadow-sm">
              <div className="grid grid-cols-2 border-b border-[#e8e6e1] bg-[#faf9f7] text-center text-xs font-semibold text-[#78736b]">
                <div className="py-3 border-r border-[#e8e6e1]">New Regime (115BAC)</div>
                <div className="py-3">Old Regime</div>
              </div>

              <div className="divide-y divide-[#f7f6f3] text-xs">
                <div className="grid grid-cols-2 p-3 text-center">
                  <div className="border-r border-[#f7f6f3]">
                    <span className="block text-[10px] text-[#9c978f]">Standard Deduction</span>
                    <span className="font-semibold text-[#2f3430]">₹{displayCalculation.newRegime.stdDeduction.toLocaleString("en-IN")}</span>
                  </div>
                  <div>
                    <span className="block text-[10px] text-[#9c978f]">Total Deductions</span>
                    <span className="font-semibold text-[#2f3430]">₹{(displayCalculation.oldRegime.stdDeduction + displayCalculation.oldRegime.totalDeductions).toLocaleString("en-IN")}</span>
                  </div>
                </div>

                <div className="grid grid-cols-2 p-3 text-center">
                  <div className="border-r border-[#f7f6f3]">
                    <span className="block text-[10px] text-[#9c978f]">Taxable Income</span>
                    <span className="font-semibold text-[#2f3430]">₹{displayCalculation.newRegime.taxableIncome.toLocaleString("en-IN")}</span>
                  </div>
                  <div>
                    <span className="block text-[10px] text-[#9c978f]">Taxable Income</span>
                    <span className="font-semibold text-[#2f3430]">₹{displayCalculation.oldRegime.taxableIncome.toLocaleString("en-IN")}</span>
                  </div>
                </div>

                <div className="grid grid-cols-2 p-3 text-center">
                  <div className="border-r border-[#f7f6f3]">
                    <span className="block text-[10px] text-[#9c978f]">Section 87A Rebate</span>
                    <span className="font-semibold text-[#4f6f54]">-₹{displayCalculation.newRegime.rebate87a.toLocaleString("en-IN")}</span>
                  </div>
                  <div>
                    <span className="block text-[10px] text-[#9c978f]">Section 87A Rebate</span>
                    <span className="font-semibold text-[#4f6f54]">-₹{displayCalculation.oldRegime.rebate87a.toLocaleString("en-IN")}</span>
                  </div>
                </div>

                <div className="grid grid-cols-2 p-3 text-center bg-[#faf9f7]">
                  <div className="border-r border-[#e8e6e1]">
                    <span className="block text-[10px] text-[#78736b]">Total Tax Payable</span>
                    <span className="text-base font-bold text-[#2f3430]">₹{displayCalculation.newRegime.totalTax.toLocaleString("en-IN")}</span>
                  </div>
                  <div>
                    <span className="block text-[10px] text-[#78736b]">Total Tax Payable</span>
                    <span className="text-base font-bold text-[#2f3430]">₹{displayCalculation.oldRegime.totalTax.toLocaleString("en-IN")}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Audit & Explanations */}
            <div className="rounded-xl border border-[#e8e6e1] bg-white p-4">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-[#37352f]">
                <ShieldCheck className="h-4 w-4 text-[#4f6f54]" /> Statutory Reference Trace
              </div>
              <ul className="mt-2 space-y-1.5 text-[11px] text-[#78736b]">
                <li>• Section 115BAC(1A) New Regime Slabs for AY {assessmentYear}</li>
                <li>• Standard Deduction of ₹{displayCalculation.newRegime.stdDeduction.toLocaleString("en-IN")} u/s 16(ia)</li>
                <li>• 4% Health & Education Cess calculated on tax liability</li>
                <li>• Section 87A rebate & mathematical marginal relief applied</li>
              </ul>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
