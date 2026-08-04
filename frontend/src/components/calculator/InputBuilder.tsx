"use client";

import { useState } from "react";

import type { FilingStatus, TaxCalculationPayload } from "@/lib/types";

interface InputBuilderProps {
  country: string;
  state?: string;
  city?: string;
  onCalculate: (payload: TaxCalculationPayload) => void;
  loading: boolean;
}

export default function InputBuilder({
  country,
  state,
  city,
  onCalculate,
  loading,
}: InputBuilderProps) {
  const [annualSalary, setAnnualSalary] = useState("100000");
  const [filingStatus, setFilingStatus] = useState<FilingStatus>("single");
  const [preTax401k, setPreTax401k] = useState("0");

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    onCalculate({
      income: { annual_salary: annualSalary },
      location: { country, state, city },
      demographics: { filing_status: filingStatus, tax_year: 2024 },
      deductions: { pre_tax_401k: preTax401k },
      currency: "USD",
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <div>
          <label htmlFor="annual-salary" className="premium-label">
            Annual Salary
          </label>
          <div className="relative">
            <span className="absolute left-4 top-3.5 text-foreground/50">$</span>
            <input
              id="annual-salary"
              type="number"
              min="0"
              className="premium-input pl-8"
              value={annualSalary}
              onChange={(event) => setAnnualSalary(event.target.value)}
              required
            />
          </div>
        </div>

        <div>
          <label htmlFor="filing-status" className="premium-label">
            Filing Status
          </label>
          <select
            id="filing-status"
            className="premium-input"
            value={filingStatus}
            onChange={(event) => setFilingStatus(event.target.value as FilingStatus)}
          >
            <option value="single">Single</option>
            <option value="married_jointly">Married Filing Jointly</option>
            <option value="married_separately">Married Filing Separately</option>
            <option value="head_of_household">Head of Household</option>
          </select>
        </div>

        <div>
          <label htmlFor="tax-year" className="premium-label">
            Tax Year
          </label>
          <input id="tax-year" className="premium-input" value="2024" readOnly />
          <p className="mt-1 text-xs text-foreground/60">Currently verified release-year rules.</p>
        </div>

        <div>
          <label htmlFor="pre-tax-401k" className="premium-label">
            Eligible Pre-Tax 401(k) Deduction
          </label>
          <div className="relative">
            <span className="absolute left-4 top-3.5 text-foreground/50">$</span>
            <input
              id="pre-tax-401k"
              type="number"
              min="0"
              className="premium-input pl-8"
              value={preTax401k}
              onChange={(event) => setPreTax401k(event.target.value)}
            />
          </div>
        </div>
      </div>

      <div className="flex justify-end pt-4">
        <button
          type="submit"
          className="premium-button flex items-center space-x-2"
          disabled={loading}
        >
          {loading ? (
            <>
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
              <span>Calculating...</span>
            </>
          ) : (
            <span>Calculate My Paycheck</span>
          )}
        </button>
      </div>
    </form>
  );
}
