"use client";

import { useState } from "react";

import { API_BASE } from "@/lib/api";
import {
  errorMessage,
  type TaxCalculationPayload,
  type TaxCalculationResult,
} from "@/lib/types";

import BreakdownTable from "./BreakdownTable";
import ExportActions from "./ExportActions";
import InputBuilder from "./InputBuilder";
import TaxCharts from "./TaxCharts";

interface CalculatorInterfaceProps {
  country: string;
  state?: string;
  city?: string;
}

export default function CalculatorInterface({ country, state, city }: CalculatorInterfaceProps) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<TaxCalculationResult | null>(null);
  const [payload, setPayload] = useState<TaxCalculationPayload | null>(null);
  const [error, setError] = useState("");

  const calculateTaxes = async (requestPayload: TaxCalculationPayload) => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${API_BASE}/calculate/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestPayload),
      });
      if (!response.ok) {
        throw new Error("Calculation failed. Check the selected jurisdiction and tax year.");
      }
      const data = (await response.json()) as TaxCalculationResult;
      setResult(data);
      setPayload(requestPayload);
    } catch (caughtError) {
      setResult(null);
      setPayload(null);
      setError(errorMessage(caughtError, "Unable to calculate taxes right now."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="glass-card p-8">
        <h2 className="mb-6 text-2xl font-semibold">Your Details</h2>
        <InputBuilder
          country={country}
          state={state}
          city={city}
          onCalculate={calculateTaxes}
          loading={loading}
        />
        {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
      </div>

      {result && payload && (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
            <div className="glass-card overflow-hidden p-8 lg:col-span-2">
              <h2 className="mb-6 text-2xl font-semibold">Salary Breakdown</h2>
              <BreakdownTable result={result} />
            </div>
            <div className="glass-card p-8">
              <h2 className="mb-6 text-2xl font-semibold">Visual Overview</h2>
              <TaxCharts result={result} />
            </div>
          </div>

          <div className="glass-card flex items-center justify-between bg-gradient-to-r from-primary/10 to-transparent p-8">
            <div>
              <h3 className="text-lg font-medium">Download Full Report</h3>
              <p className="text-sm text-foreground/70">
                Get a detailed PDF, Excel, or CSV breakdown of your taxes.
              </p>
            </div>
            <ExportActions jurisdiction={country} payload={payload} />
          </div>
        </div>
      )}
    </div>
  );
}
