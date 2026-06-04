/**
 * 파일명: sample/initData.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 공개 샘플 허브 페이지 모드/API 설정
 */

export const PAGE_CONFIG = {
  MODE: "SSR",
  INIT_API: {
    overview: {
      path: "/api/v1/sample/overview",
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
  },
};
