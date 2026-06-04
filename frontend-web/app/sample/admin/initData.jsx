/**
 * 파일명: sample/admin/initData.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 공개 관리자 샘플 페이지 모드/API 설정
 */

export const PAGE_CONFIG = {
  MODE: "SSR",
  INIT_API: {
    users: {
      path: "/api/v1/sample/admin/users?page=1&size=50",
      method: "GET",
      authless: true,
    },
    settings: {
      path: "/api/v1/sample/admin/settings",
      method: "GET",
      authless: true,
    },
  },
  API: {
    usersList: {
      path: "/api/v1/sample/admin/users?page=1&size=50",
      method: "GET",
      authless: true,
    },
    userCreate: {
      path: "/api/v1/sample/admin/users",
      method: "POST",
      authless: true,
    },
    userDetail: {
      path: "/api/v1/sample/admin/users/:id",
      method: "GET",
      authless: true,
    },
    settings: {
      path: "/api/v1/sample/admin/settings",
      method: "GET",
      authless: true,
    },
    settingsUpdate: {
      path: "/api/v1/sample/admin/settings",
      method: "PUT",
      authless: true,
    },
  },
};
