import type { NextConfig } from "next";

let serverApiBase = (
  process.env.TAXOS_API_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000/api/v1"
).replace(/\/$/, "");

if (!serverApiBase.endsWith("/api/v1")) {
  serverApiBase = `${serverApiBase}/api/v1`;
}

const nextConfig: NextConfig = {
  output: "standalone",
  poweredByHeader: false,
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${serverApiBase}/:path*`,
      },
    ];
  },
};

export default nextConfig;
