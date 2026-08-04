"use client";

import { useState } from "react";

import type { DisplayTaxPeriod, PeriodAmounts, TaxCalculationResult } from "@/lib/types";

const PERIODS: DisplayTaxPeriod[] = ["annual", "monthly", "biweekly", "weekly", "daily"];

interface BreakdownTableProps {
  result: TaxCalculationResult;
}

export default function BreakdownTable({ result }: BreakdownTableProps) {
  const [period, setPeriod] = useState<DisplayTaxPeriod>("annual");

  const formatCurrency = (value: string | number) =>
    new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: result.currency ?? "USD",
    }).format(Number(value));

  const getAmount = (amounts: PeriodAmounts) => amounts[period] ?? "0";

  return (
    <div>
      <div className="mb-6 inline-flex space-x-2 rounded-lg border border-border bg-background p-1">
        {PERIODS.map((currentPeriod) => (
          <button
            key={currentPeriod}
            onClick={() => setPeriod(currentPeriod)}
            className={`rounded-md px-4 py-2 text-sm font-medium transition-all duration-200 ${
              period === currentPeriod
                ? "bg-primary text-primary-foreground shadow-sm"
                : "text-foreground/70 hover:bg-black/5 hover:text-foreground"
            }`}
          >
            {currentPeriod.charAt(0).toUpperCase() + currentPeriod.slice(1)}
          </button>
        ))}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-left">
          <thead>
            <tr className="border-b-2 border-border/60">
              <th className="px-2 py-4 font-semibold text-foreground/80">Category</th>
              <th className="px-2 py-4 text-right font-semibold text-foreground/80">Amount</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/40">
            <tr>
              <td className="px-2 py-4 font-medium text-primary">Gross Income</td>
              <td className="px-2 py-4 text-right font-medium text-primary">
                {formatCurrency(getAmount(result.gross_income))}
              </td>
            </tr>

            {result.breakdown.map((item) => {
              const divisor =
                period === "monthly"
                  ? 12
                  : period === "biweekly"
                    ? 26
                    : period === "weekly"
                      ? 52
                      : period === "daily"
                        ? 260
                        : 1;
              const annualValue =
                Number(item.tax) || Number(item.deduction) || Number(item.credit) || 0;
              const periodValue = annualValue / divisor;

              if (periodValue === 0) {
                return null;
              }

              const isDeduction = Number(item.tax) > 0 || Number(item.deduction) > 0;

              return (
                <tr key={item.rule} className="transition-colors hover:bg-black/5">
                  <td className="flex items-center space-x-2 px-2 py-4">
                    <span
                      className={`h-2 w-2 rounded-full ${
                        isDeduction ? "bg-red-500" : "bg-green-500"
                      }`}
                    />
                    <span>{item.name ?? item.rule}</span>
                  </td>
                  <td className="px-2 py-4 text-right text-foreground/80">
                    {isDeduction ? "-" : "+"}
                    {formatCurrency(periodValue)}
                  </td>
                </tr>
              );
            })}

            <tr className="bg-primary/5">
              <td className="rounded-l-lg px-2 py-5 text-lg font-bold">Take Home Pay</td>
              <td className="rounded-r-lg px-2 py-5 text-right text-lg font-bold">
                {formatCurrency(getAmount(result.net_income))}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
