/**
 * 파일명: sample/dashboard/initData.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 공개 샘플 대시보드 페이지 모드/API 설정
 */

export const PAGE_CONFIG = {
  MODE: "SSR",
  INIT_API: {
    dashboard: {
      path: "/api/v1/sample/dashboard",
      method: "GET",
      authless: true,
    },
  },
  API: {
    dashboard: {
      path: "/api/v1/sample/dashboard",
      method: "GET",
      authless: true,
    },
  },
};
