/**
 * 파일명: sample/crud/initData.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 공개 CRUD 샘플 페이지 모드/API 설정
 */

export const PAGE_CONFIG = {
  MODE: "SSR",
  INIT_API: {
    list: {
      path: "/api/v1/sample/tasks?page=1&size=50",
      method: "GET",
      authless: true,
    },
  },
  API: {
    list: {
      path: "/api/v1/sample/tasks?page=1&size=50",
      method: "GET",
      authless: true,
    },
    create: {
      path: "/api/v1/sample/tasks",
      method: "POST",
      authless: true,
    },
    detail: {
      path: "/api/v1/sample/tasks/:id",
      method: "GET",
      authless: true,
    },
  },
};
