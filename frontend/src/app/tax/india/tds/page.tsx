"use client";

import Link from "next/link";
import { useEffect, useState, useId } from "react";
import {
  ArrowLeft,
  Search,
  ShieldCheck,
  Percent,
  CheckCircle2,
  AlertTriangle,
  Building2,
  UserCheck,
} from "lucide-react";
import { API_BASE } from "@/lib/api";

interface SectionDefinition {
  section_code: string;
  nature_of_payment: string;
  threshold_amount: number;
  rate_individual_or_huf: number;
  rate_others: number;
  higher_rate_no_pan: number;
  description: string;
}

interface TDSCalculationResponse {
  section_code: string;
  nature_of_payment: string;
  payment_amount: number;
  threshold_amount: number;
  is_threshold_exceeded: boolean;
  effective_rate: number;
  tds_amount: number;
  net_payable: number;
  is_higher_rate_pan_applied: boolean;
  explanation: string;
}

export default function IndiaTDSPage() {
  const searchInputId = useId();
  const amountInputId = useId();

  const [sections, setSections] = useState<SectionDefinition[]>([]);
  const [selectedSection, setSelectedSection] = useState<string>("194J");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [paymentAmount, setPaymentAmount] = useState<number>(100000);
  const [isIndividual, setIsIndividual] = useState<boolean>(true);
  const [hasValidPan, setHasValidPan] = useState<boolean>(true);
  const [result, setResult] = useState<TDSCalculationResponse | null>(null);

  // Fetch all supported statutory sections
  useEffect(() => {
    async function loadSections() {
      try {
        const res = await fetch(`${API_BASE}/api/v1/india/tds/sections`);
        if (res.ok) {
          const data = await res.json();
          setSections(
            data.map((d: {
              section_code: string;
              nature_of_payment: string;
              threshold_amount: number | string;
              rate_individual_or_huf: number | string;
              rate_others: number | string;
              higher_rate_no_pan: number | string;
              description: string;
            }) => ({
              section_code: d.section_code,
              nature_of_payment: d.nature_of_payment,
              threshold_amount: Number(d.threshold_amount),
              rate_individual_or_huf: Number(d.rate_individual_or_huf),
              rate_others: Number(d.rate_others),
              higher_rate_no_pan: Number(d.higher_rate_no_pan),
              description: d.description,
            }))
          );
        }
      } catch {
        // Fallback default list
        setSections([
          {
            section_code: "194C",
            nature_of_payment: "Payment to Contractors/Sub-contractors",
            threshold_amount: 30000,
            rate_individual_or_huf: 1.0,
            rate_others: 2.0,
            higher_rate_no_pan: 20.0,
            description: "1% for Individuals/HUFs, 2% for others. Single bill > ₹30k or annual > ₹1L.",
          },
          {
            section_code: "194J",
            nature_of_payment: "Fees for Professional or Technical Services",
            threshold_amount: 30000,
            rate_individual_or_huf: 10.0,
            rate_others: 10.0,
            higher_rate_no_pan: 20.0,
            description: "10% for professional services, 2% for technical services / call centres.",
          },
          {
            section_code: "194I",
            nature_of_payment: "Rent for Land, Building or Furniture",
            threshold_amount: 240000,
            rate_individual_or_huf: 10.0,
            rate_others: 10.0,
            higher_rate_no_pan: 20.0,
            description: "10% for land/building, 2% for plant/machinery. Annual threshold ₹2.4 Lakhs.",
          },
          {
            section_code: "194Q",
            nature_of_payment: "Purchase of Goods by Large Buyers",
            threshold_amount: 5000000,
            rate_individual_or_huf: 0.1,
            rate_others: 0.1,
            higher_rate_no_pan: 5.0,
            description: "0.1% on purchase value exceeding ₹50 Lakhs where buyer turnover > ₹10 Cr.",
          },
        ]);
      }
    }
    loadSections();
  }, []);

  // Compute TDS on input changes
  useEffect(() => {
    let cancelled = false;

    async function calculateTDS() {
      try {
        const res = await fetch(`${API_BASE}/api/v1/india/tds/calculate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            section_code: selectedSection,
            payment_amount: paymentAmount,
            is_payee_individual_or_huf: isIndividual,
            has_valid_pan: hasValidPan,
          }),
        });

        if (res.ok) {
          const data = await res.json();
          if (!cancelled) {
            setResult({
              section_code: data.section_code,
              nature_of_payment: data.nature_of_payment,
              payment_amount: Number(data.payment_amount),
              threshold_amount: Number(data.threshold_amount),
              is_threshold_exceeded: Boolean(data.is_threshold_exceeded),
              effective_rate: Number(data.effective_rate),
              tds_amount: Number(data.tds_amount),
              net_payable: Number(data.net_payable),
              is_higher_rate_pan_applied: Boolean(data.is_higher_rate_pan_applied),
              explanation: data.explanation || "",
            });
          }
        }
      } catch {
        // fallback
      }
    }

    calculateTDS();
    return () => {
      cancelled = true;
    };
  }, [selectedSection, paymentAmount, isIndividual, hasValidPan]);

  const filteredSections = sections.filter(
    (s) =>
      s.section_code.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.nature_of_payment.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const activeDef = sections.find((s) => s.section_code === selectedSection);

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
            <span className="text-3xl">✂️</span>
            <div>
              <h1 className="text-2xl font-bold text-stone-900 tracking-tight">
                India TDS & TCS Rate Finder & Deduction Engine
              </h1>
              <p className="text-sm text-stone-500">
                Explore Chapter XVII-B withholding tax sections (194C, 194J, 194I, 194Q, etc.), statutory thresholds, and Section 206AA non-PAN penalty rates.
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column: Section Selector & Payment Config */}
          <div className="lg:col-span-7 space-y-6">
            {/* Section Search and Quick Filter */}
            <div className="bg-white border border-stone-200 rounded-xl p-5 shadow-xs">
              <h2 className="text-sm font-semibold text-stone-900 uppercase tracking-wider mb-3 flex items-center gap-2">
                <Search className="w-4 h-4 text-stone-500" />
                Select Withholding Section
              </h2>
              <div className="relative mb-3">
                <input
                  id={searchInputId}
                  type="text"
                  placeholder="Search section code or payment type (e.g. 194J, rent, contractor)..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-stone-50 border border-stone-300 rounded-lg pl-9 pr-3 py-2 text-xs font-medium text-stone-800 focus:outline-none focus:ring-2 focus:ring-emerald-600 focus:bg-white"
                />
                <Search className="w-4 h-4 text-stone-400 absolute left-3 top-2.5" />
              </div>

              {/* Grid of Sections */}
              <div className="max-h-56 overflow-y-auto space-y-2 pr-1 custom-scrollbar">
                {filteredSections.map((sec) => (
                  <button
                    key={sec.section_code}
                    type="button"
                    onClick={() => setSelectedSection(sec.section_code)}
                    className={`w-full text-left p-3 rounded-lg border transition-all flex items-start justify-between text-xs ${
                      selectedSection === sec.section_code
                        ? "border-emerald-600 bg-emerald-50/40 text-emerald-950 ring-1 ring-emerald-600"
                        : "border-stone-200 bg-white hover:bg-stone-50 text-stone-800"
                    }`}
                  >
                    <div>
                      <div className="font-bold flex items-center gap-2">
                        <span className="bg-stone-200/80 px-1.5 py-0.5 rounded text-[11px] font-mono text-stone-900">
                          Sec {sec.section_code}
                        </span>
                        <span>{sec.nature_of_payment}</span>
                      </div>
                      <div className="text-[11px] text-stone-500 mt-1 line-clamp-1">
                        {sec.description}
                      </div>
                    </div>
                    <div className="text-right shrink-0 ml-3">
                      <div className="font-semibold text-stone-900">
                        {sec.rate_individual_or_huf}%
                      </div>
                      <div className="text-[10px] text-stone-400">
                        Threshold: {formatINR(sec.threshold_amount)}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Payment & Deductee Configuration */}
            <div className="bg-white border border-stone-200 rounded-xl p-5 shadow-xs space-y-4">
              <h2 className="text-sm font-semibold text-stone-900 uppercase tracking-wider flex items-center gap-2">
                <Percent className="w-4 h-4 text-emerald-600" />
                Payment Transaction Details
              </h2>
              <div>
                <label htmlFor={amountInputId} className="block text-xs font-semibold text-stone-700 mb-1">
                  Gross Payment Amount (₹)
                </label>
                <input
                  id={amountInputId}
                  type="number"
                  value={paymentAmount || ""}
                  onChange={(e) => setPaymentAmount(Number(e.target.value) || 0)}
                  className="w-full bg-stone-50 border border-stone-300 rounded-lg px-3 py-2 text-sm font-medium text-stone-800 focus:outline-none focus:ring-2 focus:ring-emerald-600 focus:bg-white"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                <div>
                  <span className="block text-xs font-semibold text-stone-700 mb-1.5">
                    Deductee / Payee Entity Type
                  </span>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      onClick={() => setIsIndividual(true)}
                      className={`px-3 py-2 rounded-lg border text-xs font-medium flex items-center justify-center gap-1.5 transition-all ${
                        isIndividual
                          ? "bg-emerald-600 text-white border-emerald-600 shadow-xs"
                          : "bg-white text-stone-700 border-stone-300 hover:bg-stone-50"
                      }`}
                    >
                      <UserCheck className="w-3.5 h-3.5" />
                      Individual / HUF
                    </button>
                    <button
                      type="button"
                      onClick={() => setIsIndividual(false)}
                      className={`px-3 py-2 rounded-lg border text-xs font-medium flex items-center justify-center gap-1.5 transition-all ${
                        !isIndividual
                          ? "bg-emerald-600 text-white border-emerald-600 shadow-xs"
                          : "bg-white text-stone-700 border-stone-300 hover:bg-stone-50"
                      }`}
                    >
                      <Building2 className="w-3.5 h-3.5" />
                      Company / Firm
                    </button>
                  </div>
                </div>

                <div>
                  <span className="block text-xs font-semibold text-stone-700 mb-1.5">
                    Payee PAN Status (Sec 206AA)
                  </span>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      onClick={() => setHasValidPan(true)}
                      className={`px-3 py-2 rounded-lg border text-xs font-medium flex items-center justify-center gap-1.5 transition-all ${
                        hasValidPan
                          ? "bg-emerald-600 text-white border-emerald-600 shadow-xs"
                          : "bg-white text-stone-700 border-stone-300 hover:bg-stone-50"
                      }`}
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Valid PAN
                    </button>
                    <button
                      type="button"
                      onClick={() => setHasValidPan(false)}
                      className={`px-3 py-2 rounded-lg border text-xs font-medium flex items-center justify-center gap-1.5 transition-all ${
                        !hasValidPan
                          ? "bg-red-600 text-white border-red-600 shadow-xs"
                          : "bg-white text-stone-700 border-stone-300 hover:bg-stone-50"
                      }`}
                    >
                      <AlertTriangle className="w-3.5 h-3.5" />
                      No PAN / Invalid
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Deduction Breakdown & Statutory Analysis */}
          <div className="lg:col-span-5 space-y-6">
            {/* Section Overview Card */}
            {activeDef && (
              <div className="bg-white border border-stone-200 rounded-xl p-5 shadow-xs">
                <div className="flex items-center justify-between mb-2">
                  <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 text-[11px] font-bold font-mono">
                    Section {activeDef.section_code}
                  </span>
                  <span className="text-xs text-stone-500">
                    Threshold: <strong className="text-stone-800">{formatINR(activeDef.threshold_amount)}</strong>
                  </span>
                </div>
                <h3 className="font-bold text-sm text-stone-900 mb-1">
                  {activeDef.nature_of_payment}
                </h3>
                <p className="text-xs text-stone-500 leading-relaxed">
                  {activeDef.description}
                </p>
              </div>
            )}

            {/* Threshold & PAN Banner */}
            {!hasValidPan && (
              <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3 text-xs text-amber-900">
                <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                <div>
                  <strong className="font-semibold block mb-0.5">
                    Section 206AA Penalty Rate Active
                  </strong>
                  Where the deductee fails to furnish a valid PAN, tax is mandatorily deducted at 20% or the standard rate, whichever is higher.
                </div>
              </div>
            )}

            {/* Deduction Result Card */}
            <div className="bg-stone-900 text-white rounded-xl p-5 shadow-sm space-y-4">
              <h3 className="text-xs font-semibold text-stone-300 uppercase tracking-wider">
                TDS Deduction Summary
              </h3>
              <div className="space-y-2.5 text-xs">
                <div className="flex justify-between items-center text-stone-300">
                  <span>Gross Invoice / Payment</span>
                  <span className="font-semibold text-white">
                    {result ? formatINR(result.payment_amount) : "₹0"}
                  </span>
                </div>
                <div className="flex justify-between items-center text-stone-300">
                  <span>Applied Withholding Rate</span>
                  <span className="font-bold text-emerald-400">
                    {result ? `${result.effective_rate}%` : "0%"}
                  </span>
                </div>
                <div className="flex justify-between items-center text-stone-300">
                  <span>Statutory Threshold Met?</span>
                  <span className={`font-semibold ${result?.is_threshold_exceeded ? "text-amber-400" : "text-emerald-400"}`}>
                    {result?.is_threshold_exceeded ? "Yes (Deduction Mandatory)" : "No (Exempt)"}
                  </span>
                </div>
                <div className="pt-2 border-t border-stone-800 flex justify-between items-center text-stone-200">
                  <span>Total TDS to Deposit</span>
                  <span className="font-bold text-red-400 text-base">
                    {result ? formatINR(result.tds_amount) : "₹0"}
                  </span>
                </div>
                <div className="pt-2 border-t border-stone-800 flex justify-between items-center text-sm font-bold">
                  <span className="text-emerald-400">Net Payable to Vendor / Payee</span>
                  <span className="text-emerald-400 text-lg">
                    {result ? formatINR(result.net_payable) : "₹0"}
                  </span>
                </div>
              </div>
            </div>

            {/* Form 26Q / 24Q Filing Guide */}
            <div className="bg-white border border-stone-200 rounded-xl p-5 shadow-xs text-xs space-y-2">
              <h4 className="font-semibold text-stone-900 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                Compliance & Deposit Deadlines
              </h4>
              <p className="text-stone-500 leading-relaxed">
                TDS deducted must be deposited to the Central Government using <strong>Challan ITNS 281</strong> on or before the <strong>7th of the following month</strong> (30th April for March deductions). Quarterly returns are filed on <strong>Form 26Q</strong> (non-salary) or <strong>Form 24Q</strong> (salary).
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
