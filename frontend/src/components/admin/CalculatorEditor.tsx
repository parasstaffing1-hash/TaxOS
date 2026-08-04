"use client";

import { useState } from "react";

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

interface CalculatorEditorProps {
  initialConfig: DynamicCalculatorConfig;
  isNew: boolean;
  onClose: () => void;
}

export default function CalculatorEditor({ initialConfig, isNew, onClose }: CalculatorEditorProps) {
  const [config, setConfig] = useState(() => JSON.stringify(initialConfig, null, 2));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [previewTab, setPreviewTab] = useState<"code" | "preview">("code");
  const [previewResults, setPreviewResults] = useState<DynamicCalculationResults | null>(null);

  const parsedConfig = (): DynamicCalculatorConfig | null => {
    try {
      const parsed: unknown = JSON.parse(config);
      return isDynamicCalculatorConfig(parsed) ? parsed : null;
    } catch {
      return null;
    }
  };

  const handleSave = async () => {
    const parsed = parsedConfig();
    if (!parsed) {
      setError("The configuration must be valid calculator JSON.");
      return;
    }

    setError("");
    setSaving(true);
    try {
      const method = isNew ? "POST" : "PUT";
      const url = isNew
        ? `${API_BASE}/dynamic-calculators/`
        : `${API_BASE}/dynamic-calculators/${parsed.slug}`;
      const response = await fetch(url, {
        method,
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(parsed),
      });
      if (!response.ok) {
        const payload: unknown = await response.json().catch(() => null);
        const detail = isRecord(payload) && typeof payload.detail === "string" ? payload.detail : null;
        throw new Error(detail ?? "Failed to save configuration.");
      }
      onClose();
    } catch (caughtError) {
      setError(errorMessage(caughtError, "Unable to save the calculator."));
    } finally {
      setSaving(false);
    }
  };

  const handleCalculatePreview = (formData: FormValues) => {
    const schema = parsedConfig();
    if (!schema) {
      return;
    }
    const mockResults: DynamicCalculationResults = { ...formData };
    schema.formulas.forEach((formula) => {
      mockResults[formula.id] = 1000;
    });
    setPreviewResults(mockResults);
  };

  const schema = parsedConfig();

  return (
    <div className="fixed inset-0 z-50 flex h-screen flex-col bg-gray-50 dark:bg-gray-900">
      <div className="flex items-center justify-between border-b border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">
          {isNew ? "Create Calculator" : "Edit Calculator"}
        </h2>
        <div className="flex items-center gap-4">
          {error && <span className="text-sm font-medium text-red-500">{error}</span>}
          <div className="flex rounded-lg bg-gray-100 p-1 dark:bg-gray-700">
            <button
              onClick={() => setPreviewTab("code")}
              className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
                previewTab === "code"
                  ? "bg-white text-gray-900 shadow-sm dark:bg-gray-600 dark:text-white"
                  : "text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              }`}
            >
              Code
            </button>
            <button
              onClick={() => setPreviewTab("preview")}
              className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
                previewTab === "preview"
                  ? "bg-white text-gray-900 shadow-sm dark:bg-gray-600 dark:text-white"
                  : "text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              }`}
            >
              Preview UI
            </button>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? "Saving..." : "Save Configuration"}
          </button>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {previewTab === "code" ? (
          <textarea
            value={config}
            onChange={(event) => setConfig(event.target.value)}
            className="h-full w-full resize-none bg-gray-900 p-4 font-mono text-sm text-green-400 outline-none"
            spellCheck="false"
          />
        ) : (
          <div className="h-full w-full overflow-y-auto p-8">
            {schema ? (
              <div className="mx-auto grid max-w-7xl grid-cols-1 gap-8 xl:grid-cols-12">
                <div className="xl:col-span-4">
                  <DynamicForm schema={schema} onCalculate={handleCalculatePreview} />
                </div>
                <div className="xl:col-span-8">
                  {previewResults ? (
                    <DynamicResults schema={schema} results={previewResults} inputs={{}} />
                  ) : (
                    <div className="flex h-full items-center justify-center rounded-xl border border-gray-100 bg-white p-12 dark:border-gray-700 dark:bg-gray-800">
                      <p className="text-lg text-gray-500 dark:text-gray-400">
                        Click Calculate to preview results.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="mt-20 text-center text-red-500">
                Invalid JSON schema. Cannot render preview.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
