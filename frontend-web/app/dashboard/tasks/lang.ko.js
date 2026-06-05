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
      { value: "", text: "전체 레벨" },
      { value: "info", text: "정보" },
      { value: "warn", text: "경고" },
      { value: "error", text: "오류" },
    ],
    sortFilterList: [
      { value: "at_desc", text: "시간 최신순" },
      { value: "at_asc", text: "시간 오래된순" },
      { value: "level_asc", text: "레벨 오름차순" },
      { value: "code_asc", text: "코드 오름차순" },
      { value: "code_desc", text: "코드 내림차순" },
    ],
  },
  view: {
    statusLabelMap: {
      info: "정보",
      warn: "경고",
      warning: "경고",
      error: "오류",
    },
    error: {
      listEndpointMissing: "감시 로그 목록 API가 설정되지 않았습니다.",
      listLoadFailed: "감시 로그를 불러오지 못했습니다.",
      requestIdLabel: "requestId",
    },
    table: {
      atHeader: "시각",
      levelHeader: "레벨",
      codeHeader: "코드",
      messageHeader: "메시지",
      tagsHeader: "태그",
      emptyFallback: "표시할 감시 로그가 없습니다.",
    },
    search: {
      keywordPlaceholder: "코드/메시지/태그 검색",
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
