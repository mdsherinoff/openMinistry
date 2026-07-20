/** @type {import('next').NextConfig} */
const nextConfig = {
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
