/**
 * 파일명: signup/initData.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 회원가입 페이지 모드/API(초기적재) 설정
 */

export const PAGE_CONFIG = {
  MODE: "CSR",
  INIT_API: {},
  API: {
    signup: {
      path: "/api/v1/auth/signup",
      method: "POST",
      authless: true,
    },
  },
};
