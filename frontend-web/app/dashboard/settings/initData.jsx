/**
 * 파일명: dashboard/settings/initData.jsx
 * 설명: hwiStock 운영 정책 페이지 모드/API(읽기 전용) 설정
 */

export const PAGE_CONFIG = {
  MODE: "CSR",
  INIT_API: {
    profileMe: {
      path: "/api/v1/profile/me",
      method: "GET",
    },
  },
  API: {
    profileMe: {
      path: "/api/v1/profile/me",
      method: "GET",
    },
  },
};
