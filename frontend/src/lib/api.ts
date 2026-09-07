const rawApiUrl = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "");

export const API_BASE = rawApiUrl
  ? rawApiUrl.endsWith("/api/v1")
    ? rawApiUrl
    : `${rawApiUrl}/api/v1`
  : "/api/v1";

let rawServerUrl = (
  process.env.TAXOS_API_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000/api/v1"
).replace(/\/$/, "");

if (!rawServerUrl.endsWith("/api/v1")) {
  rawServerUrl = `${rawServerUrl}/api/v1`;
}

export const SERVER_API_BASE = rawServerUrl;
