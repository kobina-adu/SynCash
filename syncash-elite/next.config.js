/** @type {import('next').NextConfig} */

const nextConfig = {
  experimental: {
    appDir: true,
  },
  images: {
    domains: ['localhost'],
  },
  env: {
    CUSTOM_KEY: 'my-value',
  },
  async rewrites() {
    return [
      {
        source: '/proxy/:path*',
        destination: 'http://localhost:8787/:path*', // Hono backend
      },
    ]
  },
}

module.exports = nextConfig
