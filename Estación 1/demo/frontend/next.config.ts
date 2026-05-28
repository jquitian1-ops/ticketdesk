import type { NextConfig } from "next";

// Troubleshooting #14 + #16: derive API origin from the SAME env var the app uses.
// Strip trailing slashes and whitespace so we never inject a stale or broken
// origin into the Content-Security-Policy. A CSP that doesn't match the runtime
// API URL silently blocks fetches in WebKit (impossible to diagnose).
const rawApiUrl =
  process.env.NEXT_PUBLIC_API_URL ??
  "https://6svkxadr3h.execute-api.us-east-1.amazonaws.com";
const apiUrl = rawApiUrl.replace(/\s+/g, "").replace(/\/+$/, "");
const apiOrigin = (() => {
  try {
    return new URL(apiUrl).origin;
  } catch {
    return apiUrl;
  }
})();

const s3Origin = "https://*.s3.amazonaws.com https://*.s3.us-east-1.amazonaws.com";
const newRelicOrigin = "https://otlp.nr-data.net";

const csp = [
  "default-src 'self'",
  "script-src 'self' 'unsafe-inline'",
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: blob: https://*.amazonaws.com",
  `connect-src 'self' ${apiOrigin} ${s3Origin} ${newRelicOrigin}`,
  "font-src 'self' data:",
  "frame-ancestors 'none'",
  "base-uri 'self'",
  "form-action 'self'"
].join("; ");

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "Content-Security-Policy", value: csp },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=()"
          }
        ]
      }
    ];
  }
};

export default nextConfig;
