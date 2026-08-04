"use client";

import { API_BASE } from "@/lib/api";
import { errorMessage, type TaxCalculationPayload } from "@/lib/types";

interface ExportActionsProps {
  jurisdiction: string;
  payload: TaxCalculationPayload;
}

type ExportFormat = "pdf" | "excel" | "csv";

export default function ExportActions({ jurisdiction, payload }: ExportActionsProps) {
  const handleExport = async (format: ExportFormat) => {
    try {
      const response = await fetch(
        `${API_BASE}/after-tax-salary-calculator/${encodeURIComponent(jurisdiction)}/${format}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        },
      );
      if (!response.ok) {
        throw new Error(`Unable to generate the ${format.toUpperCase()} report.`);
      }

      const url = window.URL.createObjectURL(await response.blob());
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `tax-report.${format === "excel" ? "xlsx" : format}`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      window.alert(errorMessage(error, "Unable to download this report."));
    }
  };

  return (
    <div className="flex space-x-3">
      <button
        onClick={() => handleExport("pdf")}
        className="rounded-md border border-border bg-white px-4 py-2 text-sm font-medium shadow-sm transition-colors hover:border-red-200 hover:bg-red-50 hover:text-red-600"
      >
        PDF
      </button>
      <button
        onClick={() => handleExport("excel")}
        className="rounded-md border border-border bg-white px-4 py-2 text-sm font-medium shadow-sm transition-colors hover:border-green-200 hover:bg-green-50 hover:text-green-600"
      >
        Excel
      </button>
      <button
        onClick={() => handleExport("csv")}
        className="rounded-md border border-border bg-white px-4 py-2 text-sm font-medium shadow-sm transition-colors hover:border-blue-200 hover:bg-blue-50 hover:text-blue-600"
      >
        CSV
      </button>
    </div>
  );
}
