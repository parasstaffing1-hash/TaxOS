import type { MetadataRoute } from "next";

import { SERVER_API_BASE } from "@/lib/api";
import { isRecord } from "@/lib/types";

type SitemapItem = {
  loc: string;
  lastmod?: string;
  changefreq?: MetadataRoute.Sitemap[number]["changeFrequency"];
  priority?: number;
};

const fallbackSitemap: MetadataRoute.Sitemap = [
  {
    url: "https://taxos.app/after-tax-salary-calculator/us/ca",
    lastModified: new Date(),
    changeFrequency: "weekly",
    priority: 1,
  },
];

function isSitemapItem(value: unknown): value is SitemapItem {
  return isRecord(value) && typeof value.loc === "string";
}

function isSitemapChunkCount(value: unknown): value is { total_chunks?: number } {
  return isRecord(value) && (value.total_chunks === undefined || typeof value.total_chunks === "number");
}

export async function generateSitemaps() {
  try {
    const response = await fetch(`${SERVER_API_BASE}/seo/sitemaps/count`, { cache: "no-store" });
    if (!response.ok) {
      return [{ id: 0 }];
    }
    const body: unknown = await response.json();
    const totalChunks = isSitemapChunkCount(body) ? body.total_chunks ?? 1 : 1;
    return Array.from({ length: Math.max(1, totalChunks) }, (_, id) => ({ id }));
  } catch {
    return [{ id: 0 }];
  }
}

export default async function sitemap({ id }: { id: number }): Promise<MetadataRoute.Sitemap> {
  try {
    const response = await fetch(`${SERVER_API_BASE}/seo/sitemaps/${id}`, { cache: "no-store" });
    if (!response.ok) {
      return fallbackSitemap;
    }

    const body: unknown = await response.json();
    if (!isRecord(body) || !Array.isArray(body.urls)) {
      return fallbackSitemap;
    }

    const urls = body.urls.filter(isSitemapItem);
    return urls.map((item) => ({
      url: item.loc,
      lastModified: item.lastmod ? new Date(item.lastmod) : new Date(),
      changeFrequency: item.changefreq ?? "weekly",
      priority: typeof item.priority === "number" ? item.priority : 0.8,
    }));
  } catch {
    return fallbackSitemap;
  }
}
