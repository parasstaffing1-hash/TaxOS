"use client";

import Link from "next/link";
import { useEffect, useState, useMemo } from "react";
import {
  ArrowLeft,
  CheckCircle2,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import { API_BASE } from "@/lib/api";

interface BackendGSTCalculation {
  taxable_value: number;
  cgst_amount: number;
  sgst_amount: number;
  igst_amount: number;
  cess_amount: number;
  total_gst_amount: number;
  gross_invoice_amount: number;
  round_off_adjustment: number;
  net_payable_amount: number;
}

interface BackendGSTINStatus {
  is_valid: boolean;
  state_code?: string | null;
  state_name?: string | null;
  pan?: string | null;
  error_message?: string | null;
}

export default function GSTCalculatorPage() {
  const [calcMode, setCalcMode] = useState<"exclusive" | "inclusive">("exclusive");
  const [baseAmount, setBaseAmount] = useState<number>(10000);
  const [gstRate, setGstRate] = useState<number>(18);
  const [supplyType, setSupplyType] = useState<"intra_state" | "inter_state">("intra_state");
  const [cessRate, setCessRate] = useState<number>(0);

  // GSTIN Validator Sandbox State
  const [inputGstin, setInputGstin] = useState<string>("27AAAAA0000A1Z5");
  const [backendCalculation, setBackendCalculation] = useState<BackendGSTCalculation | null>(null);
  const [backendGstinStatus, setBackendGstinStatus] = useState<BackendGSTINStatus | null>(null);
  const [backendState, setBackendState] = useState<"idle" | "loading" | "ready" | "error">("idle");

  const gstCalculation = useMemo(() => {
    const rateFraction = gstRate / 100;
    const cessFraction = cessRate / 100;

    let taxable = 0;
    let totalTax = 0;
    let cgst = 0;
    let sgst = 0;
    let igst = 0;
    let cess = 0;
    let grossTotal = 0;

    if (calcMode === "exclusive") {
      taxable = baseAmount;
      totalTax = taxable * rateFraction;
      cess = taxable * cessFraction;
      grossTotal = taxable + totalTax + cess;
    } else {
      // Inclusive
      const divisor = 1 + rateFraction + cessFraction;
      taxable = baseAmount / divisor;
      totalTax = taxable * rateFraction;
      cess = taxable * cessFraction;
      grossTotal = baseAmount;
    }

    if (supplyType === "intra_state") {
      cgst = totalTax / 2;
      sgst = totalTax / 2;
      igst = 0;
    } else {
      cgst = 0;
      sgst = 0;
      igst = totalTax;
    }

    const netPayable = Math.round(grossTotal);
    const roundOff = netPayable - grossTotal;

    return {
      taxable: Math.round(taxable * 100) / 100,
      cgst: Math.round(cgst * 100) / 100,
      sgst: Math.round(sgst * 100) / 100,
      igst: Math.round(igst * 100) / 100,
      cess: Math.round(cess * 100) / 100,
      totalGst: Math.round((totalTax + cess) * 100) / 100,
      grossTotal: Math.round(grossTotal * 100) / 100,
      roundOff: Math.round(roundOff * 100) / 100,
      netPayable,
    };
  }, [calcMode, baseAmount, gstRate, supplyType, cessRate]);

  useEffect(() => {
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      setBackendState("loading");
      const endpoint = calcMode === "exclusive" ? "calculate-exclusive" : "calculate-inclusive";
      const body = calcMode === "exclusive"
        ? { taxable_value: baseAmount, gst_rate: gstRate / 100, supply_type: supplyType, cess_rate: cessRate / 100 }
        : { gross_amount: baseAmount, gst_rate: gstRate / 100, supply_type: supplyType, cess_rate: cessRate / 100 };
      fetch(`${API_BASE}/gst/${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify(body),
      })
        .then(async (response) => {
          if (!response.ok) throw new Error(`GST API request failed (${response.status})`);
          return response.json() as Promise<BackendGSTCalculation>;
        })
        .then((result) => {
          setBackendCalculation(result);
          setBackendState("ready");
        })
        .catch((error: unknown) => {
          if (error instanceof DOMException && error.name === "AbortError") return;
          setBackendCalculation(null);
          setBackendState("error");
        });
    }, 250);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [calcMode, baseAmount, gstRate, supplyType, cessRate]);

  useEffect(() => {
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      fetch(`${API_BASE}/gst/validate-gstin`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify({ gstin: inputGstin }),
      })
        .then(async (response) => {
          if (!response.ok) throw new Error(`GSTIN API request failed (${response.status})`);
          return response.json() as Promise<BackendGSTINStatus>;
        })
        .then(setBackendGstinStatus)
        .catch((error: unknown) => {
          if (error instanceof DOMException && error.name === "AbortError") return;
          setBackendGstinStatus(null);
        });
    }, 250);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [inputGstin]);

  const displayedCalculation = backendCalculation
    ? {
        taxable: Number(backendCalculation.taxable_value),
        cgst: Number(backendCalculation.cgst_amount),
        sgst: Number(backendCalculation.sgst_amount),
        igst: Number(backendCalculation.igst_amount),
        cess: Number(backendCalculation.cess_amount),
        totalGst: Number(backendCalculation.total_gst_amount),
        grossTotal: Number(backendCalculation.gross_invoice_amount),
        roundOff: Number(backendCalculation.round_off_adjustment),
        netPayable: Number(backendCalculation.net_payable_amount),
      }
    : gstCalculation;

  // GSTIN Validation status
  const gstinStatus = useMemo(() => {
    const clean = inputGstin.trim().toUpperCase();
    const gstinRegex = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/;
    if (clean.length !== 15) {
      return { isValid: false, message: "GSTIN must be exactly 15 characters long." };
    }
    if (!gstinRegex.test(clean)) {
      return { isValid: false, message: "Invalid GSTIN format (State code + PAN + entity + Z + Checksum)." };
    }
    return {
      isValid: true,
      stateCode: clean.slice(0, 2),
      pan: clean.slice(2, 12),
      message: "Valid GSTIN structure and format.",
    };
  }, [inputGstin]);

  const displayedGstinStatus = backendGstinStatus
    ? {
        isValid: backendGstinStatus.is_valid,
        message: backendGstinStatus.error_message ?? "GSTIN checksum and format verified.",
        stateCode: backendGstinStatus.state_code ?? undefined,
        stateName: backendGstinStatus.state_name ?? undefined,
        pan: backendGstinStatus.pan ?? undefined,
      }
    : gstinStatus;

  return (
    <div className="min-h-screen bg-[#fffefa] text-[#37352f]">
      {/* Header */}
      <header className="sticky top-0 z-20 flex h-14 items-center justify-between border-b border-[#f0eee9] bg-white/90 px-6 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <Link href="/tax" className="flex items-center gap-1.5 text-xs text-[#78736b] hover:text-[#37352f]">
            <ArrowLeft className="h-3.5 w-3.5" /> All Tools
          </Link>
          <span className="text-[#d2cfc8]">/</span>
          <span className="text-xs font-semibold text-[#37352f]">GST Calculator & Validator</span>
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
      </header>

      {/* Main Container */}
      <main className="mx-auto max-w-[1140px] px-6 py-8">
        {/* Title */}
        <div className="mb-8">
          <div className="flex items-center gap-2 text-xs font-medium text-[#6f9476]">
            <span className="inline-block h-2 w-2 rounded-full bg-[#6f9476]" />
            CGST + SGST / IGST Engine · Section 170 Round-off Rule
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight sm:text-3xl">
            India GST Calculator & GSTIN Validator
          </h1>
          <p className="mt-1 text-xs text-[#78736b]">
            Compute exclusive and inclusive GST, split intra-state vs inter-state tax, and verify 15-digit GSTINs.
          </p>
        </div>

        {/* Layout: GST Calculator (8 cols) & GSTIN Validator (4 cols) */}
        <div className="grid gap-8 lg:grid-cols-12">
          {/* Left Column: GST Calculator */}
          <div className="space-y-6 lg:col-span-8">
            <div className="rounded-xl border border-[#e8e6e1] bg-white p-6 shadow-sm">
              {/* Mode Toggle */}
              <div className="flex gap-2 border-b border-[#f0eee9] pb-4">
                <button
                  type="button"
                  onClick={() => setCalcMode("exclusive")}
                  className={`rounded-lg px-4 py-2 text-xs font-medium transition ${
                    calcMode === "exclusive"
                      ? "bg-[#2f3430] text-white"
                      : "border border-[#e0ded9] bg-white text-[#78736b] hover:bg-[#faf9f7]"
                  }`}
                >
                  GST Exclusive (Add GST to Net Price)
                </button>
                <button
                  type="button"
                  onClick={() => setCalcMode("inclusive")}
                  className={`rounded-lg px-4 py-2 text-xs font-medium transition ${
                    calcMode === "inclusive"
                      ? "bg-[#2f3430] text-white"
                      : "border border-[#e0ded9] bg-white text-[#78736b] hover:bg-[#faf9f7]"
                  }`}
                >
                  GST Inclusive (Extract Base from MRP)
                </button>
              </div>

              {/* Inputs */}
              <div className="mt-5 grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="text-xs font-semibold text-[#4f4b44]">
                    {calcMode === "exclusive" ? "Taxable Net Amount (₹)" : "Gross MRP Amount (₹)"}
                  </label>
                  <input
                    type="number"
                    value={baseAmount}
                    onChange={(e) => setBaseAmount(Math.max(0, Number(e.target.value)))}
                    className="mt-1.5 w-full rounded-md border border-[#e0ded9] px-3 py-2 text-xs outline-none focus:border-[#78736b]"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-[#4f4b44]">GST Rate Slab (%)</label>
                  <select
                    value={gstRate}
                    onChange={(e) => setGstRate(Number(e.target.value))}
                    className="mt-1.5 w-full rounded-md border border-[#e0ded9] bg-white px-3 py-2 text-xs outline-none"
                  >
                    <option value={0}>0% (Exempt / Nil)</option>
                    <option value={5}>5% (Essential Goods/Services)</option>
                    <option value={12}>12% (Standard Items)</option>
                    <option value={18}>18% (Standard Services/Software)</option>
                    <option value={28}>28% (Luxury / Automobiles)</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-semibold text-[#4f4b44]">Supply Type</label>
                  <select
                    value={supplyType}
                    onChange={(e) => setSupplyType(e.target.value as "intra_state" | "inter_state")}
                    className="mt-1.5 w-full rounded-md border border-[#e0ded9] bg-white px-3 py-2 text-xs outline-none"
                  >
                    <option value="intra_state">Intra-State (CGST 50% + SGST 50%)</option>
                    <option value="inter_state">Inter-State / Export (IGST 100%)</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-semibold text-[#4f4b44]">Compensation Cess (%)</label>
                  <input
                    type="number"
                    value={cessRate}
                    onChange={(e) => setCessRate(Math.max(0, Number(e.target.value)))}
                    className="mt-1.5 w-full rounded-md border border-[#e0ded9] px-3 py-2 text-xs outline-none"
                    placeholder="e.g. 15% for motor vehicles"
                  />
                </div>
              </div>

              {/* GST Breakdown Output */}
              <div className="mt-8 rounded-xl border border-[#e8e6e1] bg-[#faf9f7] p-5">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-[#78736b]">
                  GST Tax Computation Summary
                </h3>
                <div className="mt-4 grid gap-3 sm:grid-cols-3">
                  <div className="rounded-lg border border-[#e8e6e1] bg-white p-3">
                    <span className="text-[10px] text-[#9c978f]">Base Taxable Value</span>
                    <div className="text-base font-bold text-[#2f3430]">₹{displayedCalculation.taxable.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</div>
                  </div>
                  <div className="rounded-lg border border-[#e8e6e1] bg-white p-3">
                    <span className="text-[10px] text-[#9c978f]">Total GST ({gstRate}%)</span>
                    <div className="text-base font-bold text-[#4f6f54]">₹{displayedCalculation.totalGst.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</div>
                  </div>
                  <div className="rounded-lg border border-[#2f3430] bg-[#2f3430] p-3 text-white">
                    <span className="text-[10px] text-[#d2cfc8]">Gross Invoice Value</span>
                    <div className="text-base font-bold">₹{displayedCalculation.netPayable.toLocaleString("en-IN")}</div>
                  </div>
                </div>

                {/* Sub-breakdown */}
                <div className="mt-4 space-y-1.5 border-t border-[#e8e6e1] pt-3 text-xs text-[#78736b]">
                  {supplyType === "intra_state" ? (
                    <>
                      <div className="flex justify-between">
                        <span>CGST ({gstRate / 2}%):</span>
                        <span className="font-semibold text-[#2f3430]">₹{displayedCalculation.cgst.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>SGST ({gstRate / 2}%):</span>
                        <span className="font-semibold text-[#2f3430]">₹{displayedCalculation.sgst.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</span>
                      </div>
                    </>
                  ) : (
                    <div className="flex justify-between">
                      <span>IGST ({gstRate}%):</span>
                      <span className="font-semibold text-[#2f3430]">₹{displayedCalculation.igst.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</span>
                    </div>
                  )}
                  {cessRate > 0 && (
                    <div className="flex justify-between">
                      <span>Compensation Cess ({cessRate}%):</span>
                      <span className="font-semibold text-[#2f3430]">₹{displayedCalculation.cess.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: GSTIN Validator Sandbox */}
          <div className="space-y-6 lg:col-span-4">
            <div className="rounded-xl border border-[#e8e6e1] bg-white p-5 shadow-sm">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-[#37352f]">
                <ShieldCheck className="h-4 w-4 text-[#4f6f54]" /> GSTIN Validator Sandbox
              </div>
              <p className="mt-1 text-[11px] text-[#78736b]">
                Test any 15-digit GSTIN with state code, PAN extraction, and Luhn Mod-36 validation.
              </p>

              <div className="mt-4">
                <input
                  type="text"
                  maxLength={15}
                  value={inputGstin}
                  onChange={(e) => setInputGstin(e.target.value.toUpperCase())}
                  className="w-full rounded-md border border-[#e0ded9] px-3 py-2 font-mono text-xs uppercase outline-none focus:border-[#78736b]"
                  placeholder="e.g. 27AAAAA0000A1Z5"
                />
              </div>

              <div className="mt-4 rounded-lg border border-[#e8e6e1] bg-[#faf9f7] p-3 text-xs">
                <div className="flex items-center gap-1.5 font-medium">
                  {displayedGstinStatus.isValid ? (
                    <CheckCircle2 className="h-4 w-4 text-[#4f6f54]" />
                  ) : (
                    <XCircle className="h-4 w-4 text-[#b94a48]" />
                  )}
                  <span className={displayedGstinStatus.isValid ? "text-[#4f6f54]" : "text-[#b94a48]"}>
                    {displayedGstinStatus.message}
                  </span>
                </div>

                {displayedGstinStatus.isValid && (
                  <div className="mt-3 space-y-1 text-[11px] text-[#78736b]">
                    <div>State Code: <strong>{displayedGstinStatus.stateCode}</strong></div>
                    <div>PAN Number: <strong>{displayedGstinStatus.pan}</strong></div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
