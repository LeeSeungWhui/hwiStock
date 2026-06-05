/**
 * 파일명: dashboard/tasks/initData.jsx
 * 설명: hwiStock 감시 로그 페이지 모드/API(읽기 전용) 설정
 */

export const PAGE_CONFIG = {
  MODE: "CSR",
  INIT_API: {},
  API: {
    list: {
      path: "/api/v1/hwistock/runner/operatorSnapshot",
      method: "GET",
    },
  },
};
