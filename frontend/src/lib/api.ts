export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "/api/v1";

// Server components cannot fetch a relative API URL during static generation.
// Deployments with a separate API host must set TAXOS_API_URL for server-side
// requests; browsers continue to use the reverse-proxied relative URL by default.
export const SERVER_API_BASE =
  process.env.TAXOS_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
