/**
 * 파일명: app/dashboard/tasks/lang.ko.js
 * 설명: hwiStock 감시 로그 경로 한국어 리소스
 */

export const LANG_KO = {
  page: {
    metadataTitle: "hwiStock 감시 로그",
  },
  initData: {
    statusFilterList: [
      { value: "", text: "전체 상태" },
      { value: "ready", text: "준비" },
      { value: "pending", text: "대기" },
      { value: "running", text: "진행중" },
      { value: "done", text: "완료" },
      { value: "failed", text: "실패" },
    ],
    sortFilterList: [
      { value: "reg_dt_desc", text: "등록일 최신순" },
      { value: "reg_dt_asc", text: "등록일 오래된순" },
      { value: "amt_desc", text: "금액 높은순" },
      { value: "amt_asc", text: "금액 낮은순" },
      { value: "title_asc", text: "제목 오름차순" },
      { value: "title_desc", text: "제목 내림차순" },
    ],
  },
  view: {
    statusLabelMap: {
      ready: "준비",
      pending: "대기",
      running: "진행중",
      done: "완료",
      failed: "실패",
    },
    error: {
      listEndpointMissing: "감시 로그 목록 API가 설정되지 않았습니다.",
      listLoadFailed: "감시 로그를 불러오지 못했습니다.",
      requestIdLabel: "requestId",
    },
    table: {
      titleHeader: "이벤트",
      statusHeader: "상태",
      amountHeader: "금액",
      createdAtHeader: "기록일",
      tagsHeader: "태그",
      emptyFallback: "표시할 감시 로그가 없습니다.",
    },
    search: {
      keywordPlaceholder: "이벤트/설명 검색",
      searchButton: "조회",
      resetButton: "초기화",
    },
    card: {
      filterTitle: "감시 로그 필터",
      filterSubtitle: "읽기 전용 · 조회·필터만 지원합니다.",
      tableTitle: "감시 로그 목록",
    },
    action: {
      totalCountTemplate: "총 {total}건",
    },
    misc: {
      noData: "없음",
      currencyZero: "0",
      dateUnknown: "-",
    },
  },
};

export default LANG_KO;
