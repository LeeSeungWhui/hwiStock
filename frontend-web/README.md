This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://github.com/vercel/next.js/tree/canary/packages/create-next-app).

## Getting Started

First, set API base and run the development server:

```bash
cp .env.local.example .env.local # and set NEXT_PUBLIC_API_BASE
pnpm dev
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) with your browser to see the result.

You can start editing the page by modifying `app/page.js`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Conventions (Template)

- JS only (no TypeScript). Tailwind v4.
- Cookie session. All requests use credentials: include.
- Data fetch strategy: Choose MODE per page.
  - SSR: call common contract in page.jsx (server). SEO-ready.
  - CSR: call the same contract in client component. Interactive.
- 공통 통신 계층: `app/lib/runtime/api.js`
  - 기본: `apiJSON` (JSON 리턴), 필요 시 `apiRequest`로 Response 전체 제어
  - 클라이언트에서 스트리밍/자동 재검증이 필요하면 `app/lib/hooks/useApiStream.jsx` 사용 (SWR 래퍼)
