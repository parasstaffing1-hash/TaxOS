"use client";

import { useEffect, useState } from "react";

import CalculatorEditor from "@/components/admin/CalculatorEditor";
import { API_BASE } from "@/lib/api";
import {
  errorMessage,
  isDynamicCalculatorConfig,
  type DynamicCalculatorConfig,
} from "@/lib/types";

const newCalculator: DynamicCalculatorConfig = {
  slug: "new-calculator",
  title: "New Calculator",
  description: "Describe what this calculator estimates.",
  inputs: [],
  formulas: [],
  output: { summary_cards: [], charts: [] },
};

export default function AdminCalculatorsPage() {
  const [calculators, setCalculators] = useState<DynamicCalculatorConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editingConfig, setEditingConfig] = useState<DynamicCalculatorConfig | null>(null);

  const fetchCalculators = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/dynamic-calculators/`, {
        credentials: "include",
      });
      if (!response.ok) {
        throw new Error("Failed to fetch calculators.");
      }
      const data: unknown = await response.json();
      if (!Array.isArray(data) || !data.every(isDynamicCalculatorConfig)) {
        throw new Error("The server returned invalid calculator data.");
      }
      setCalculators(data);
      setError("");
    } catch (caughtError) {
      setError(errorMessage(caughtError, "Unable to load calculators."));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchCalculators();
  }, []);

  const handleDelete = async (slug: string) => {
    if (!window.confirm(`Are you sure you want to delete ${slug}?`)) {
      return;
    }
    try {
      const response = await fetch(`${API_BASE}/dynamic-calculators/${slug}`, {
        method: "DELETE",
        credentials: "include",
      });
      if (!response.ok) {
        throw new Error("Delete failed.");
      }
      await fetchCalculators();
    } catch (caughtError) {
      window.alert(errorMessage(caughtError, "Unable to delete the calculator."));
    }
  };

  if (editingConfig) {
    return (
      <CalculatorEditor
        initialConfig={editingConfig}
        isNew={!calculators.some((calculator) => calculator.slug === editingConfig.slug)}
        onClose={() => {
          setEditingConfig(null);
          void fetchCalculators();
        }}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8 dark:bg-gray-900">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Calculators Admin</h1>
            <p className="text-gray-600 dark:text-gray-400">Manage dynamic calculator definitions.</p>
          </div>
          <button
            onClick={() => setEditingConfig(newCalculator)}
            className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
          >
            Create New Calculator
          </button>
        </div>

        {error && <div className="mb-4 text-red-500">{error}</div>}

        {loading ? (
          <div>Loading...</div>
        ) : (
          <div className="overflow-hidden rounded-xl border border-gray-100 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-800/50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                    Title
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                    Slug
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-800">
                {calculators.map((calculator) => (
                  <tr key={calculator.slug}>
                    <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-gray-900 dark:text-white">
                      {calculator.title}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500 dark:text-gray-400">
                      {calculator.slug}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-right text-sm font-medium">
                      <button
                        onClick={() => setEditingConfig(calculator)}
                        className="mr-4 text-indigo-600 hover:text-indigo-900 dark:text-indigo-400 dark:hover:text-indigo-300"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => void handleDelete(calculator.slug)}
                        className="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
                {calculators.length === 0 && (
                  <tr>
                    <td colSpan={3} className="px-6 py-4 text-center text-gray-500">
                      No calculators found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
