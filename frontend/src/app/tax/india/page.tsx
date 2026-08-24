"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowLeft, ArrowRight, Search, ShieldCheck } from "lucide-react";
import { API_BASE } from "@/lib/api";

interface CatalogTool {
  id: string;
  number: number;
  title: string;
  description: string;
  family: string;
  route: string;
  status: string;
  tags: string[];
}

export default function IndiaTaxHubPage() {
  const [tools, setTools] = useState<CatalogTool[]>([]);
  const [query, setQuery] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    fetch(`${API_BASE}/catalog?jurisdiction=IN&limit=850`, { signal: controller.signal })
      .then((response) => response.json())
      .then(setTools)
      .catch(() => setTools([]));
    return () => controller.abort();
  }, []);
  const filtered = tools.filter((tool) => `${tool.title} ${tool.family} ${tool.tags.join(" ")}`.toLowerCase().includes(query.toLowerCase()));
  return (
    <main className="min-h-screen bg-[#fffefa] px-6 py-8 text-[#37352f]">
      <div className="mx-auto max-w-[1180px]">
        <Link href="/tax" className="inline-flex items-center gap-1.5 text-xs text-[#78736b]"><ArrowLeft className="h-3.5 w-3.5" /> All tax tools</Link>
        <div className="mt-10 max-w-2xl"><span className="text-xs font-medium text-[#6f9476]">INDIA TAX WORKSPACE</span><h1 className="mt-2 text-4xl font-semibold tracking-[-0.05em]">India tax tools</h1><p className="mt-3 text-sm leading-6 text-[#78736b]">Income tax, salary, capital gains, GST, TDS, reconciliation, and compliance workflows in one searchable workspace.</p></div>
        <div className="relative mt-8 max-w-xl"><Search className="absolute left-3 top-3 h-4 w-4 text-[#9c978f]" /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search India tools, sections, or tags" className="w-full rounded-xl border border-[#e8e6e1] bg-white py-2.5 pl-10 pr-4 text-sm outline-none focus:border-[#78736b]" /></div>
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.slice(0, 60).map((tool) => <Link key={tool.id} href={tool.route} className="group rounded-xl border border-[#e8e6e1] bg-white p-5 hover:border-[#cbc7be] hover:shadow-sm"><div className="flex items-center justify-between"><span className="font-mono text-[11px] text-[#9c978f]">#{String(tool.number).padStart(3, "0")}</span><span className="text-[10px] uppercase text-[#9c978f]">{tool.status}</span></div><h2 className="mt-3 text-base font-semibold">{tool.title}</h2><p className="mt-1.5 line-clamp-3 text-xs leading-5 text-[#78736b]">{tool.description}</p><span className="mt-4 inline-flex items-center gap-1 text-xs font-medium text-[#4f6f54]">View tool <ArrowRight className="h-3.5 w-3.5 transition group-hover:translate-x-0.5" /></span></Link>)}
        </div>
        <div className="mt-12 flex items-center gap-2 rounded-xl border border-[#dbe6dc] bg-[#f5f9f5] p-4 text-xs text-[#4f6f54]"><ShieldCheck className="h-4 w-4" /> Planned tools remain visible with honest status labels until their API and tests are complete.</div>
      </div>
    </main>
  );
}
