/** @type {import('next').NextConfig} */
const nextConfig = {
  turbopack: {
    resolveAlias: {
      canvas: './app/lib/runtime/stubs/canvas.js',
      'canvas$': './app/lib/runtime/stubs/canvas.js',
    },
  },
};

export default nextConfig;
