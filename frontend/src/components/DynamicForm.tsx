"use client";

import { useState } from "react";

import {
  asFormValue,
  type DynamicCalculatorConfig,
  type FormValue,
  type FormValues,
} from "@/lib/types";

interface DynamicFormProps {
  schema: DynamicCalculatorConfig;
  onCalculate: (data: FormValues) => void;
}

export default function DynamicForm({ schema, onCalculate }: DynamicFormProps) {
  const [formData, setFormData] = useState<FormValues>(() =>
    Object.fromEntries(
      schema.inputs.map((field) => [field.id, asFormValue(field.default)]),
    ),
  );

  const handleChange = (id: string, value: FormValue) => {
    setFormData((previous) => ({ ...previous, [id]: value }));
  };

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    onCalculate(formData);
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-6 rounded-xl border border-gray-100 bg-white p-6 shadow-md dark:border-gray-700 dark:bg-gray-800"
    >
      <h2 className="mb-4 text-xl font-semibold text-gray-900 dark:text-white">
        Calculator Inputs
      </h2>

      {schema.inputs.map((field) => {
        const value = formData[field.id] ?? "";
        const inputId = `${schema.slug}-${field.id}`;

        return (
          <div key={field.id} className="flex flex-col">
            <label
              htmlFor={inputId}
              className="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300"
            >
              {field.label} {field.required && <span className="text-red-500">*</span>}
            </label>

            {field.type === "select" ? (
              <select
                id={inputId}
                className="rounded-lg border bg-gray-50 p-3 outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-900 dark:text-white"
                value={String(value)}
                onChange={(event) => handleChange(field.id, event.target.value)}
                required={field.required}
              >
                <option value="">Select an option</option>
                {field.options?.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            ) : field.type === "boolean" ? (
              <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                <input
                  id={inputId}
                  type="checkbox"
                  checked={Boolean(value)}
                  onChange={(event) => handleChange(field.id, event.target.checked)}
                />
                Yes
              </label>
            ) : (
              <input
                id={inputId}
                type={
                  field.type === "number" ||
                  field.type === "currency" ||
                  field.type === "percentage"
                    ? "number"
                    : "text"
                }
                className="rounded-lg border bg-gray-50 p-3 outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-900 dark:text-white"
                value={String(value)}
                onChange={(event) => handleChange(field.id, event.target.value)}
                required={field.required}
                min={field.min_value}
                max={field.max_value}
              />
            )}

            {field.help_text && (
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">{field.help_text}</p>
            )}
          </div>
        );
      })}

      <button
        type="submit"
        className="w-full rounded-lg bg-blue-600 px-4 py-3 font-bold text-white transition-colors hover:bg-blue-700"
      >
        Calculate
      </button>
    </form>
  );
}
