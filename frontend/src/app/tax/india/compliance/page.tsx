"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowLeft, CalendarClock, CheckCircle2, Circle } from "lucide-react";
import { API_BASE } from "@/lib/api";

interface Obligation { obligation_id: string; tax_family: string; form_or_filing_name: string; frequency: string; applicable_period: string; statutory_due_date_rule: string; resolved_due_date?: string | null; consequences_of_delay: string; source_reference: string; }
interface Task { task_id: string; obligation_id: string; status: string; }

export default function IndiaCompliancePage() {
  const [obligations, setObligations] = useState<Obligation[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  useEffect(() => {
    const controller = new AbortController();
    Promise.all([
      fetch(`${API_BASE}/compliance/obligations?assessment_year=2025-26`, { signal: controller.signal }).then((response) => response.json()),
      fetch(`${API_BASE}/compliance/tasks`, { signal: controller.signal }).then((response) => response.json()),
    ]).then(([items, tracked]) => { setObligations(items); setTasks(tracked); }).catch(() => undefined);
    return () => controller.abort();
  }, []);

  async function markTracked(obligationId: string) {
    const response = await fetch(`${API_BASE}/compliance/tasks`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ obligation_id: obligationId, status: "filed_on_time" }) });
    if (response.ok) {
      const task = await response.json();
      setTasks((current) => [...current, task]);
    }
  }

  return <main className="min-h-screen bg-[#fffefa] px-6 py-8 text-[#37352f]"><div className="mx-auto max-w-[1050px]"><Link href="/tax/india" className="inline-flex items-center gap-1.5 text-xs text-[#78736b]"><ArrowLeft className="h-3.5 w-3.5" /> India tax tools</Link><div className="mt-10 flex items-start justify-between gap-4"><div><span className="inline-flex items-center gap-2 text-xs font-medium text-[#6f9476]"><CalendarClock className="h-3.5 w-3.5" /> COMPLIANCE WORKSPACE</span><h1 className="mt-2 text-3xl font-semibold tracking-[-0.04em]">India compliance calendar</h1><p className="mt-2 text-sm text-[#78736b]">Assessment Year 2025-26 · versioned obligation rules with trackable filing state.</p></div></div><div className="mt-8 space-y-3">{obligations.map((item) => { const tracked = tasks.some((task) => task.obligation_id === item.obligation_id); return <article key={item.obligation_id} className="rounded-xl border border-[#e8e6e1] bg-white p-5"><div className="flex flex-wrap items-start justify-between gap-4"><div><div className="text-[10px] uppercase tracking-wider text-[#9c978f]">{item.tax_family} · {item.frequency}</div><h2 className="mt-1 text-sm font-semibold">{item.form_or_filing_name}</h2><p className="mt-1 text-xs text-[#78736b]">{item.applicable_period} · {item.resolved_due_date ? `Due ${item.resolved_due_date}` : item.statutory_due_date_rule}</p></div><button type="button" onClick={() => void markTracked(item.obligation_id)} disabled={tracked} className="inline-flex items-center gap-1.5 rounded-lg border border-[#e0ded9] px-3 py-2 text-xs font-medium disabled:cursor-default disabled:bg-[#f5f9f5] disabled:text-[#4f6f54]">{tracked ? <CheckCircle2 className="h-3.5 w-3.5" /> : <Circle className="h-3.5 w-3.5" />}{tracked ? "Tracked" : "Track obligation"}</button></div><p className="mt-3 border-t border-[#f7f6f3] pt-3 text-[11px] text-[#8f8a81]">{item.consequences_of_delay} · Source: {item.source_reference}</p></article>; })}</div></div></main>;
}
