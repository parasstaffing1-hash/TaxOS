export type JsonPrimitive = string | number | boolean | null;
export type JsonValue = JsonPrimitive | JsonObject | JsonValue[];
export type JsonObject = { [key: string]: JsonValue };

export type FormValue = string | number | boolean;
export type FormValues = Record<string, FormValue>;

export type DynamicInputType =
  | "currency"
  | "number"
  | "percentage"
  | "select"
  | "boolean"
  | "text";

export interface DynamicOption {
  label: string;
  value: string;
}

export interface DynamicInput {
  id: string;
  label: string;
  type: DynamicInputType;
  required?: boolean;
  default?: JsonValue;
  min_value?: number;
  max_value?: number;
  options?: DynamicOption[];
  help_text?: string;
}

export interface DynamicFormula {
  id: string;
  expression: string;
  label?: string;
  format?: "currency" | "percentage" | "number";
  is_result?: boolean;
}

export interface DynamicChart {
  id: string;
  type: "pie" | "bar" | "line";
  title: string;
  data_sources: string[];
}

export interface DynamicCalculatorConfig {
  slug: string;
  title: string;
  description: string;
  inputs: DynamicInput[];
  formulas: DynamicFormula[];
  output: {
    summary_cards: string[];
    charts: DynamicChart[];
  };
}

export type DynamicCalculationResults = Record<string, JsonValue>;

export type TaxPeriod = "annual" | "monthly" | "biweekly" | "weekly" | "daily" | "hourly";
export type DisplayTaxPeriod = Exclude<TaxPeriod, "hourly">;
export type PeriodAmounts = Partial<Record<TaxPeriod, string | number>>;

export interface TaxBreakdownItem {
  rule: string;
  name?: string;
  tax: string | number;
  deduction: string | number;
  credit: string | number;
  employer_cost: string | number;
}

export interface TaxCalculationResult {
  currency?: string;
  gross_income: PeriodAmounts;
  taxable_income: PeriodAmounts;
  net_income: PeriodAmounts;
  final_tax: PeriodAmounts;
  effective_tax_rate: string | number;
  breakdown: TaxBreakdownItem[];
}

export type FilingStatus = "single" | "married_jointly" | "married_separately" | "head_of_household";

export interface TaxCalculationPayload {
  income: {
    annual_salary: string;
  };
  location: {
    country: string;
    state?: string;
    city?: string;
  };
  demographics: {
    filing_status: FilingStatus;
    tax_year: number;
  };
  deductions: {
    pre_tax_401k: string;
  };
  currency: "USD";
}

export interface AuthUser {
  id: number;
  email: string;
  is_active: boolean;
  created_at: string;
}

export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function errorMessage(error: unknown, fallback = "Something went wrong."): string {
  return error instanceof Error && error.message ? error.message : fallback;
}

export function asNumber(value: unknown): number {
  const numberValue = Number(value);
  return Number.isFinite(numberValue) ? numberValue : 0;
}

export function asFormValue(value: JsonValue | undefined): FormValue {
  return typeof value === "string" || typeof value === "number" || typeof value === "boolean"
    ? value
    : "";
}

export function isDynamicCalculatorConfig(value: unknown): value is DynamicCalculatorConfig {
  if (!isRecord(value)) {
    return false;
  }

  return (
    typeof value.slug === "string" &&
    typeof value.title === "string" &&
    typeof value.description === "string" &&
    Array.isArray(value.inputs) &&
    Array.isArray(value.formulas) &&
    isRecord(value.output) &&
    Array.isArray(value.output.summary_cards) &&
    Array.isArray(value.output.charts)
  );
}
