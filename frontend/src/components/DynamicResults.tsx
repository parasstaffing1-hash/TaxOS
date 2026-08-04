"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { FileCode, FileJson, FileSpreadsheet, FileText, Printer } from "lucide-react";

import { API_BASE } from "@/lib/api";
import {
  asNumber,
  errorMessage,
  type DynamicCalculatorConfig,
  type DynamicCalculationResults,
  type FormValues,
} from "@/lib/types";

const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884d8"];
type DocumentFormat = "pdf" | "excel" | "csv" | "json";

interface DynamicResultsProps {
  schema: DynamicCalculatorConfig;
  results: DynamicCalculationResults;
  inputs: FormValues;
}

function displayValue(value: unknown, format: "currency" | "percentage" | "number" | undefined) {
  if (format === "currency") {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 2,
    }).format(asNumber(value));
  }
  if (format === "percentage") {
    return `${asNumber(value).toFixed(2)}%`;
  }
  return typeof value === "string" || typeof value === "number" ? String(value) : "—";
}

export default function DynamicResults({ schema, results, inputs }: DynamicResultsProps) {
  const handlePrint = () => window.print();

  const handleExport = async (format: DocumentFormat) => {
    try {
      const response = await fetch(`${API_BASE}/documents/${schema.slug}/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          format,
          template_id: "corporate",
          inputs,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to generate ${format} document.`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.style.display = "none";
      anchor.href = url;
      anchor.download = `${schema.slug}-report.${format === "excel" ? "xlsx" : format}`;

      const disposition = response.headers.get("Content-Disposition");
      const filename = /filename="([^"]+)"/.exec(disposition ?? "")?.[1];
      if (filename) {
        anchor.download = filename;
      }

      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      window.alert(errorMessage(error, "Unable to generate the selected report."));
    }
  };

  return (
    <div className="space-y-8 print:w-full">
      <div className="flex flex-wrap justify-end gap-2 print:hidden">
        <button
          onClick={handlePrint}
          title="Print View"
          className="flex items-center gap-2 rounded bg-gray-100 px-3 py-2 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700"
        >
          <Printer size={16} /> Print
        </button>
        <button
          onClick={() => handleExport("pdf")}
          title="Download PDF"
          className="flex items-center gap-2 rounded bg-red-50 px-3 py-2 text-red-700 hover:bg-red-100 dark:bg-red-900/30 dark:text-red-400 dark:hover:bg-red-900/50"
        >
          <FileText size={16} /> PDF
        </button>
        <button
          onClick={() => handleExport("excel")}
          title="Download Excel"
          className="flex items-center gap-2 rounded bg-green-50 px-3 py-2 text-green-700 hover:bg-green-100 dark:bg-green-900/30 dark:text-green-400 dark:hover:bg-green-900/50"
        >
          <FileSpreadsheet size={16} /> Excel
        </button>
        <button
          onClick={() => handleExport("csv")}
          title="Download CSV"
          className="flex items-center gap-2 rounded bg-gray-100 px-3 py-2 text-gray-700 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
        >
          <FileCode size={16} /> CSV
        </button>
        <button
          onClick={() => handleExport("json")}
          title="Download JSON"
          className="flex items-center gap-2 rounded bg-blue-50 px-3 py-2 text-blue-700 hover:bg-blue-100 dark:bg-blue-900/30 dark:text-blue-400 dark:hover:bg-blue-900/50"
        >
          <FileJson size={16} /> JSON
        </button>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
        {schema.output.summary_cards.map((id) => {
          const formula = schema.formulas.find((item) => item.id === id);
          return (
            <div
              key={id}
              className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800"
            >
              <h3 className="mb-1 text-sm font-medium text-gray-500 dark:text-gray-400">
                {formula?.label ?? id}
              </h3>
              <p className="text-3xl font-bold text-gray-900 dark:text-white">
                {displayValue(results[id], formula?.format)}
              </p>
            </div>
          );
        })}
      </div>

      {schema.output.charts.length > 0 && (
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
          {schema.output.charts.map((chart) => {
            const data = chart.data_sources.map((source) => {
              const field =
                schema.formulas.find((item) => item.id === source) ??
                schema.inputs.find((item) => item.id === source);
              return { name: field?.label ?? source, value: asNumber(results[source]) };
            });

            return (
              <div
                key={chart.id}
                className="h-[400px] rounded-xl border border-gray-100 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800"
              >
                <h3 className="mb-6 text-lg font-semibold text-gray-900 dark:text-white">
                  {chart.title}
                </h3>
                <ResponsiveContainer width="100%" height="100%">
                  {chart.type === "pie" ? (
                    <PieChart>
                      <Pie
                        data={data}
                        dataKey="value"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        outerRadius={100}
                        label
                      >
                        {data.map((_, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                      <Legend />
                    </PieChart>
                  ) : (
                    <BarChart data={data}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="value" fill="#0088FE" />
                    </BarChart>
                  )}
                </ResponsiveContainer>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
