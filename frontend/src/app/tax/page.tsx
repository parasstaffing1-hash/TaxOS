"use client";

import Link from "next/link";
import { useEffect, useState, useMemo } from "react";
import {
  ChevronRight,
  Filter,
  Search,
  ShieldCheck,
} from "lucide-react";
import { API_BASE } from "@/lib/api";

interface CatalogToolItem {
  id: string;
  number: number;
  title: string;
  description: string;
  category: string;
  jurisdiction: string;
  toolType: string;
  route: string;
  tags: string[];
  status?: "complete" | "partial" | "not_started" | "blocked";
}

const MASTER_CATALOG_TOOLS: CatalogToolItem[] = [
  // India Income Tax & Salary
  {
    id: "income-tax-calculator",
    number: 1,
    title: "Income Tax Calculator (AY 2025-26 & 2024-25)",
    description: "Universal India income tax engine with Old vs New regime, Sec 87A rebate & marginal relief.",
    category: "India Income Tax",
    jurisdiction: "India (IN)",
    toolType: "Calculator",
    route: "/tax/india/income-tax-calculator",
    tags: ["income-tax", "old-regime", "new-regime", "87a-rebate", "marginal-relief"],
  },
  {
    id: "salary-ctc-take-home",
    number: 23,
    title: "CTC to Take-Home Salary Calculator",
    description: "Break down annual CTC into monthly in-hand take-home salary with EPF, PT, and HRA exemption.",
    category: "India Salary & CTC",
    jurisdiction: "India (IN)",
    toolType: "Calculator",
    route: "/tax/india/income-tax-calculator",
    tags: ["ctc", "take-home", "salary-slip", "in-hand"],
  },
  {
    id: "hra-exemption-calculator",
    number: 30,
    title: "HRA Exemption Calculator (Sec 10(13A))",
    description: "Determine exact tax-exempt HRA under Rule 2A for Metro (50%) and Non-Metro (40%) cities.",
    category: "India Salary & CTC",
    jurisdiction: "India (IN)",
    toolType: "Calculator",
    route: "/tax/india/income-tax-calculator",
    tags: ["hra", "rent-receipt", "10-13a"],
  },
  {
    id: "capital-gains-calculator",
    number: 71,
    title: "Capital Gains Tax Calculator (Budget 2024)",
    description: "Compute STCG (20%/15%), LTCG (12.5%/10% with ₹1.25L exemption), Property, and loss set-offs.",
    category: "Capital Gains",
    jurisdiction: "India (IN)",
    toolType: "Calculator",
    route: "/tax/india/income-tax-calculator",
    tags: ["capital-gains", "stcg-111a", "ltcg-112a", "equity", "crypto-115bbh"],
  },
  {
    id: "advance-tax-calculator",
    number: 181,
    title: "Advance Tax & Sec 234A/B/C Interest Calculator",
    description: "Quarterly installments (15/45/75/100%) and delay interest computations.",
    category: "Advance Tax & Interest",
    jurisdiction: "India (IN)",
    toolType: "Calculator",
    route: "/tax/india/income-tax-calculator",
    tags: ["advance-tax", "234a", "234b", "234c", "234f"],
  },
  {
    id: "tds-tcs-rate-finder",
    number: 201,
    title: "TDS / TCS Section & Rate Finder",
    description: "Instant lookup for 194C, 194J, 194I, 194Q, 194A rates, thresholds, and missing PAN rules.",
    category: "TDS & TCS",
    jurisdiction: "India (IN)",
    toolType: "Checker",
    route: "/tax/india/income-tax-calculator",
    tags: ["tds", "tcs", "194c", "194j", "194i", "206c"],
  },

  // India GST
  {
    id: "gst-calculator",
    number: 271,
    title: "GST Inclusive & Exclusive Calculator",
    description: "Split CGST + SGST (Intra-state) vs IGST (Inter-state), reverse calculate from MRP, and apply cess.",
    category: "India GST",
    jurisdiction: "India (IN)",
    toolType: "Calculator",
    route: "/tax/india/gst-calculator",
    tags: ["gst", "cgst", "sgst", "igst", "reverse-gst", "inclusive"],
  },
  {
    id: "gstin-validator",
    number: 297,
    title: "GSTIN Checksum & State Code Validator",
    description: "Verify 15-character GSTIN format, jurisdiction state name, PAN, and Luhn Mod-36 checksum.",
    category: "India GST",
    jurisdiction: "India (IN)",
    toolType: "Validator",
    route: "/tax/india/gst-calculator",
    tags: ["gstin", "luhn-mod-36", "state-codes", "pan-verification"],
  },
  {
    id: "gst-reconciliation-dashboard",
    number: 358,
    title: "GSTR-2B vs Purchase Register Reconciliation",
    description: "Autonomous multi-pass reconciliation engine matching invoices with tolerance and variance tracking.",
    category: "GST & Tax Reconciliation",
    jurisdiction: "India (IN)",
    toolType: "Reconciler",
    route: "/tax/india/reconciliation",
    tags: ["reconciliation", "gstr-2b", "itc-matching", "missing-invoices"],
  },

  // Global Jurisdictions
  {
    id: "us-tax-calculator",
    number: 561,
    title: "US Federal Income & Sales Tax Calculator",
    description: "Federal progressive brackets (10%-37%), standard deduction, FICA, and state sales tax rates.",
    category: "Global Personal Tax",
    jurisdiction: "United States (US)",
    toolType: "Calculator",
    route: "/tax/india/income-tax-calculator",
    tags: ["us-tax", "irs", "federal-slabs", "sales-tax"],
  },
  {
    id: "uk-vat-income-tax",
    number: 591,
    title: "UK PAYE Income Tax & VAT Calculator",
    description: "HMRC standard 20% VAT, Personal Allowance £12,570, National Insurance, and PAYE tax brackets.",
    category: "Global Personal Tax",
    jurisdiction: "United Kingdom (GB)",
    toolType: "Calculator",
    route: "/tax/india/income-tax-calculator",
    tags: ["uk-vat", "hmrc", "paye", "national-insurance"],
  },
  {
    id: "uae-corporate-tax",
    number: 621,
    title: "UAE Corporate Tax & Free Zone Analyzer",
    description: "9% Corporate Tax calculation above AED 375,000 threshold and 5% standard VAT.",
    category: "Global Corporate Tax",
    jurisdiction: "UAE (AE)",
    toolType: "Calculator",
    route: "/tax/india/income-tax-calculator",
    tags: ["uae", "corporate-tax", "aed-375000", "free-zone"],
  },
];

const CATEGORIES = [
  "All Tools",
  "India Income Tax",
  "India Salary & CTC",
  "India GST",
  "Capital Gains",
  "TDS & TCS",
  "Advance Tax & Interest",
  "GST & Tax Reconciliation",
  "Global Personal Tax",
  "Global Corporate Tax",
];

function catalogFamilyLabel(family: string): string {
  if (family.startsWith("india_gst")) return "India GST";
  if (family === "india_income_tax") return "India Income Tax";
  if (family === "india_salary_tax") return "India Salary & CTC";
  if (family === "india_advance_tax" || family === "india_interest_penalty") {
    return "Advance Tax & Interest";
  }
  if (family === "india_tds" || family === "india_tcs") return "TDS & TCS";
  if (family === "india_gst_reconciliation" || family === "audit_reconciliation") {
    return "GST & Tax Reconciliation";
  }
  if (family === "global_corporate_tax") return "Global Corporate Tax";
  return "Global Personal Tax";
}

export default function MasterTaxCatalogPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All Tools");
  const [catalogTools, setCatalogTools] = useState<CatalogToolItem[]>([]);
  const [catalogError, setCatalogError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetch(`${API_BASE}/catalog?limit=850`, { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error(`Catalog request failed (${response.status})`);
        return response.json();
      })
      .then((tools: Array<Record<string, unknown>>) => {
        setCatalogTools(
          tools.map((tool) => ({
            id: String(tool.id),
            number: Number(tool.number),
            title: String(tool.title),
            description: String(tool.description),
            category: catalogFamilyLabel(String(tool.family)),
            jurisdiction: String(tool.jurisdiction),
            toolType: String(tool.tool_type),
            route: String(tool.route),
            tags: Array.isArray(tool.tags) ? tool.tags.map(String) : [],
            status: tool.status as CatalogToolItem["status"],
          }))
        );
        setCatalogError(null);
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setCatalogError("Live catalog unavailable; showing the featured tool set.");
      });
    return () => controller.abort();
  }, []);

  const tools = catalogTools.length > 0 ? catalogTools : MASTER_CATALOG_TOOLS;

  const filteredTools = useMemo(() => {
    return tools.filter((tool) => {
      const matchesCategory =
        selectedCategory === "All Tools" || tool.category === selectedCategory;
      const q = searchQuery.toLowerCase().trim();
      const matchesQuery =
        !q ||
        tool.title.toLowerCase().includes(q) ||
        tool.description.toLowerCase().includes(q) ||
        tool.tags.some((tag) => tag.includes(q));
      return matchesCategory && matchesQuery;
    });
  }, [searchQuery, selectedCategory, tools]);

  return (
    <div className="min-h-screen bg-[#fffefa] text-[#37352f]">
      {/* Header */}
      <header className="sticky top-0 z-20 flex h-14 items-center justify-between border-b border-[#f0eee9] bg-white/90 px-6 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <Link
            href="/"
            className="flex items-center gap-2 text-sm font-semibold tracking-tight text-[#37352f]"
          >
            <span className="flex h-7 w-7 items-center justify-center rounded-[7px] bg-[#2f3430] text-xs font-bold text-white">
              T
            </span>
            TaxOS
          </Link>
          <span className="text-[#d2cfc8]">/</span>
          <span className="text-xs font-medium text-[#78736b]">Tax Tools Catalog</span>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href="/tax/india/income-tax-calculator"
            className="rounded-md bg-[#2f3430] px-3 py-1.5 text-xs font-medium text-white transition hover:bg-[#1e221f]"
          >
            Launch Calculator →
          </Link>
        </div>
      </header>

      {/* Main Container */}
      <main className="mx-auto max-w-[1180px] px-6 py-10">
        {/* Banner Section */}
        <div className="mb-10">
          <div className="mb-2 flex items-center gap-2 text-xs font-medium text-[#6f9476]">
            <span className="inline-block h-2 w-2 rounded-full bg-[#6f9476]" />
            Deterministic Tax Engine · India-First & Global Catalog
          </div>
          <h1 className="text-3xl font-semibold tracking-[-0.04em] sm:text-4xl">
            Tax Intelligence & Automation Catalog
          </h1>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-[#78736b]">
            Browse the live TaxOS tool registry, including implemented workflows and
            clearly marked planned coverage.
          </p>
          {catalogError && <p className="mt-2 text-xs text-[#a15c38]">{catalogError}</p>}
        </div>

        {/* Search & Filter Bar */}
        <div className="mb-8 flex flex-col gap-3 rounded-xl border border-[#e8e6e1] bg-[#faf9f7] p-4 sm:flex-row sm:items-center">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-[#9c978f]" />
            <input
              type="text"
              placeholder="Search by keyword, section (e.g. 87A, 115BAC, HRA, 194C), or country..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-lg border border-[#e0ded9] bg-white py-2 pl-9 pr-4 text-xs text-[#37352f] outline-none transition focus:border-[#78736b]"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter className="h-3.5 w-3.5 text-[#9c978f]" />
            <span className="text-xs font-medium text-[#78736b]">
              Showing {filteredTools.length} of {tools.length} catalog entries
            </span>
          </div>
        </div>

        {/* Category Pills */}
        <div className="mb-8 flex flex-wrap gap-1.5">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`rounded-full px-3 py-1 text-xs font-medium transition ${
                selectedCategory === cat
                  ? "bg-[#2f3430] text-white"
                  : "border border-[#e8e6e1] bg-white text-[#78736b] hover:bg-[#f7f6f3]"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Tools Grid */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filteredTools.map((tool) => (
            <Link
              key={tool.id}
              href={tool.route}
              className="group flex flex-col justify-between rounded-xl border border-[#e8e6e1] bg-white p-5 transition hover:border-[#cbc7be] hover:shadow-sm"
            >
              <div>
                <div className="mb-2 flex items-center justify-between text-[11px] text-[#9c978f]">
                  <span className="font-mono font-medium text-[#78736b]">
                    #{tool.number.toString().padStart(3, "0")}
                  </span>
                  <span className="rounded bg-[#f0eee9] px-2 py-0.5 text-[10px] font-medium text-[#6b665e]">
                    {tool.jurisdiction}
                  </span>
                </div>
                <h2 className="text-base font-semibold tracking-tight text-[#37352f] group-hover:text-[#1a1917]">
                  {tool.title}
                </h2>
                {tool.status && tool.status !== "complete" && (
                  <span className="mt-2 inline-flex rounded-full bg-[#fff3df] px-2 py-0.5 text-[10px] font-medium capitalize text-[#9a6a2f]">
                    {tool.status.replace("_", " ")}
                  </span>
                )}
                <p className="mt-1.5 text-xs leading-relaxed text-[#78736b]">
                  {tool.description}
                </p>
              </div>

              <div className="mt-4 flex items-center justify-between border-t border-[#f7f6f3] pt-3">
                <span className="text-[11px] font-medium text-[#8f8a81]">
                  {tool.category}
                </span>
                <span className="inline-flex items-center text-xs font-medium text-[#4f6f54] group-hover:translate-x-0.5 transition">
                  Open Tool <ChevronRight className="ml-1 h-3.5 w-3.5" />
                </span>
              </div>
            </Link>
          ))}
        </div>

        {/* Trust & Guarantee Banner */}
        <div className="mt-14 rounded-2xl border border-[#dbe6dc] bg-[#f5f9f5] p-6">
          <div className="flex items-start gap-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white text-[#4f6f54] shadow-sm">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-[#2f3430]">
                Statutory Precision & Mathematical Explainability
              </h3>
              <p className="mt-1 text-xs leading-relaxed text-[#5f6b61]">
                Every calculation resolves through versioned tax rule packs, guarantees zero
                binary float rounding errors via Decimal arithmetic, and returns full
                statutory references with step-by-step audit explanations.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
