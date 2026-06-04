/**
 * 파일명: sample/form/initData.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 공개 복합 폼 샘플 페이지 모드/API 설정
 */

export const PAGE_CONFIG = {
  MODE: "SSR",
  INIT_API: {
    meta: {
      path: "/api/v1/sample/forms/meta",
      method: "GET",
      authless: true,
    },
  },
  API: {
    meta: {
      path: "/api/v1/sample/forms/meta",
      method: "GET",
      authless: true,
    },
    submit: {
      path: "/api/v1/sample/forms",
      method: "POST",
      authless: true,
    },
  },
};
