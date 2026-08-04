"use client";

import { use, useEffect, useState } from "react";

import DynamicForm from "@/components/DynamicForm";
import DynamicResults from "@/components/DynamicResults";
import { API_BASE } from "@/lib/api";
import {
  errorMessage,
  isDynamicCalculatorConfig,
  isRecord,
  type DynamicCalculationResults,
  type DynamicCalculatorConfig,
  type FormValues,
} from "@/lib/types";

interface CalculatorPageProps {
  params: Promise<{ slug: string }>;
}

export default function CalculatorPage({ params }: CalculatorPageProps) {
  const [schema, setSchema] = useState<DynamicCalculatorConfig | null>(null);
  const [results, setResults] = useState<DynamicCalculationResults | null>(null);
  const [formData, setFormData] = useState<FormValues>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const { slug } = use(params);

  useEffect(() => {
    const loadCalculator = async () => {
      setLoading(true);
      setError("");
      try {
        const response = await fetch(`${API_BASE}/dynamic-calculators/${slug}/config`);
        if (!response.ok) {
          throw new Error("Calculator not found.");
        }
        const data: unknown = await response.json();
        if (!isDynamicCalculatorConfig(data)) {
          throw new Error("Calculator configuration is invalid.");
        }
        setSchema(data);
      } catch (caughtError) {
        setError(errorMessage(caughtError, "Unable to load this calculator."));
      } finally {
        setLoading(false);
      }
    };

    void loadCalculator();
  }, [slug]);

  const handleCalculate = async (newFormData: FormValues) => {
    try {
      const response = await fetch(`${API_BASE}/dynamic-calculators/${slug}/calculate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newFormData),
      });
      if (!response.ok) {
        throw new Error("Calculation failed.");
      }

      const data: unknown = await response.json();
      if (!isRecord(data) || !isRecord(data.results)) {
        throw new Error("Calculator returned an invalid result.");
      }
      setResults(data.results as DynamicCalculationResults);
      setFormData(newFormData);

      const url = new URL(window.location.href);
      Object.entries(newFormData).forEach(([key, value]) => url.searchParams.set(key, String(value)));
      window.history.pushState({}, "", url);
    } catch (caughtError) {
      window.alert(errorMessage(caughtError, "Unable to calculate with these inputs."));
    }
  };

  if (loading) {
    return <div className="p-8 text-center">Loading Calculator...</div>;
  }
  if (error || !schema) {
    return <div className="p-8 text-center text-red-500">{error || "Calculator not found."}</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 transition-colors duration-200 dark:bg-gray-900">
      <main className="mx-auto max-w-7xl p-4 sm:p-6 lg:p-8">
        <div className="mb-8">
          <h1 className="mb-2 text-3xl font-bold text-gray-900 dark:text-white">{schema.title}</h1>
          <p className="text-lg text-gray-600 dark:text-gray-400">{schema.description}</p>
        </div>

        <div className="grid grid-cols-1 gap-8 xl:grid-cols-12">
          <div className="print:hidden xl:col-span-4">
            <DynamicForm schema={schema} onCalculate={handleCalculate} />
          </div>
          <div className="xl:col-span-8">
            {results ? (
              <DynamicResults schema={schema} results={results} inputs={formData} />
            ) : (
              <div className="flex h-full items-center justify-center rounded-xl border border-gray-100 bg-white p-12 print:hidden dark:border-gray-700 dark:bg-gray-800">
                <p className="text-lg text-gray-500 dark:text-gray-400">
                  Enter your information and click Calculate to see your results.
                </p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
