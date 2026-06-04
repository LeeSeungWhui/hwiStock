const runningVitest = !!process.env.VITEST || process.env.NODE_ENV === 'test';

const config = {
  plugins: runningVitest ? { '@tailwindcss/postcss': {} } : ['@tailwindcss/postcss'],
};

export default config;
