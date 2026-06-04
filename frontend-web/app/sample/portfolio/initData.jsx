/**
 * 파일명: sample/portfolio/initData.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 공개 샘플 포트폴리오 페이지 모드/API 설정
 */

export const PAGE_CONFIG = {
  MODE: "SSR",
  INIT_API: {
    overview: {
      path: "/api/v1/sample/overview",
      method: "GET",
      authless: true,
    },
    dashboard: {
      path: "/api/v1/sample/dashboard",
      method: "GET",
      authless: true,
    },
  },
  API: {
    overview: {
      path: "/api/v1/sample/overview",
      method: "GET",
      authless: true,
    },
    dashboard: {
      path: "/api/v1/sample/dashboard",
      method: "GET",
      authless: true,
    },
  },
};
