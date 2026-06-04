/**
 * 파일명: forgot-password/initData.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 비밀번호 찾기 페이지 초기 설정
 */

export const PAGE_CONFIG = {
  MODE: "CSR",
  INIT_API: {},
  API: {
    requestPasswordReset: {
      path: "/api/v1/auth/password-reset/request",
      method: "POST",
    },
  },
};
