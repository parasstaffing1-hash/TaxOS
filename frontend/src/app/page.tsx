"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  ArrowRight,
  BarChart3,
  Calculator,
  ChevronDown,
  Clock3,
  FileText,
  HelpCircle,
  Landmark,
  Menu,
  MoreHorizontal,
  PanelLeft,
  Plus,
  Search,
  Settings2,
  ShieldCheck,
  Sparkles,
  Star,
  X,
} from "lucide-react";

import SearchAutocomplete from "@/components/calculator/SearchAutocomplete";

const calculators = [
  {
    title: "India Income Tax (AY 2025-26)",
    description: "Old vs New regime comparator with Sec 87A rebate & marginal relief.",
    href: "/tax/india/income-tax-calculator",
    icon: Calculator,
    iconClass: "bg-[#e9f3ec] text-[#4c8c62]",
    updated: "AY 2025-26 Live",
  },
  {
    title: "GST Inclusive / Exclusive Calculator",
    description: "CGST/SGST/IGST split and 15-digit GSTIN checksum validator.",
    href: "/tax/india/gst-calculator",
    icon: Landmark,
    iconClass: "bg-[#f6eddf] text-[#ba7b35]",
    updated: "Rule 46 verified",
  },
  {
    title: "GSTR-2B vs Books Reconciliation",
    description: "Multi-pass invoice matcher with tolerance & variance classification.",
    href: "/tax/india/reconciliation",
    icon: BarChart3,
    iconClass: "bg-[#e9eef7] text-[#5977ae]",
    updated: "Auto-Match",
  },
  {
    title: "Paycheck Calculator (US/Global)",
    description: "See your net paycheck after taxes and deductions.",
    href: "/calculators/paycheck-calculator",
    icon: Landmark,
    iconClass: "bg-[#f5f8fc] text-[#5977ae]",
    updated: "2024 Rates",
  },
];

const navItems = [
  { label: "Home", icon: PanelLeft, active: true },
  { label: "Tax Catalog (845+)", icon: Calculator, href: "/tax" },
  { label: "India Tax Engine", icon: Landmark, href: "/tax/india/income-tax-calculator" },
  { label: "GST & Invoicing", icon: Landmark, href: "/tax/india/gst-calculator" },
  { label: "Reconciliation", icon: BarChart3, href: "/tax/india/reconciliation" },
  { label: "Analytics", icon: BarChart3, href: "/analytics" },
];


type SidebarProps = {
  onClose?: () => void;
  onQuickFind?: () => void;
  onUpdates?: () => void;
};

function Sidebar({ onClose, onQuickFind, onUpdates }: SidebarProps) {
  return (
    <aside className="flex h-full w-[248px] shrink-0 flex-col border-r border-[#e8e6e1] bg-[#f7f6f3] px-3 py-3 text-[#57534e]">
      <div className="flex items-center justify-between px-2 pb-5">
        <Link href="/" className="flex items-center gap-2.5 text-[15px] font-semibold tracking-[-0.01em] text-[#37352f]">
          <span className="flex h-7 w-7 items-center justify-center rounded-[7px] bg-[#2f3430] text-[13px] font-bold text-white">T</span>
          TaxOS
          <ChevronDown className="h-3.5 w-3.5 text-[#9b9891]" strokeWidth={2.2} />
        </Link>
        {onClose && (
          <button aria-label="Close sidebar" onClick={onClose} className="rounded-md p-1.5 text-[#78736b] hover:bg-[#ebe9e4] lg:hidden">
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      <div className="space-y-1 px-1">
        <button className="notion-sidebar-row w-full" type="button" onClick={onQuickFind}>
          <Search className="h-4 w-4 text-[#8d8981]" />
          <span>Quick find</span>
          <span className="ml-auto rounded border border-[#dedbd5] px-1.5 py-0.5 text-[10px] text-[#a5a19a]">⌘ K</span>
        </button>
        <button className="notion-sidebar-row w-full" type="button" onClick={onUpdates}>
          <Clock3 className="h-4 w-4 text-[#8d8981]" />
          <span>Updates</span>
        </button>
      </div>

      <div className="mt-7 px-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-[#a09c94]">Workspace</div>
      <nav className="mt-2 space-y-0.5 px-1" aria-label="Workspace navigation">
        {navItems.map((item) => {
          const Icon = item.icon;
          const row = (
            <span className={`notion-sidebar-row ${item.active ? "notion-sidebar-row-active" : ""}`}>
              <Icon className="h-4 w-4" />
              <span>{item.label}</span>
            </span>
          );
          return item.href ? <Link href={item.href} key={item.label}>{row}</Link> : <div key={item.label}>{row}</div>;
        })}
      </nav>

      <div className="mt-7 px-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-[#a09c94]">Favorites</div>
      <div className="mt-2 space-y-0.5 px-1">
        <Link href="/calculators/income-tax-calculator" className="notion-sidebar-row">
          <span className="h-2 w-2 rounded-full bg-[#70a37d]" />
          Income tax overview
        </Link>
        <Link href="/calculators/paycheck-calculator" className="notion-sidebar-row">
          <span className="h-2 w-2 rounded-full bg-[#d6a363]" />
          2024 paycheck notes
        </Link>
      </div>

      <div className="mt-auto space-y-1 px-1">
        <Link href="/org/taxos/settings" className="notion-sidebar-row">
          <Settings2 className="h-4 w-4" />
          Settings
        </Link>
        <button className="notion-sidebar-row w-full" type="button">
          <HelpCircle className="h-4 w-4" />
          Help & resources
        </button>
        <div className="mt-3 flex items-center gap-2 rounded-lg px-2 py-2.5 hover:bg-[#ebe9e4]">
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-[#dbe4da] text-xs font-semibold text-[#4d6d50]">PS</span>
          <div className="min-w-0 flex-1">
            <div className="truncate text-xs font-medium text-[#45413b]">Personal workspace</div>
            <div className="truncate text-[11px] text-[#9a968f]">Free plan</div>
          </div>
          <MoreHorizontal className="h-4 w-4 text-[#9a968f]" />
        </div>
      </div>
    </aside>
  );
}

function StatCard({ label, value, detail, tone }: { label: string; value: string; detail: string; tone: "green" | "orange" | "blue" }) {
  const toneClasses = {
    green: "border-[#dbe8dd] bg-[#f5faf5]",
    orange: "border-[#eee1d0] bg-[#fcf8f1]",
    blue: "border-[#dce4f1] bg-[#f5f8fc]",
  };
  return (
    <div className={`rounded-xl border p-4 ${toneClasses[tone]}`}>
      <div className="text-[11px] font-medium uppercase tracking-[0.06em] text-[#858078]">{label}</div>
      <div className="mt-2 text-[26px] font-semibold tracking-[-0.04em] text-[#37352f]">{value}</div>
      <div className="mt-1 text-xs text-[#8b867e]">{detail}</div>
    </div>
  );
}

function QuickFindDialog({
  query,
  onQueryChange,
  onClose,
}: {
  query: string;
  onQueryChange: (value: string) => void;
  onClose: () => void;
}) {
  const matches = calculators.filter((calculator) =>
    `${calculator.title} ${calculator.description}`.toLowerCase().includes(query.trim().toLowerCase()),
  );

  return (
    <div
      className="fixed inset-0 z-[60] flex items-start justify-center bg-[#37352f]/25 px-4 pt-[12vh] backdrop-blur-[2px]"
      role="presentation"
      onMouseDown={onClose}
    >
      <div
        className="w-full max-w-xl overflow-hidden rounded-xl border border-[#dedbd5] bg-white shadow-[0_18px_60px_rgba(55,53,47,0.18)]"
        role="dialog"
        aria-modal="true"
        aria-label="Quick find"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="flex items-center gap-3 border-b border-[#f0eee9] px-4 py-3">
          <Search className="h-4 w-4 text-[#9a968f]" />
          <input
            autoFocus
            value={query}
            onChange={(event) => onQueryChange(event.target.value)}
            onKeyDown={(event) => event.key === "Escape" && onClose()}
            placeholder="Search your workspace..."
            aria-label="Search your workspace"
            className="min-w-0 flex-1 bg-transparent text-sm text-[#37352f] outline-none placeholder:text-[#aaa69f]"
          />
          <button type="button" onClick={onClose} className="rounded border border-[#dedbd5] px-1.5 py-0.5 text-[10px] text-[#9a968f] hover:bg-[#f7f6f3]">
            ESC
          </button>
        </div>
        <div className="max-h-[min(420px,55vh)] overflow-y-auto p-2">
          <div className="px-2 pb-2 pt-1 text-[10px] font-semibold uppercase tracking-[0.08em] text-[#aaa69f]">Calculators</div>
          {matches.length > 0 ? matches.map((calculator) => {
            const Icon = calculator.icon;
            return (
              <Link
                key={calculator.title}
                href={calculator.href}
                onClick={onClose}
                className="flex items-center gap-3 rounded-lg px-2 py-2.5 hover:bg-[#f7f6f3]"
              >
                <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${calculator.iconClass}`}><Icon className="h-4 w-4" /></span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm font-medium text-[#4a4640]">{calculator.title}</span>
                  <span className="block truncate text-xs text-[#9a968f]">{calculator.description}</span>
                </span>
                <ArrowRight className="h-3.5 w-3.5 text-[#b6b2aa]" />
              </Link>
            );
          }) : <div className="px-2 py-8 text-center text-sm text-[#9a968f]">No calculators found.</div>}
        </div>
        <div className="border-t border-[#f0eee9] bg-[#faf9f7] px-4 py-2 text-[11px] text-[#aaa69f]">Search is limited to your saved workspace shortcuts for now.</div>
      </div>
    </div>
  );
}

function UpdatesDialog({ onClose }: { onClose: () => void }) {
  return (
    <div
      className="fixed inset-0 z-[60] flex items-start justify-end bg-[#37352f]/10 px-4 pt-16 sm:px-8"
      role="presentation"
      onMouseDown={onClose}
    >
      <div
        className="w-full max-w-sm overflow-hidden rounded-xl border border-[#dedbd5] bg-white shadow-[0_18px_60px_rgba(55,53,47,0.14)]"
        role="dialog"
        aria-modal="true"
        aria-label="Workspace updates"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-[#f0eee9] px-4 py-3">
          <div><div className="text-sm font-semibold text-[#37352f]">Workspace updates</div><div className="mt-0.5 text-xs text-[#9a968f]">A short changelog from TaxOS</div></div>
          <button type="button" onClick={onClose} aria-label="Close updates" className="notion-icon-button"><X className="h-4 w-4" /></button>
        </div>
        <div className="space-y-3 p-4">
          <div className="rounded-lg bg-[#f5faf5] p-3"><div className="text-xs font-semibold text-[#4f6f54]">Today</div><div className="mt-1 text-sm text-[#4a4640]">R2-ready document storage and Aiven database support are ready for launch configuration.</div></div>
          <div className="rounded-lg bg-[#f7f6f3] p-3"><div className="text-xs font-semibold text-[#77726a]">Current coverage</div><div className="mt-1 text-sm text-[#4a4640]">16 verified calculators are released; the rest remain safely marked as planned.</div></div>
        </div>
      </div>
    </div>
  );
}

export default function Home() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [quickFindOpen, setQuickFindOpen] = useState(false);
  const [quickFindQuery, setQuickFindQuery] = useState("");
  const [updatesOpen, setUpdatesOpen] = useState(false);
  const [favorite, setFavorite] = useState(false);
  const [noteOpen, setNoteOpen] = useState(false);

  useEffect(() => {
    const handleShortcut = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setQuickFindOpen(true);
        setUpdatesOpen(false);
      }
      if (event.key === "Escape") {
        setQuickFindOpen(false);
        setUpdatesOpen(false);
      }
    };

    window.addEventListener("keydown", handleShortcut);
    return () => window.removeEventListener("keydown", handleShortcut);
  }, []);

  const openQuickFind = () => {
    setQuickFindQuery("");
    setQuickFindOpen(true);
    setUpdatesOpen(false);
    setSidebarOpen(false);
  };

  const openUpdates = () => {
    setUpdatesOpen(true);
    setQuickFindOpen(false);
    setSidebarOpen(false);
  };

  return (
    <div className="notion-app-shell">
      {quickFindOpen && <QuickFindDialog query={quickFindQuery} onQueryChange={setQuickFindQuery} onClose={() => setQuickFindOpen(false)} />}
      {updatesOpen && <UpdatesDialog onClose={() => setUpdatesOpen(false)} />}
      <div className={`notion-sidebar-overlay ${sidebarOpen ? "notion-sidebar-overlay-visible" : ""}`} onClick={() => setSidebarOpen(false)} />
      <div className={`notion-sidebar-drawer ${sidebarOpen ? "notion-sidebar-drawer-open" : ""}`}>
        <Sidebar onClose={() => setSidebarOpen(false)} onQuickFind={openQuickFind} onUpdates={openUpdates} />
      </div>
      <div className="hidden lg:block">
        <Sidebar onQuickFind={openQuickFind} onUpdates={openUpdates} />
      </div>

      <main className="min-w-0 flex-1 bg-[#fffefa]">
        <header className="flex h-14 items-center justify-between border-b border-[#f0eee9] px-5 sm:px-8">
          <div className="flex items-center gap-2 text-xs text-[#a09c94]">
            <button aria-label="Open sidebar" onClick={() => setSidebarOpen(true)} className="rounded-md p-1.5 text-[#77726a] hover:bg-[#f0eee9] lg:hidden">
              <Menu className="h-4 w-4" />
            </button>
            <span className="hidden sm:inline">Personal workspace</span>
            <span className="hidden text-[#d2cfc8] sm:inline">/</span>
            <span className="font-medium text-[#6e6961]">Home</span>
          </div>
          <div className="flex items-center gap-1">
            <Link href="/login" className="notion-quiet-button hidden sm:inline-flex">Sign in</Link>
            <Link href="/register" className="notion-dark-button">Get started <ArrowRight className="h-3.5 w-3.5" /></Link>
          </div>
        </header>

        <div className="mx-auto max-w-[1120px] px-5 py-8 sm:px-8 sm:py-12">
          <div className="mb-10 flex items-start justify-between gap-5">
            <div>
              <div className="mb-3 flex items-center gap-2 text-xs text-[#aaa69f]"><span className="inline-block h-2 w-2 rounded-full bg-[#7ba583]" /> Workspace overview</div>
              <h1 className="text-[38px] font-semibold leading-tight tracking-[-0.045em] text-[#37352f] sm:text-[46px]">Good morning, Paras</h1>
              <p className="mt-3 max-w-xl text-[15px] leading-7 text-[#858078]">A calm place to understand your taxes, explore scenarios, and keep your payroll decisions in one place.</p>
            </div>
            <button type="button" className="notion-icon-button hidden sm:flex" aria-label={favorite ? "Remove from favorites" : "Add to favorites"} aria-pressed={favorite} onClick={() => setFavorite((value) => !value)}><Star className={`h-4 w-4 ${favorite ? "fill-[#d6a363] text-[#ba7b35]" : ""}`} /></button>
          </div>

          <section className="notion-callout mb-8" aria-label="Workspace search">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white text-[#77726a] shadow-sm"><Sparkles className="h-4 w-4" /></div>
            <div className="min-w-0 flex-1">
              <div className="mb-2 text-sm font-medium text-[#4d4942]">What would you like to calculate?</div>
              <SearchAutocomplete />
            </div>
            <div className="hidden items-center gap-1.5 text-[11px] text-[#a09c94] md:flex"><span className="rounded border border-[#dedbd5] bg-white px-1.5 py-0.5">⌘</span>K</div>
          </section>

          <section className="mb-10" aria-labelledby="overview-heading">
            <div className="mb-3 flex items-center justify-between">
              <h2 id="overview-heading" className="notion-section-title">Overview</h2>
              <button type="button" className="notion-link-button">Customize <Settings2 className="h-3.5 w-3.5" /></button>
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              <StatCard label="Calculations" value="12" detail="3 saved this week" tone="green" />
              <StatCard label="Estimated take-home" value="$6,840" detail="Based on your last scenario" tone="orange" />
              <StatCard label="Effective tax rate" value="24.6%" detail="Down 1.2% from last month" tone="blue" />
            </div>
          </section>

          <section aria-labelledby="calculators-heading">
            <div className="mb-3 flex items-center justify-between">
              <h2 id="calculators-heading" className="notion-section-title">Your calculators</h2>
              <Link href="/calculators/income-tax-calculator" className="notion-link-button">View all <ArrowRight className="h-3.5 w-3.5" /></Link>
            </div>
            <div className="overflow-hidden rounded-xl border border-[#e8e6e1] bg-white">
              <div className="hidden grid-cols-[minmax(0,1.7fr)_minmax(180px,1fr)_100px_32px] gap-4 border-b border-[#f0eee9] bg-[#faf9f7] px-4 py-2.5 text-[10px] font-semibold uppercase tracking-[0.08em] text-[#aaa69f] sm:grid">
                <span>Name</span><span>Description</span><span>Updated</span><span />
              </div>
              {calculators.map((calculator) => {
                const Icon = calculator.icon;
                return (
                  <Link key={calculator.title} href={calculator.href} className="group grid gap-3 border-b border-[#f0eee9] px-4 py-3.5 transition-colors last:border-b-0 hover:bg-[#faf9f7] sm:grid-cols-[minmax(0,1.7fr)_minmax(180px,1fr)_100px_32px] sm:items-center sm:gap-4">
                    <div className="flex min-w-0 items-center gap-3">
                      <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${calculator.iconClass}`}><Icon className="h-4 w-4" /></span>
                      <span className="truncate text-sm font-medium text-[#4a4640] group-hover:text-[#2f3430]">{calculator.title}</span>
                    </div>
                    <span className="truncate pl-11 text-xs text-[#96918a] sm:pl-0">{calculator.description}</span>
                    <span className="pl-11 text-xs text-[#aaa69f] sm:pl-0">{calculator.updated}</span>
                    <MoreHorizontal className="hidden h-4 w-4 justify-self-end text-[#b6b2aa] sm:block" />
                  </Link>
                );
              })}
              <Link href="/calculators/income-tax-calculator" className="flex items-center gap-2 px-4 py-3 text-xs font-medium text-[#868078] transition-colors hover:bg-[#faf9f7] hover:text-[#4d4942]"><Plus className="h-4 w-4" /> Add a calculator</Link>
            </div>
          </section>

          <section className="mt-10 grid gap-3 md:grid-cols-[1.4fr_1fr]">
            <div className="rounded-xl border border-[#e8e6e1] bg-[#f8f7f4] p-5">
              <div className="flex items-start gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white text-[#66806d] shadow-sm"><ShieldCheck className="h-4 w-4" /></div>
                <div><h3 className="text-sm font-medium text-[#4a4640]">Built for confident decisions</h3><p className="mt-1.5 text-xs leading-5 text-[#8b867e]">TaxOS keeps every estimate transparent, with clear assumptions and a breakdown you can actually understand.</p></div>
              </div>
              <Link href="/analytics" className="mt-4 inline-flex items-center gap-1.5 text-xs font-medium text-[#5b7461] hover:text-[#3e5c45]">Explore analytics <ArrowRight className="h-3.5 w-3.5" /></Link>
            </div>
            <div className="rounded-xl border border-[#e8e6e1] bg-white p-5">
              <div className="flex items-center gap-2 text-[#77726a]"><FileText className="h-4 w-4" /><span className="text-xs font-medium">Recent note</span></div>
              <p className="mt-3 text-sm font-medium text-[#4a4640]">2024 filing assumptions</p>
              <p className="mt-1 text-xs leading-5 text-[#98938c]">Review your saved deductions before running a new scenario.</p>
              <button type="button" onClick={() => setNoteOpen((value) => !value)} className="mt-4 text-xs font-medium text-[#77726a] hover:text-[#37352f]">{noteOpen ? "Close note ↑" : "Open note →"}</button>
              {noteOpen && <div className="mt-3 rounded-lg bg-[#faf9f7] p-3 text-xs leading-5 text-[#77726a]">Before a new scenario, confirm your assessment year, standard deduction, and eligible Chapter VI-A claims.</div>}
            </div>
          </section>

          <footer className="mt-14 flex flex-col gap-2 border-t border-[#f0eee9] pt-5 text-[11px] text-[#aaa69f] sm:flex-row sm:items-center sm:justify-between">
            <span>TaxOS · Personal workspace</span>
            <span>Tax rules verified for 2024</span>
          </footer>
        </div>
      </main>
    </div>
  );
}
