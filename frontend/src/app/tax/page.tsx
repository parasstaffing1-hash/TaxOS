"use client";

import Link from "next/link";
import { useEffect, useState, useMemo } from "react";
import {
  ArrowRight,
  Briefcase,
  Building2,
  Calendar,
  ChevronRight,
  Clock,
  Coins,
  FileSpreadsheet,
  Filter,
  Receipt,
  Search,
  ShieldCheck,
  Sparkles,
  TrendingUp,
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

const FEATURED_TOOLS = [
  {
    id: "income-tax-calculator",
    title: "Income Tax Calculator",
    subtitle: "New (115BAC) vs Old Regime",
    description: "Compare tax slabs for AY 2025-26 & AY 2024-25, Section 87A rebate, standard deduction, and find your optimal tax regime.",
    route: "/tax/india/income-tax-calculator",
    icon: Sparkles,
    badge: "Most Popular",
    badgeColor: "bg-[#eaf3eb] text-[#4f6f54]",
  },
  {
    id: "salary-calculator",
    title: "Salary & Take-Home Calculator",
    subtitle: "CTC to In-Hand Monthly Pay",
    description: "Convert annual CTC into exact monthly in-hand take-home salary after EPF, Professional Tax, and Income Tax deductions.",
    route: "/tax/india/salary-calculator",
    icon: Briefcase,
    badge: "Essential",
    badgeColor: "bg-[#f5f4f1] text-[#78736b]",
  },
  {
    id: "gst-calculator",
    title: "GST Calculator & Validator",
    subtitle: "Inclusive/Exclusive GST & GSTIN Check",
    description: "Calculate CGST, SGST, IGST across statutory rates (5%, 12%, 18%, 28%) and validate GSTIN formats and checksums.",
    route: "/tax/india/gst-calculator",
    icon: Receipt,
    badge: "Business",
    badgeColor: "bg-[#eef2ff] text-[#4338ca]",
  },
  {
    id: "capital-gains-calculator",
    title: "Capital Gains Tax Calculator",
    subtitle: "Budget 2024 Revised Rates",
    description: "Compute STCG (20%/15%), LTCG (12.5% with ₹1.25L exemption), real estate indexation rules, and crypto taxes.",
    route: "/tax/india/capital-gains",
    icon: TrendingUp,
    badge: "Investments",
    badgeColor: "bg-[#fef3c7] text-[#92400e]",
  },
  {
    id: "tds-tcs-calculator",
    title: "TDS & TCS Calculator",
    subtitle: "Sections 194C, 194J, 194I, 194Q & 206C",
    description: "Instant lookup for statutory TDS/TCS deduction rates, PAN validation, threshold limits, and net payable amounts.",
    route: "/tax/india/tds",
    icon: Coins,
    badge: "Compliance",
    badgeColor: "bg-[#f3e8ff] text-[#6b21a8]",
  },
  {
    id: "compliance-calendar",
    title: "Tax Compliance Calendar",
    subtitle: "Deadlines, Returns & Advance Tax",
    description: "Track statutory income tax return due dates, TDS deposit schedules, and quarterly advance tax installments.",
    route: "/tax/india/compliance",
    icon: Calendar,
    badge: "Statutory",
    badgeColor: "bg-[#eaf3eb] text-[#4f6f54]",
  },
];

const SECONDARY_TOOLS = [
  {
    title: "HRA Exemption Calculator",
    description: "Calculate tax-exempt House Rent Allowance u/s 10(13A) for metro vs non-metro cities.",
    route: "/tax/india/hra-calculator",
    icon: Building2,
  },
  {
    title: "Advance Tax & Interest (234A/B/C)",
    description: "Calculate quarterly installments (15/45/75/100%) and delay interest.",
    route: "/tax/india/advance-tax",
    icon: Clock,
  },
  {
    title: "GSTR-2B Reconciliation Engine",
    description: "Automated multi-pass invoice reconciliation for input tax credit matching.",
    route: "/tax/india/reconciliation",
    icon: FileSpreadsheet,
  },
];

const CATEGORIES = [
  "All Categories",
  "India Personal Tax",
  "Salary & CTC",
  "India GST",
  "Capital Gains",
  "TDS & TCS",
  "Compliance & Filing",
  "Global Tax",
];

export default function MasterTaxCatalogPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All Categories");
  const [catalogTools, setCatalogTools] = useState<CatalogToolItem[]>([]);
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [showFullCatalog, setShowFullCatalog] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    fetch(`${API_BASE}/catalog?limit=850`, { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error(`Catalog API status ${response.status}`);
        return response.json();
      })
      .then((tools: Array<Record<string, unknown>>) => {
        setCatalogTools(
          tools.map((tool) => ({
            id: String(tool.id),
            number: Number(tool.number),
            title: String(tool.title),
            description: String(tool.description),
            category: String(tool.family || "General"),
            jurisdiction: String(tool.jurisdiction || "Global"),
            toolType: String(tool.tool_type || "Tool"),
            route: String(tool.route || `/tax/${tool.jurisdiction || "in"}/${tool.id}`),
            tags: Array.isArray(tool.tags) ? tool.tags.map(String) : [],
            status: tool.status as CatalogToolItem["status"],
          }))
        );
        setCatalogError(null);
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setCatalogError("Live extended registry is currently in background sync mode.");
      });
    return () => controller.abort();
  }, []);

  const filteredCatalog = useMemo(() => {
    if (!catalogTools.length) return [];
    return catalogTools.filter((tool) => {
      const matchesCat =
        selectedCategory === "All Categories" ||
        tool.category.toLowerCase().includes(selectedCategory.toLowerCase());
      const q = searchQuery.toLowerCase().trim();
      const matchesQuery =
        !q ||
        tool.title.toLowerCase().includes(q) ||
        tool.description.toLowerCase().includes(q) ||
        tool.tags.some((t) => t.toLowerCase().includes(q));
      return matchesCat && matchesQuery;
    });
  }, [catalogTools, selectedCategory, searchQuery]);

  return (
    <div className="min-h-screen bg-[#fffefa] text-[#37352f]">
      {/* Header */}
      <header className="sticky top-0 z-20 flex h-14 items-center justify-between border-b border-[#f0eee9] bg-white/90 px-4 sm:px-6 backdrop-blur-md">
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
          <span className="text-xs font-medium text-[#78736b]">Tax Intelligence</span>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href="/tax/india/income-tax-calculator"
            className="rounded-lg bg-[#2f3430] px-3 py-1.5 text-xs font-medium text-white transition hover:bg-[#1e221f]"
          >
            Income Tax Calculator →
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-[1140px] px-4 sm:px-6 py-8 sm:py-12">
        {/* Hero Section */}
        <div className="mb-10 text-center sm:text-left">
          <div className="inline-flex items-center gap-2 rounded-full border border-[#dbe6dc] bg-[#f5f9f5] px-3 py-1 text-xs font-medium text-[#4f6f54] mb-3">
            <span className="inline-block h-2 w-2 rounded-full bg-[#4f6f54]" />
            Official India Tax Engine · AY 2025-26 & AY 2024-25 Ready
          </div>
          <h1 className="text-3xl font-bold tracking-tight sm:text-4xl text-[#1e221f]">
            Simple, Accurate & Deterministic Tax Calculators
          </h1>
          <p className="mt-2 max-w-2xl text-xs sm:text-sm text-[#78736b] leading-relaxed">
            Calculate income tax, optimize CTC to take-home pay, compute GST, analyze capital
            gains, and track statutory deadlines with exact government rules.
          </p>
        </div>

        {/* 6 Core Featured Calculators */}
        <div className="mb-12">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-[#78736b]">
              Primary Tax Tools
            </h2>
            <span className="text-xs text-[#9c978f]">100% Free & No Signup Required</span>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURED_TOOLS.map((tool) => {
              const Icon = tool.icon;
              return (
                <Link
                  key={tool.id}
                  href={tool.route}
                  className="group flex flex-col justify-between rounded-2xl border border-[#e8e6e1] bg-white p-5 transition hover:border-[#cbc7be] hover:shadow-md"
                >
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#faf9f7] text-[#2f3430] group-hover:bg-[#2f3430] group-hover:text-white transition">
                        <Icon className="h-5 w-5" />
                      </div>
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${tool.badgeColor}`}>
                        {tool.badge}
                      </span>
                    </div>
                    <h3 className="text-base font-bold text-[#1e221f] group-hover:text-[#2f3430]">
                      {tool.title}
                    </h3>
                    <p className="text-[11px] font-medium text-[#4f6f54] mt-0.5">
                      {tool.subtitle}
                    </p>
                    <p className="mt-2 text-xs leading-relaxed text-[#78736b]">
                      {tool.description}
                    </p>
                  </div>

                  <div className="mt-5 flex items-center justify-between border-t border-[#f7f6f3] pt-3 text-xs font-semibold text-[#2f3430] group-hover:text-[#4f6f54]">
                    <span>Calculate Now</span>
                    <ArrowRight className="h-3.5 w-3.5 group-hover:translate-x-1 transition" />
                  </div>
                </Link>
              );
            })}
          </div>
        </div>

        {/* Specialized Indian Tax Tools */}
        <div className="mb-12 rounded-2xl border border-[#e8e6e1] bg-[#faf9f7] p-6">
          <h2 className="text-sm font-semibold tracking-tight text-[#37352f] mb-3">
            Specialized Calculators & Compliance
          </h2>
          <div className="grid gap-3 sm:grid-cols-3">
            {SECONDARY_TOOLS.map((tool) => {
              const Icon = tool.icon;
              return (
                <Link
                  key={tool.title}
                  href={tool.route}
                  className="group flex items-start gap-3 rounded-xl border border-[#e8e6e1] bg-white p-3.5 transition hover:border-[#cbc7be] hover:shadow-sm"
                >
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#f5f4f1] text-[#2f3430]">
                    <Icon className="h-4 w-4" />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-[#1e221f] group-hover:text-[#4f6f54] flex items-center gap-1">
                      {tool.title}
                      <ChevronRight className="h-3 w-3 opacity-0 group-hover:opacity-100 transition" />
                    </h3>
                    <p className="mt-0.5 text-[11px] text-[#78736b] leading-tight">
                      {tool.description}
                    </p>
                  </div>
                </Link>
              );
            })}
          </div>
        </div>

        {/* Complete Extended Catalog Toggle & Search */}
        <div className="mb-12">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
            <div>
              <h2 className="text-sm font-semibold uppercase tracking-wider text-[#78736b]">
                Extended Tax Tools Catalog
              </h2>
              <p className="text-xs text-[#9c978f]">
                Browse all statutory calculators, validators, and tax rules.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setShowFullCatalog(!showFullCatalog)}
              className="self-start sm:self-auto rounded-lg border border-[#e8e6e1] bg-white px-3 py-1.5 text-xs font-medium text-[#37352f] hover:bg-[#faf9f7] transition"
            >
              {showFullCatalog ? "Hide Extended Catalog" : "Explore All Tools"}
            </button>
          </div>

          {showFullCatalog && (
            <div className="space-y-4">
              {/* Search & Category Filter */}
              <div className="flex flex-col sm:flex-row gap-3 rounded-xl border border-[#e8e6e1] bg-[#faf9f7] p-3">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-[#9c978f]" />
                  <input
                    type="text"
                    placeholder="Search by section (e.g., 87A, 194C, 115BAC, HRA) or tool name..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full rounded-lg border border-[#e0ded9] bg-white py-1.5 pl-8 pr-3 text-xs text-[#37352f] outline-none focus:border-[#2f3430]"
                  />
                </div>
                <div className="flex items-center gap-2">
                  <Filter className="h-3.5 w-3.5 text-[#9c978f]" />
                  <select
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                    className="rounded-lg border border-[#e0ded9] bg-white py-1.5 px-2.5 text-xs text-[#37352f] outline-none"
                  >
                    {CATEGORIES.map((cat) => (
                      <option key={cat} value={cat}>
                        {cat}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {catalogError && (
                <p className="text-xs text-[#a15c38]">{catalogError}</p>
              )}

              {/* Filtered Grid */}
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 max-h-[500px] overflow-y-auto pr-1">
                {filteredCatalog.map((item) => {
                  const isReady = item.status === "complete" || item.status === "partial";
                  return isReady ? (
                    <Link
                      key={item.id}
                      href={item.route}
                      className="group flex flex-col justify-between rounded-xl border border-[#e8e6e1] bg-white p-4 transition hover:border-[#cbc7be] hover:shadow-sm"
                    >
                      <div>
                        <div className="flex items-center justify-between text-[10px] text-[#9c978f] mb-1">
                          <span className="font-mono">#{item.number.toString().padStart(3, "0")}</span>
                          <span className="rounded bg-[#f0eee9] px-1.5 py-0.5 text-[#6b665e]">
                            {item.jurisdiction}
                          </span>
                        </div>
                        <h3 className="text-xs font-bold text-[#37352f] group-hover:text-[#1e221f]">
                          {item.title}
                        </h3>
                        <p className="mt-1 text-[11px] text-[#78736b] line-clamp-2">
                          {item.description}
                        </p>
                      </div>
                      <div className="mt-3 flex items-center justify-between text-[10px] font-medium text-[#4f6f54] border-t border-[#f7f6f3] pt-2">
                        <span>{item.status === "partial" ? "Open beta tool" : "Open tool"}</span>
                        <ChevronRight className="h-3 w-3" />
                      </div>
                    </Link>
                  ) : (
                    <div
                      key={item.id}
                      className="flex flex-col justify-between rounded-xl border border-[#e8e6e1] bg-[#faf9f7] p-4 opacity-75"
                    >
                      <div>
                        <div className="flex items-center justify-between text-[10px] text-[#9c978f] mb-1">
                          <span className="font-mono">#{item.number.toString().padStart(3, "0")}</span>
                          <span className="rounded bg-[#f0eee9] px-1.5 py-0.5 text-[#8f8a81]">
                            In development
                          </span>
                        </div>
                        <h3 className="text-xs font-semibold text-[#78736b]">
                          {item.title}
                        </h3>
                        <p className="mt-1 text-[11px] text-[#9c978f] line-clamp-2">
                          {item.description}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Trust and Precision Guarantee */}
        <div className="rounded-2xl border border-[#dbe6dc] bg-[#f5f9f5] p-5 sm:p-6">
          <div className="flex items-start gap-3 sm:gap-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white text-[#4f6f54] shadow-sm">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-xs sm:text-sm font-semibold text-[#2f3430]">
                Statutory Precision Guarantee & Pure Decimal Calculations
              </h3>
              <p className="mt-1 text-[11px] sm:text-xs text-[#5f6b61] leading-relaxed">
                All calculations are performed by the backend engine with zero floating-point
                rounding errors. Sourced directly from the Income-tax Act, Finance Acts, and CBDT notifications.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
