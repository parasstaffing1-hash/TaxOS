"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowLeft, CheckCircle2, Clock3, ExternalLink, ShieldCheck } from "lucide-react";
import { API_BASE } from "@/lib/api";

type ToolStatus = "complete" | "partial" | "not_started" | "blocked";

interface CatalogTool {
  id: string;
  number: number;
  title: string;
  description: string;
  family: string;
  jurisdiction: string;
  tool_type: string;
  route: string;
  api_endpoint: string | null;
  status: ToolStatus;
  tags: string[];
}

function statusLabel(status: ToolStatus): string {
  return status === "not_started" ? "Planned" : status.replace("_", " ");
}

export default function CatalogToolPage() {
  const params = useParams<{ jurisdiction: string; tool: string }>();
  const toolSlug = Array.isArray(params.tool) ? params.tool[0] : params.tool;
  const [tool, setTool] = useState<CatalogTool | null>(null);
  const [loading, setLoading] = useState(true);
  const [amount, setAmount] = useState("1000");
  const [country, setCountry] = useState("US");
  const [taxType, setTaxType] = useState("income_tax");
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    fetch(`${API_BASE}/catalog/${encodeURIComponent(toolSlug)}`, { signal: controller.signal })
      .then((response) => (response.ok ? response.json() : null))
      .then((result: CatalogTool | null) => setTool(result))
      .catch(() => setTool(null))
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, [toolSlug]);

  useEffect(() => {
    if (!tool) return;
    setTaxType(tool.id.includes("vat") || tool.id.includes("gst") ? "vat_gst" : "income_tax");
  }, [tool]);

  async function calculateGlobalTool() {
    if (!tool?.api_endpoint) return;
    setSubmitting(true);
    try {
      const endpoint = tool.api_endpoint.replace(/^\/api\/v1/, "");
      const response = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ country_code: country, gross_income_or_revenue: amount, tax_type: taxType }),
      });
      setResult(response.ok ? await response.json() : { error: `Request failed (${response.status})` });
    } catch {
      setResult({ error: "The calculation API is unavailable." });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#fffefa] px-6 py-8 text-[#37352f]">
      <div className="mx-auto max-w-[920px]">
        <Link href="/tax" className="inline-flex items-center gap-1.5 text-xs text-[#78736b] hover:text-[#37352f]">
          <ArrowLeft className="h-3.5 w-3.5" /> All tax tools
        </Link>

        {loading && <div className="mt-12 rounded-xl border border-[#e8e6e1] bg-white p-8 text-sm text-[#78736b]">Loading tool metadata…</div>}

        {!loading && !tool && (
          <div className="mt-12 rounded-xl border border-[#ecd7d0] bg-[#fff9f7] p-8">
            <h1 className="text-xl font-semibold">Tool not found</h1>
            <p className="mt-2 text-sm text-[#78736b]">This route is not present in the TaxOS catalog.</p>
          </div>
        )}

        {tool && (
          <section className="mt-10 rounded-2xl border border-[#e8e6e1] bg-white p-7 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <span className="font-mono text-xs text-[#8f8a81]">#{String(tool.number).padStart(3, "0")}</span>
              <span className={`rounded-full px-2.5 py-1 text-[11px] font-medium ${
                tool.status === "complete"
                  ? "bg-[#eaf3eb] text-[#4f6f54]"
                  : tool.status === "partial"
                    ? "bg-[#fff3df] text-[#9a6a2f]"
                    : "bg-[#f5f4f1] text-[#78736b]"
              }`}>
                {statusLabel(tool.status)}
              </span>
            </div>
            <h1 className="mt-4 text-3xl font-semibold tracking-[-0.04em]">{tool.title}</h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-[#78736b]">{tool.description}</p>

            <div className="mt-7 grid gap-3 sm:grid-cols-3">
              <div className="rounded-xl bg-[#faf9f7] p-4"><span className="text-[10px] uppercase text-[#9c978f]">Family</span><div className="mt-1 text-sm font-medium">{tool.family.replaceAll("_", " ")}</div></div>
              <div className="rounded-xl bg-[#faf9f7] p-4"><span className="text-[10px] uppercase text-[#9c978f]">Jurisdiction</span><div className="mt-1 text-sm font-medium">{tool.jurisdiction}</div></div>
              <div className="rounded-xl bg-[#faf9f7] p-4"><span className="text-[10px] uppercase text-[#9c978f]">Type</span><div className="mt-1 text-sm font-medium">{tool.tool_type}</div></div>
            </div>

            {tool.api_endpoint === "/api/v1/global/calculate" && (
              <div className="mt-7 rounded-xl border border-[#e8e6e1] bg-[#faf9f7] p-5">
                <div className="text-xs font-semibold uppercase tracking-wider text-[#78736b]">Try the rule-pack API</div>
                <div className="mt-3 grid gap-3 sm:grid-cols-3">
                  <label className="text-xs text-[#78736b]">Country<select value={country} onChange={(event) => setCountry(event.target.value)} className="mt-1 w-full rounded-lg border border-[#e0ded9] bg-white px-3 py-2 text-sm text-[#37352f]"><option value="US">United States</option><option value="GB">United Kingdom</option><option value="AE">United Arab Emirates</option><option value="CA">Canada</option><option value="AU">Australia</option><option value="SG">Singapore</option><option value="DE">Germany</option><option value="FR">France</option></select></label>
                  <label className="text-xs text-[#78736b]">Tax type<select value={taxType} onChange={(event) => setTaxType(event.target.value)} className="mt-1 w-full rounded-lg border border-[#e0ded9] bg-white px-3 py-2 text-sm text-[#37352f]"><option value="income_tax">Income tax</option><option value="corporate_tax">Corporate tax</option><option value="vat_gst">VAT/GST</option></select></label>
                  <label className="text-xs text-[#78736b]">Gross amount<input value={amount} onChange={(event) => setAmount(event.target.value)} inputMode="decimal" className="mt-1 w-full rounded-lg border border-[#e0ded9] bg-white px-3 py-2 text-sm text-[#37352f]" /></label>
                </div>
                <button type="button" onClick={() => void calculateGlobalTool()} disabled={submitting} className="mt-4 rounded-lg bg-[#2f3430] px-4 py-2 text-xs font-medium text-white disabled:opacity-60">{submitting ? "Calculating…" : "Calculate"}</button>
                {result && <pre className="mt-4 overflow-auto rounded-lg bg-[#2f3430] p-4 text-[11px] leading-5 text-[#eef4ee]">{JSON.stringify(result, null, 2)}</pre>}
              </div>
            )}

            <div className="mt-7 border-t border-[#f0eee9] pt-5">
              {tool.status === "complete" && tool.route !== `/tax/${params.jurisdiction}/${toolSlug}` ? (
                <Link href={tool.route} className="inline-flex items-center gap-2 rounded-lg bg-[#2f3430] px-4 py-2.5 text-xs font-medium text-white hover:bg-[#1e221f]">
                  <CheckCircle2 className="h-4 w-4" /> Open verified workflow <ExternalLink className="h-3.5 w-3.5" />
                </Link>
              ) : tool.status === "partial" ? (
                <div className="flex items-start gap-2 rounded-lg bg-[#fff8ec] p-4 text-xs text-[#8a632e]"><Clock3 className="mt-0.5 h-4 w-4 shrink-0" /><span>This tool has a working foundation, but its dedicated workflow is still being completed.</span></div>
              ) : (
                <div className="flex items-start gap-2 rounded-lg bg-[#f5f4f1] p-4 text-xs text-[#78736b]"><ShieldCheck className="mt-0.5 h-4 w-4 shrink-0" /><span>This tool is in the TaxOS roadmap and is not yet available for production calculations.</span></div>
              )}
              {tool.api_endpoint && <p className="mt-4 font-mono text-[11px] text-[#9c978f]">API: {tool.api_endpoint}</p>}
            </div>
          </section>
        )}
      </div>
    </main>
  );
}
