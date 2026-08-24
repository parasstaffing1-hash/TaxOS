"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  RefreshCw,
  XCircle,
} from "lucide-react";
import { API_BASE } from "@/lib/api";

interface MockInvoicePair {
  id: string;
  vendorName: string;
  gstin: string;
  invoiceNo: string;
  invoiceDate: string;
  booksTax: number;
  portalTax: number;
  status:
    | "MATCHED"
    | "PARTIAL_MATCH"
    | "MISMATCH"
    | "MISSING_IN_BOOKS"
    | "MISSING_IN_RETURN"
    | "DUPLICATE"
    | "REVIEW_REQUIRED";
  notes: string;
}

interface ReconciliationApiRecord {
  record_id: string;
  party_identifier: string;
  reference_number: string;
  transaction_date: string;
  tax_amount: number;
}

interface ReconciliationApiPair {
  status: string;
  books_record?: ReconciliationApiRecord | null;
  portal_record?: ReconciliationApiRecord | null;
  confidence_score: number;
  match_strategy: string;
  explanation: string;
}

function toReconciliationRecord(pair: MockInvoicePair, source: "books" | "gstr2b", taxAmount: number) {
  return {
    record_id: `${pair.id}-${source}`,
    party_identifier: pair.gstin,
    reference_number: pair.invoiceNo,
    transaction_date: pair.invoiceDate,
    taxable_amount: taxAmount,
    tax_amount: taxAmount,
    total_amount: taxAmount,
    source,
  };
}

function fromApiPair(pair: ReconciliationApiPair, index: number): MockInvoicePair {
  const record = pair.books_record ?? pair.portal_record;
  const status = pair.status.toUpperCase() as MockInvoicePair["status"];
  return {
    id: record?.record_id ?? `REC-${String(index + 1).padStart(3, "0")}`,
    vendorName: record?.party_identifier ?? "Unknown party",
    gstin: record?.party_identifier ?? "—",
    invoiceNo: record?.reference_number ?? "—",
    invoiceDate: record?.transaction_date ?? "—",
    booksTax: Number(pair.books_record?.tax_amount ?? 0),
    portalTax: Number(pair.portal_record?.tax_amount ?? 0),
    status,
    notes: `${pair.explanation} (${pair.match_strategy}, confidence ${Math.round(pair.confidence_score * 100)}%).`,
  };
}

const INITIAL_PAIRS: MockInvoicePair[] = [
  {
    id: "REC-001",
    vendorName: "Amazon Web Services India",
    gstin: "27AAAAA0000A1Z5",
    invoiceNo: "AWS-IN-2024-8891",
    invoiceDate: "2024-10-15",
    booksTax: 18000,
    portalTax: 18000,
    status: "MATCHED",
    notes: "Exact match on GSTIN, Invoice number, and tax amount.",
  },
  {
    id: "REC-002",
    vendorName: "Google Cloud India Pvt Ltd",
    gstin: "29BBBBB0000B1Z6",
    invoiceNo: "GCP/2024/1102",
    invoiceDate: "2024-10-18",
    booksTax: 36000,
    portalTax: 36000,
    status: "MATCHED",
    notes: "Matched with normalized reference string.",
  },
  {
    id: "REC-003",
    vendorName: "Dell India Computer Supplies",
    gstin: "27CCCCC0000C1Z7",
    invoiceNo: "DELL-INV-5501",
    invoiceDate: "2024-10-20",
    booksTax: 28000,
    portalTax: 25000,
    status: "PARTIAL_MATCH",
    notes: "Tax variance of ₹3,000 between books (₹28,000) and GSTR-2B (₹25,000).",
  },
  {
    id: "REC-004",
    vendorName: "Office Supplies Co",
    gstin: "07DDDDD0000D1Z8",
    invoiceNo: "OSC-891",
    invoiceDate: "2024-10-25",
    booksTax: 4500,
    portalTax: 0,
    status: "MISSING_IN_RETURN",
    notes: "Recorded in books, but supplier has not filed in GSTR-1 / missing in GSTR-2B.",
  },
  {
    id: "REC-005",
    vendorName: "HubSpot Singapore Pte",
    gstin: "99EEEEE0000E1Z9",
    invoiceNo: "HS-OCT-2024",
    invoiceDate: "2024-10-28",
    booksTax: 0,
    portalTax: 12000,
    status: "MISSING_IN_BOOKS",
    notes: "Available in GSTR-2B portal feed, but not booked in accounting purchase register.",
  },
];

export default function GSTReconciliationPage() {
  const [filterStatus, setFilterStatus] = useState<string>("ALL");
  const [pairs, setPairs] = useState<MockInvoicePair[]>(INITIAL_PAIRS);
  const [runState, setRunState] = useState<"idle" | "loading" | "ready" | "error">("idle");

  const runReconciliation = useCallback(async () => {
    setRunState("loading");
    try {
      const response = await fetch(`${API_BASE}/reconciliation/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          books_records: INITIAL_PAIRS.filter((pair) => pair.booksTax > 0).map((pair) =>
            toReconciliationRecord(pair, "books", pair.booksTax)
          ),
          portal_records: INITIAL_PAIRS.filter((pair) => pair.portalTax > 0).map((pair) =>
            toReconciliationRecord(pair, "gstr2b", pair.portalTax)
          ),
          amount_tolerance: 1,
          date_tolerance_days: 60,
        }),
      });
      if (!response.ok) throw new Error(`Reconciliation request failed (${response.status})`);
      const report = (await response.json()) as { pairs: ReconciliationApiPair[] };
      setPairs(report.pairs.map(fromApiPair));
      setRunState("ready");
    } catch {
      setRunState("error");
    }
  }, []);

  useEffect(() => {
    void runReconciliation();
  }, [runReconciliation]);

  const filteredPairs = pairs.filter((p) => {
    if (filterStatus === "ALL") return true;
    return p.status === filterStatus;
  });

  const matchedTax = pairs.filter((p) => p.status === "MATCHED").reduce(
    (acc, p) => acc + p.booksTax,
    0
  );
  const mismatchedTax = pairs.filter((p) => p.status !== "MATCHED").reduce(
    (acc, p) => acc + p.booksTax,
    0
  );

  return (
    <div className="min-h-screen bg-[#fffefa] text-[#37352f]">
      {/* Header */}
      <header className="sticky top-0 z-20 flex h-14 items-center justify-between border-b border-[#f0eee9] bg-white/90 px-6 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <Link href="/tax" className="flex items-center gap-1.5 text-xs text-[#78736b] hover:text-[#37352f]">
            <ArrowLeft className="h-3.5 w-3.5" /> All Tools
          </Link>
          <span className="text-[#d2cfc8]">/</span>
          <span className="text-xs font-semibold text-[#37352f]">GST Reconciliation Engine</span>
        </div>
      </header>

      {/* Main Container */}
      <main className="mx-auto max-w-[1140px] px-6 py-8">
        {/* Title */}
        <div className="mb-8">
          <div className="flex items-center gap-2 text-xs font-medium text-[#6f9476]">
            <span className="inline-block h-2 w-2 rounded-full bg-[#6f9476]" />
            GSTR-2B vs Purchase Register · Multi-Pass Reconciliation
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight sm:text-3xl">
            Autonomous Tax Reconciliation Dashboard
          </h1>
          <p className="mt-1 text-xs text-[#78736b]">
            Match vendor invoices between internal books and government tax portal records with tolerance & variance classification.
          </p>
          <div className="mt-4 flex items-center gap-3">
            <button
              type="button"
              onClick={() => void runReconciliation()}
              disabled={runState === "loading"}
              className="inline-flex items-center gap-2 rounded-lg bg-[#2f3430] px-3 py-2 text-xs font-medium text-white transition hover:bg-[#1e221f] disabled:cursor-wait disabled:opacity-60"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${runState === "loading" ? "animate-spin" : ""}`} />
              {runState === "loading" ? "Running engine…" : "Run live reconciliation"}
            </button>
            <span className={`text-xs ${runState === "error" ? "text-[#a15c38]" : "text-[#78736b]"}`}>
              {runState === "ready" ? "Results returned by the TaxOS reconciliation API." : runState === "error" ? "API unavailable; showing the sample dataset." : ""}
            </span>
          </div>
        </div>

        {/* Metrics Overview */}
        <div className="mb-8 grid gap-4 sm:grid-cols-4">
          <div className="rounded-xl border border-[#e8e6e1] bg-white p-4">
            <span className="text-[10px] uppercase font-semibold text-[#8f8a81]">Total Invoices</span>
            <div className="mt-1 text-2xl font-bold text-[#2f3430]">{pairs.length}</div>
            <span className="text-xs text-[#8f8a81]">October 2024 Period</span>
          </div>

          <div className="rounded-xl border border-[#dbe8dd] bg-[#f5faf5] p-4">
            <span className="text-[10px] uppercase font-semibold text-[#4f6f54]">Matched ITC Tax</span>
            <div className="mt-1 text-2xl font-bold text-[#4f6f54]">₹{matchedTax.toLocaleString("en-IN")}</div>
            <span className="text-xs text-[#4f6f54]">100% Eligible for Claim</span>
          </div>

          <div className="rounded-xl border border-[#f3dada] bg-[#fdf6f6] p-4">
            <span className="text-[10px] uppercase font-semibold text-[#b94a48]">At Risk / Mismatched</span>
            <div className="mt-1 text-2xl font-bold text-[#b94a48]">₹{mismatchedTax.toLocaleString("en-IN")}</div>
            <span className="text-xs text-[#b94a48]">Requires Vendor Follow-up</span>
          </div>

          <div className="rounded-xl border border-[#e8e6e1] bg-white p-4">
            <span className="text-[10px] uppercase font-semibold text-[#8f8a81]">Match Ratio</span>
            <div className="mt-1 text-2xl font-bold text-[#2f3430]">
              {Math.round((matchedTax / (matchedTax + mismatchedTax)) * 100)}%
            </div>
            <span className="text-xs text-[#8f8a81]">Confidence Score: 0.96</span>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="mb-4 flex flex-wrap gap-1.5 border-b border-[#f0eee9] pb-3">
          {["ALL", "MATCHED", "PARTIAL_MATCH", "MISSING_IN_RETURN", "MISSING_IN_BOOKS"].map((st) => (
            <button
              key={st}
              onClick={() => setFilterStatus(st)}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${
                filterStatus === st
                  ? "bg-[#2f3430] text-white"
                  : "bg-white text-[#78736b] hover:bg-[#faf9f7]"
              }`}
            >
              {st.replace(/_/g, " ")}
            </button>
          ))}
        </div>

        {/* Invoice Table */}
        <div className="overflow-hidden rounded-xl border border-[#e8e6e1] bg-white shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-[#e8e6e1] bg-[#faf9f7] text-[10px] uppercase font-semibold text-[#8f8a81]">
                <tr>
                  <th className="py-3 px-4">Vendor & GSTIN</th>
                  <th className="py-3 px-4">Invoice No</th>
                  <th className="py-3 px-4">Date</th>
                  <th className="py-3 px-4">Books Tax (₹)</th>
                  <th className="py-3 px-4">Portal Tax (₹)</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Explanation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#f7f6f3]">
                {filteredPairs.map((pair) => (
                  <tr key={pair.id} className="hover:bg-[#faf9f7] transition">
                    <td className="py-3 px-4">
                      <div className="font-semibold text-[#2f3430]">{pair.vendorName}</div>
                      <div className="font-mono text-[10px] text-[#8f8a81]">{pair.gstin}</div>
                    </td>
                    <td className="py-3 px-4 font-mono text-[11px] text-[#4a4640]">{pair.invoiceNo}</td>
                    <td className="py-3 px-4 text-[#8f8a81]">{pair.invoiceDate}</td>
                    <td className="py-3 px-4 font-medium text-[#2f3430]">
                      {pair.booksTax > 0 ? `₹${pair.booksTax.toLocaleString("en-IN")}` : "—"}
                    </td>
                    <td className="py-3 px-4 font-medium text-[#2f3430]">
                      {pair.portalTax > 0 ? `₹${pair.portalTax.toLocaleString("en-IN")}` : "—"}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                          pair.status === "MATCHED"
                            ? "bg-[#eaf3eb] text-[#4f6f54]"
                            : pair.status === "PARTIAL_MATCH"
                            ? "bg-[#fdf5ea] text-[#ba7b35]"
                            : "bg-[#faecec] text-[#b94a48]"
                        }`}
                      >
                        {pair.status === "MATCHED" && <CheckCircle2 className="h-3 w-3" />}
                        {pair.status === "PARTIAL_MATCH" && <AlertTriangle className="h-3 w-3" />}
                        {(pair.status === "MISSING_IN_RETURN" || pair.status === "MISSING_IN_BOOKS") && (
                          <XCircle className="h-3 w-3" />
                        )}
                        {pair.status.replace(/_/g, " ")}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-[11px] text-[#78736b] max-w-xs">{pair.notes}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}
