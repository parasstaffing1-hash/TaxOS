"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import {
  ArrowLeft,
  BookOpen,
  Calculator,
  CheckCircle2,
  ExternalLink,
  Info,
  Sparkles,
} from "lucide-react";
import { API_BASE } from "@/lib/api";

interface InputFieldSpec {
  name: string;
  label: string;
  field_type: "number" | "text" | "select" | "boolean";
  default_value: unknown;
  min_value?: number;
  max_value?: number;
  step?: number;
  options?: { label: string; value: string }[];
  unit?: string;
  tooltip?: string;
  required?: boolean;
}

interface OfficialSource {
  source_id: string;
  title: string;
  section_or_rule: string;
  act_name: string;
  url?: string;
  effective_date?: string;
}

interface ToolSpec {
  tool_id: string;
  number: number;
  title: string;
  family: string;
  jurisdiction: string;
  tool_type: string;
  description: string;
  input_fields: InputFieldSpec[];
  official_sources: OfficialSource[];
}

interface CalculationStep {
  step_number: number;
  label: string;
  formula_or_rule: string;
  result: string | number;
  applied_rate_or_limit?: string | number | null;
  notes?: string | null;
}

interface CalculationResponse {
  calculation_id: string;
  jurisdiction: string;
  tax_type: string;
  tax_year: string;
  rule_version: string;
  effective_date: string;
  calculation: Record<string, string>;
  steps?: CalculationStep[];
  warnings?: string[];
  assumptions?: string[];
  official_sources?: OfficialSource[];
}

export default function CatalogToolPage() {
  const params = useParams<{ jurisdiction: string; tool: string }>();
  const toolSlug = Array.isArray(params.tool) ? params.tool[0] : params.tool;

  const [spec, setSpec] = useState<ToolSpec | null>(null);
  const [formValues, setFormValues] = useState<Record<string, unknown>>({});
  const [loading, setLoading] = useState(true);
  const [calculating, setCalculating] = useState(false);
  const [calcResult, setCalcResult] = useState<CalculationResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetch(`${API_BASE}/catalog/${encodeURIComponent(toolSlug)}/schema`, {
      signal: controller.signal,
    })
      .then((res) => (res.ok ? res.json() : null))
      .then((data: ToolSpec | null) => {
        if (data) {
          setSpec(data);
          const initial: Record<string, unknown> = {};
          data.input_fields.forEach((field) => {
            initial[field.name] = field.default_value;
          });
          setFormValues(initial);
        }
      })
      .catch(() => setSpec(null))
      .finally(() => setLoading(false));

    return () => controller.abort();
  }, [toolSlug]);

  const handleInputChange = (name: string, value: unknown) => {
    setFormValues((prev) => ({ ...prev, [name]: value }));
  };

  const handleCalculate = async () => {
    if (!spec) return;
    setCalculating(true);
    setErrorMessage(null);
    try {
      const res = await fetch(
        `${API_BASE}/catalog/${encodeURIComponent(toolSlug)}/calculate`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(formValues),
        }
      );
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail || `Calculation failed (${res.status})`);
      }
      const data: CalculationResponse = await res.json();
      setCalcResult(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to execute calculation";
      setErrorMessage(msg);
    } finally {
      setCalculating(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#fffefa] px-6 py-8 text-[#37352f]">
      <div className="mx-auto max-w-[960px]">
        <Link
          href="/tax"
          className="inline-flex items-center gap-1.5 text-xs text-[#78736b] hover:text-[#37352f]"
        >
          <ArrowLeft className="h-3.5 w-3.5" /> All Tax Tools & Calculators
        </Link>

        {loading && (
          <div className="mt-12 rounded-xl border border-[#e8e6e1] bg-white p-8 text-sm text-[#78736b]">
            Loading interactive tool specification…
          </div>
        )}

        {!loading && !spec && (
          <div className="mt-12 rounded-xl border border-[#ecd7d0] bg-[#fff9f7] p-8">
            <h1 className="text-xl font-semibold">Tool Not Found</h1>
            <p className="mt-2 text-sm text-[#78736b]">
              The requested tool identifier `{toolSlug}` is not present in the catalog.
            </p>
          </div>
        )}

        {spec && (
          <div className="mt-8 space-y-8">
            {/* Header section */}
            <section className="rounded-2xl border border-[#e8e6e1] bg-white p-7 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <span className="font-mono text-xs text-[#8f8a81]">
                  Tool #{String(spec.number).padStart(3, "0")}
                </span>
                <span className="inline-flex items-center gap-1.5 rounded-full bg-[#eaf3eb] px-2.5 py-1 text-[11px] font-medium text-[#4f6f54]">
                  <CheckCircle2 className="h-3.5 w-3.5" /> Production Ready
                </span>
              </div>
              <h1 className="mt-4 text-3xl font-semibold tracking-[-0.04em]">
                {spec.title}
              </h1>
              <p className="mt-3 max-w-2xl text-sm leading-6 text-[#78736b]">
                {spec.description}
              </p>

              <div className="mt-6 grid gap-3 sm:grid-cols-3">
                <div className="rounded-xl bg-[#faf9f7] p-3.5">
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-[#9c978f]">
                    Family
                  </span>
                  <div className="mt-1 text-sm font-medium">
                    {spec.family.replaceAll("_", " ")}
                  </div>
                </div>
                <div className="rounded-xl bg-[#faf9f7] p-3.5">
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-[#9c978f]">
                    Jurisdiction
                  </span>
                  <div className="mt-1 text-sm font-medium">
                    {spec.jurisdiction}
                  </div>
                </div>
                <div className="rounded-xl bg-[#faf9f7] p-3.5">
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-[#9c978f]">
                    Tool Type
                  </span>
                  <div className="mt-1 text-sm font-medium">
                    {spec.tool_type.toUpperCase()}
                  </div>
                </div>
              </div>
            </section>

            {/* Interactive Calculator Form */}
            <section className="rounded-2xl border border-[#e8e6e1] bg-white p-7 shadow-sm">
              <div className="flex items-center gap-2 border-b border-[#f0eee9] pb-4">
                <Calculator className="h-5 w-5 text-[#2f3430]" />
                <h2 className="text-lg font-semibold tracking-tight">
                  Interactive Calculator & Verification
                </h2>
              </div>

              <div className="mt-6 grid gap-5 sm:grid-cols-2">
                {spec.input_fields.map((field) => (
                  <div key={field.name} className="space-y-1.5">
                    <label className="text-xs font-medium text-[#4f4b43]">
                      {field.label}
                    </label>
                    {field.field_type === "select" ? (
                      <select
                        value={String(formValues[field.name] ?? "")}
                        onChange={(e) =>
                          handleInputChange(field.name, e.target.value)
                        }
                        className="w-full rounded-xl border border-[#e0ded9] bg-white px-3.5 py-2.5 text-sm text-[#37352f] shadow-sm outline-none transition focus:border-[#2f3430]"
                      >
                        {field.options?.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    ) : field.field_type === "boolean" ? (
                      <div className="pt-2">
                        <label className="inline-flex cursor-pointer items-center gap-2.5 text-sm text-[#37352f]">
                          <input
                            type="checkbox"
                            checked={Boolean(formValues[field.name])}
                            onChange={(e) =>
                              handleInputChange(field.name, e.target.checked)
                            }
                            className="h-4 w-4 rounded border-[#d4d1c9] text-[#2f3430] focus:ring-[#2f3430]"
                          />
                          <span>Enabled</span>
                        </label>
                      </div>
                    ) : (
                      <div className="relative">
                        {field.unit && field.unit !== "%" && (
                          <span className="absolute left-3.5 top-2.5 text-sm text-[#9c978f]">
                            {field.unit}
                          </span>
                        )}
                        <input
                          type={field.field_type === "number" ? "number" : "text"}
                          value={String(formValues[field.name] ?? "")}
                          onChange={(e) =>
                            handleInputChange(
                              field.name,
                              field.field_type === "number"
                                ? parseFloat(e.target.value) || 0
                                : e.target.value
                            )
                          }
                          className={`w-full rounded-xl border border-[#e0ded9] bg-white py-2.5 text-sm text-[#37352f] shadow-sm outline-none transition focus:border-[#2f3430] ${
                            field.unit && field.unit !== "%" ? "pl-8 pr-3.5" : "px-3.5"
                          }`}
                        />
                        {field.unit === "%" && (
                          <span className="absolute right-3.5 top-2.5 text-sm text-[#9c978f]">
                            %
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {errorMessage && (
                <div className="mt-5 rounded-xl border border-[#ecd7d0] bg-[#fff9f7] p-4 text-xs text-[#a34b35]">
                  {errorMessage}
                </div>
              )}

              <div className="mt-6 flex items-center justify-between border-t border-[#f0eee9] pt-5">
                <button
                  type="button"
                  onClick={handleCalculate}
                  disabled={calculating}
                  className="inline-flex items-center gap-2 rounded-xl bg-[#2f3430] px-6 py-2.5 text-xs font-medium text-white shadow-sm transition hover:bg-[#1e221f] disabled:opacity-50"
                >
                  <Sparkles className="h-4 w-4" />
                  {calculating ? "Calculating…" : "Run Authoritative Calculation"}
                </button>
                <span className="text-[11px] text-[#8f8a81]">
                  Statutory Rule Pack: {spec.jurisdiction}-2024.1
                </span>
              </div>
            </section>

            {/* Results Section */}
            {calcResult && (
              <section className="space-y-6 rounded-2xl border border-[#d8e3d9] bg-[#f8faf8] p-7 shadow-sm">
                <div className="flex items-center justify-between border-b border-[#e2ece3] pb-4">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-5 w-5 text-[#3a6943]" />
                    <h3 className="text-lg font-semibold tracking-tight text-[#213f28]">
                      Calculation Results & Trace
                    </h3>
                  </div>
                  <span className="font-mono text-[11px] text-[#5b7a60]">
                    ID: {calcResult.calculation_id.slice(0, 8)}…
                  </span>
                </div>

                {/* Calculation breakdown summary grid */}
                <div className="grid gap-3 sm:grid-cols-3">
                  {Object.entries(calcResult.calculation).map(([key, val]) => (
                    <div
                      key={key}
                      className="rounded-xl border border-[#e2ede3] bg-white p-4 shadow-2xs"
                    >
                      <div className="text-[10px] font-semibold uppercase tracking-wider text-[#6a8b6f]">
                        {key.replaceAll("_", " ")}
                      </div>
                      <div className="mt-1 font-mono text-base font-semibold text-[#1e3423]">
                        {typeof val === "object" ? JSON.stringify(val) : String(val)}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Step by Step Explanation Steps */}
                {calcResult.steps && calcResult.steps.length > 0 && (
                  <div className="mt-6 rounded-xl border border-[#e2ede3] bg-white p-5">
                    <h4 className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-[#486b4d]">
                      <Info className="h-3.5 w-3.5" /> Formula Explainability Steps
                    </h4>
                    <div className="mt-4 space-y-3">
                      {calcResult.steps.map((step) => (
                        <div
                          key={step.step_number}
                          className="flex items-start justify-between gap-4 border-b border-[#f4f7f4] pb-3 text-xs last:border-b-0 last:pb-0"
                        >
                          <div>
                            <span className="font-semibold text-[#27462c]">
                              {step.step_number}. {step.label}
                            </span>
                            <div className="font-mono text-[11px] text-[#718d75]">
                              {step.formula_or_rule}
                            </div>
                            {step.notes && (
                              <div className="mt-0.5 text-[11px] text-[#8aa08e]">
                                {step.notes}
                              </div>
                            )}
                          </div>
                          <span className="font-mono font-semibold text-[#27462c]">
                            {String(step.result)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Assumptions & Warnings */}
                {calcResult.warnings && calcResult.warnings.length > 0 && (
                  <div className="rounded-xl border border-[#f5e2b8] bg-[#fffbf2] p-4 text-xs text-[#825c1e]">
                    <div className="font-semibold">Statutory Notices:</div>
                    <ul className="mt-1 list-disc pl-4 space-y-1">
                      {calcResult.warnings.map((w, i) => (
                        <li key={i}>{w}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </section>
            )}

            {/* Official Statutory Legal Sources */}
            {spec.official_sources && spec.official_sources.length > 0 && (
              <section className="rounded-2xl border border-[#e8e6e1] bg-white p-6 shadow-sm">
                <div className="flex items-center gap-2 border-b border-[#f0eee9] pb-3">
                  <BookOpen className="h-4 w-4 text-[#78736b]" />
                  <h3 className="text-sm font-semibold text-[#37352f]">
                    Official Statutory Sources & Law References
                  </h3>
                </div>
                <div className="mt-3 space-y-2">
                  {spec.official_sources.map((src) => (
                    <div
                      key={src.source_id}
                      className="flex flex-wrap items-center justify-between gap-2 text-xs text-[#78736b]"
                    >
                      <div>
                        <span className="font-medium text-[#37352f]">{src.title}</span> —{" "}
                        <span>{src.section_or_rule}</span> ({src.act_name})
                      </div>
                      {src.url && (
                        <a
                          href={src.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-[#2f3430] hover:underline"
                        >
                          Official Portal <ExternalLink className="h-3 w-3" />
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              </section>
            )}
          </div>
        )}
      </div>
    </main>
  );
}
