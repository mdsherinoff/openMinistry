/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  images: {
    remotePatterns: [
      {
        protocol: "http",
        hostname: "www.niyamasabha.org",
        pathname: "/pics/**",
      },
    ],
  },
};

module.exports = nextConfig;