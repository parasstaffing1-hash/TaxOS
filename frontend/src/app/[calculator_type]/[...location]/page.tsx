import type { Metadata } from "next";
import { notFound } from "next/navigation";

import CalculatorInterface from "@/components/calculator/CalculatorInterface";
import { SERVER_API_BASE } from "@/lib/api";
import { isRecord, type JsonObject } from "@/lib/types";

export const revalidate = 3600;

interface PageProps {
  params: Promise<{
    calculator_type: string;
    location: string[];
  }>;
}

interface SeoMeta {
  title: string;
  description: string;
  canonical: string;
  og_title?: string;
  og_description?: string;
  og_url?: string;
  twitter_title?: string;
  twitter_description?: string;
}

interface SeoLink {
  name: string;
  url: string;
}

interface SeoPageData {
  h1: string;
  meta: SeoMeta;
  content_paragraphs: string[];
  faq_schema: JsonObject | null;
  software_schema: JsonObject | null;
  breadcrumb_schema: JsonObject | null;
  related_links: SeoLink[];
}

interface SeoRoute {
  calculator_type: string;
  location: string[];
}

const verifiedCalculatorTypes = new Set([
  "after-tax-salary-calculator",
  "paycheck-calculator",
]);

function isVerifiedPublicRoute(calculatorType: string, location: string[]): boolean {
  const [country, state, city] = location;
  return (
    verifiedCalculatorTypes.has(calculatorType) &&
    country?.toUpperCase() === "US" &&
    state?.toUpperCase() === "CA" &&
    city === undefined
  );
}

function isSeoMeta(value: unknown): value is SeoMeta {
  return (
    isRecord(value) &&
    typeof value.title === "string" &&
    typeof value.description === "string" &&
    typeof value.canonical === "string"
  );
}

function isSeoLink(value: unknown): value is SeoLink {
  return isRecord(value) && typeof value.name === "string" && typeof value.url === "string";
}

function isJsonObjectOrNull(value: unknown): value is JsonObject | null {
  return value === null || isRecord(value);
}

function isSeoPageData(value: unknown): value is SeoPageData {
  return (
    isRecord(value) &&
    typeof value.h1 === "string" &&
    isSeoMeta(value.meta) &&
    Array.isArray(value.content_paragraphs) &&
    value.content_paragraphs.every((paragraph) => typeof paragraph === "string") &&
    isJsonObjectOrNull(value.faq_schema) &&
    isJsonObjectOrNull(value.software_schema) &&
    isJsonObjectOrNull(value.breadcrumb_schema) &&
    Array.isArray(value.related_links) &&
    value.related_links.every(isSeoLink)
  );
}

function isSeoRoute(value: unknown): value is SeoRoute {
  return (
    isRecord(value) &&
    typeof value.calculator_type === "string" &&
    Array.isArray(value.location) &&
    value.location.every((segment) => typeof segment === "string")
  );
}

function getFallbackData(type: string, country: string, state?: string, city?: string): SeoPageData {
  const locationLabel = [city, state, country].filter(Boolean).join(", ").toUpperCase();
  const title = `${type.replace(/-/g, " ")} ${locationLabel}`;
  const path = [type, country, state, city].filter(Boolean).join("/").toLowerCase();

  return {
    h1: title,
    meta: {
      title: `${title} - TaxOS`,
      description: "Estimate your taxes and take-home pay.",
      canonical: `https://taxos.app/${path}`,
    },
    content_paragraphs: ["Use this calculator to estimate taxes and take-home pay."],
    faq_schema: null,
    software_schema: null,
    breadcrumb_schema: null,
    related_links: [],
  };
}

async function getSEOData(calculatorType: string, location: string[]): Promise<SeoPageData> {
  const [country = "US", state, city] = location;
  const fallback = getFallbackData(calculatorType, country, state, city);
  const url = new URL(`${SERVER_API_BASE}/seo/page-data`);
  url.searchParams.set("calculator_type", calculatorType);
  url.searchParams.set("country", country);
  if (state) url.searchParams.set("state", state);
  if (city) url.searchParams.set("city", city);

  try {
    const response = await fetch(url, { next: { revalidate } });
    if (!response.ok) {
      return fallback;
    }
    const body: unknown = await response.json();
    return isSeoPageData(body) ? body : fallback;
  } catch {
    return fallback;
  }
}

export async function generateStaticParams(): Promise<SeoRoute[]> {
  try {
    const response = await fetch(`${SERVER_API_BASE}/seo/top-routes`, {
      next: { revalidate },
    });
    if (!response.ok) {
      return [];
    }
    const body: unknown = await response.json();
    if (!isRecord(body) || !Array.isArray(body.routes)) {
      return [];
    }
    return body.routes.filter(isSeoRoute);
  } catch {
    return [];
  }
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const resolvedParams = await params;
  if (!isVerifiedPublicRoute(resolvedParams.calculator_type, resolvedParams.location)) {
    notFound();
  }
  const data = await getSEOData(resolvedParams.calculator_type, resolvedParams.location);

  return {
    title: data.meta.title,
    description: data.meta.description,
    alternates: { canonical: data.meta.canonical },
    openGraph: {
      title: data.meta.og_title ?? data.meta.title,
      description: data.meta.og_description ?? data.meta.description,
      url: data.meta.og_url ?? data.meta.canonical,
      type: "website",
    },
    twitter: {
      card: "summary_large_image",
      title: data.meta.twitter_title ?? data.meta.title,
      description: data.meta.twitter_description ?? data.meta.description,
    },
  };
}

function JsonLd({ schema }: { schema: JsonObject }) {
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{
        __html: JSON.stringify({ "@context": "https://schema.org", ...schema }),
      }}
    />
  );
}

export default async function CalculatorPage({ params }: PageProps) {
  const resolvedParams = await params;
  if (!isVerifiedPublicRoute(resolvedParams.calculator_type, resolvedParams.location)) {
    notFound();
  }
  const data = await getSEOData(resolvedParams.calculator_type, resolvedParams.location);
  const [country = "US", state, city] = resolvedParams.location;

  return (
    <div className="flex min-h-screen flex-col items-center bg-gray-50">
      <main className="mt-10 w-full max-w-4xl rounded-lg bg-white p-8 shadow">
        <h1 className="mb-4 text-3xl font-bold">{data.h1}</h1>
        {data.content_paragraphs.map((paragraph, index) => (
          <p key={`${paragraph}-${index}`} className="mb-4 leading-relaxed text-gray-700">
            {paragraph}
          </p>
        ))}

        <div className="mt-8">
          <CalculatorInterface country={country} state={state} city={city} />
        </div>

        {data.related_links.length > 0 && (
          <div className="mt-8">
            <h2 className="mb-2 text-lg font-semibold">Related Calculators</h2>
            <ul className="list-disc pl-5">
              {data.related_links.map((link) => (
                <li key={link.url}>
                  <a href={link.url} className="text-blue-600 hover:underline">
                    {link.name}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        )}
      </main>

      {data.faq_schema && <JsonLd schema={data.faq_schema} />}
      {data.software_schema && <JsonLd schema={data.software_schema} />}
      {data.breadcrumb_schema && <JsonLd schema={data.breadcrumb_schema} />}
    </div>
  );
}
