import type { NextConfig } from "next";

const serverApiBase = (process.env.TAXOS_API_URL ?? "http://localhost:8000/api/v1").replace(
  /\/$/,
  "",
);

const nextConfig: NextConfig = {
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
