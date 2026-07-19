/** @type {import('next').NextConfig} */

// Content-Security-Policy for the web app. Allows self, the Google Maps JS API
// (scripts/images) and inline styles (Tailwind/Next inject styles at runtime).
// `connect-src` permits the API proxy and the maps endpoints.
const csp = [
  "default-src 'self'",
  "script-src 'self' 'unsafe-inline' https://maps.googleapis.com https://maps.gstatic.com",
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: blob: https://maps.googleapis.com https://maps.gstatic.com https://*.googleapis.com https://*.ggpht.com",
  "font-src 'self' data:",
  "connect-src 'self' https://maps.googleapis.com",
  "frame-ancestors 'none'",
  "base-uri 'self'",
  "form-action 'self'",
].join("; ");

const securityHeaders = [
  { key: "Content-Security-Policy", value: csp },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "geolocation=(self), microphone=(), camera=()" },
  { key: "Strict-Transport-Security", value: "max-age=31536000; includeSubDomains" },
];

const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  poweredByHeader: false,
  // Proxy API calls to the FastAPI backend during development.
  async rewrites() {
    const backend = process.env.BACKEND_URL || "http://localhost:8000";
    return [{ source: "/api/:path*", destination: `${backend}/api/:path*` }];
  },
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
};

export default nextConfig;
