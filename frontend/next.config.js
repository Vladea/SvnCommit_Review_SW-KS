/** @type {import('next').NextConfig} */
const isDev = process.env.NODE_ENV === 'development';

const nextConfig = {
  output: 'export',
  trailingSlash: true,
  reactStrictMode: true,
};

if (isDev) {
  nextConfig.output = undefined;
  nextConfig.rewrites = async () => [
    { source: '/api/:path*', destination: 'http://127.0.0.1:8000/api/:path*' },
  ];
}

module.exports = nextConfig;
