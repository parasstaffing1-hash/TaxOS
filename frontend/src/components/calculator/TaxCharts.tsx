"use client";

import { asNumber, type TaxCalculationResult } from "@/lib/types";

interface TaxChartsProps {
  result: TaxCalculationResult;
}

export default function TaxCharts({ result }: TaxChartsProps) {
  const effectiveRate = asNumber(result.effective_tax_rate).toFixed(1);
  const netAnnual = asNumber(result.net_income.annual);
  const taxAnnual = asNumber(result.final_tax.annual);
  const total = netAnnual + taxAnnual;

  const takeHomePct = total > 0 ? ((netAnnual / total) * 100).toFixed(1) : "0";
  const taxPct = total > 0 ? ((taxAnnual / total) * 100).toFixed(1) : "0";

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-2 gap-4">
        <div className="rounded-xl border border-border bg-background p-4 text-center">
          <p className="mb-1 text-sm text-foreground/60">Effective Tax Rate</p>
          <p className="text-3xl font-bold text-primary">{effectiveRate}%</p>
        </div>
        <div className="rounded-xl border border-border bg-background p-4 text-center">
          <p className="mb-1 text-sm text-foreground/60">Take Home %</p>
          <p className="text-3xl font-bold text-green-600">{takeHomePct}%</p>
        </div>
      </div>

      <div className="relative pt-4">
        <div className="flex h-12 w-full overflow-hidden rounded-full shadow-inner">
          <div
            style={{ width: `${takeHomePct}%` }}
            className="flex h-full items-center justify-center bg-green-500 text-xs font-bold text-white shadow-[inset_0_-2px_4px_rgba(0,0,0,0.1)] transition-all duration-1000"
          >
            {takeHomePct}%
          </div>
          <div
            style={{ width: `${taxPct}%` }}
            className="flex h-full items-center justify-center bg-red-400 text-xs font-bold text-white shadow-[inset_0_-2px_4px_rgba(0,0,0,0.1)] transition-all duration-1000"
          >
            {taxPct}%
          </div>
        </div>
        <div className="mt-3 flex justify-between text-sm font-medium">
          <span className="flex items-center text-green-600">
            <span className="mr-2 h-3 w-3 rounded-full bg-green-500" /> Take Home
          </span>
          <span className="flex items-center text-red-500">
            Total Tax <span className="ml-2 h-3 w-3 rounded-full bg-red-400" />
          </span>
        </div>
      </div>

      <div className="mt-8 rounded-xl border border-primary/20 bg-gradient-to-br from-primary/10 to-transparent p-6">
        <h4 className="mb-2 text-lg font-semibold">Did you know?</h4>
        <p className="text-sm leading-relaxed text-foreground/80">
          Your marginal tax rate applies to the next dollar earned. Eligible pre-tax contributions
          may lower taxable income; confirm your individual eligibility with a qualified tax adviser.
        </p>
      </div>
    </div>
  );
}
