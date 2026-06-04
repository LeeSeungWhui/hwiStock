/**
 * 파일명: common/i18n/lang.ko.js
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: frontend-web 공통 한국어 리소스 템플릿
 */

export const COMMON_LANG_KO = {
  action: {
    save: "저장",
    cancel: "취소",
    close: "닫기",
    reset: "초기화",
    search: "검색",
  },
  status: {
    loading: "불러오는 중...",
    empty: "표시할 데이터가 없습니다.",
  },
  message: {
    unknownError: "요청 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
  },
};

export const COMMON_COMPONENT_LANG_KO = {
  alert: {
    title: "알림",
    confirmText: "확인",
  },
  confirm: {
    title: "확인",
    confirmText: "확인",
    cancelText: "취소",
  },
  dropdown: {
    placeholder: "선택",
    emptyItem: "항목 없음",
    multiSelectedSuffix: "개 선택됨",
  },
  empty: {
    titleNoData: "데이터가 없습니다",
  },
  easyChart: {
    empty: "표시할 데이터가 없습니다.",
    loadFailed: "데이터를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.",
    seriesRequired: "시리즈 설정이 필요합니다. dataKey와 라벨을 전달해 주세요.",
  },
  easyTable: {
    empty: "데이터가 없습니다.",
    loading: "불러오는 중...",
    error: "오류가 발생했습니다.",
    noRenderCardProvided: "카드 렌더링 함수가 없습니다.",
  },
  easyUpload: {
    fileUploadUrlRequired: "파일 업로드 URL이 필요합니다.",
    uploadFailedTitle: "업로드 실패",
    uploadFailedDefault: "업로드 실패",
    uploadFailedWithStatusSuffix: " 업로드 실패",
    uploadFailedDescription: "파일 업로드에 실패했습니다.",
    uploadUnknownError: "파일 업로드 중 알 수 없는 오류가 발생했습니다.",
  },
  header: {
    defaultTitle: "Dashboard",
    toggleSidebarAriaLabel: "사이드바 토글",
    primaryMenuAriaLabel: "주요 메뉴",
    defaultMenuLabel: "메뉴",
    defaultSubMenuLabel: "하위메뉴",
    subMenuAriaSuffix: "하위 메뉴",
  },
  loading: {
    processingText: "처리중...",
  },
  input: {
    showPassword: "비밀번호 보기",
    hidePassword: "비밀번호 숨기기",
  },
  pagination: {
    navigationAriaLabel: "페이지네이션",
    firstPageAriaLabel: "첫 페이지",
    previousPageAriaLabel: "이전 페이지",
    nextPageAriaLabel: "다음 페이지",
    lastPageAriaLabel: "마지막 페이지",
  },
  sidebar: {
    expandAriaLabel: "사이드바 펼치기",
    collapseAriaLabel: "사이드바 접기",
    closeAriaLabel: "사이드바 닫기",
    menuAriaLabel: "사이드바 메뉴",
    navigationAriaLabel: "사이드바 내비게이션",
    defaultMenuLabel: "메뉴",
    defaultSubMenuLabel: "하위메뉴",
    subMenuAriaSuffix: "하위 메뉴",
  },
  footer: {
    defaultTextTemplate: "© {year} MyWebTemplate",
    defaultLinkLabel: "링크",
  },
  publicLayout: {
    brandLabel: "MyWebTemplate",
    copyrightTemplate: "© {year} MyWebTemplate. All rights reserved.",
    footerLinkList: [
      { href: "/sample", label: "샘플 허브" },
      { href: "/component", label: "컴포넌트" },
      { href: "/sample/portfolio", label: "포트폴리오" },
    ],
    demoMenuList: [
      { href: "/sample", label: "샘플 허브" },
      { href: "/sample/dashboard", label: "샘플 대시보드" },
      { href: "/sample/crud", label: "CRUD 관리" },
      { href: "/sample/form", label: "복합 폼" },
      { href: "/sample/admin", label: "관리자 화면" },
    ],
    publicMenuList: [
      { href: "/component", label: "컴포넌트" },
      { href: "/sample/portfolio", label: "포트폴리오" },
    ],
    mobileMenuOpenAriaLabel: "모바일 메뉴 열기",
    demoMenuLabel: "샘플",
    demoMenuAriaLabel: "샘플 메뉴",
  },
  stat: {
    valueAriaLabel: "값",
    deltaAriaLabel: "증감",
  },
  pdfViewer: {
    ariaLabel: "PDF 뷰어",
    loadFailedStatus: "PDF 문서를 불러오지 못했습니다.",
    sourceUnavailableStatus: "PDF 소스를 확인할 수 없습니다.",
    loadingStatus: "PDF 문서를 불러오는 중입니다.",
    pageStatusTemplate: "총 {totalPages}페이지 중 {currentPage}페이지, 확대 {zoomPercent}%",
    readyStatus: "PDF 문서 준비가 완료되었습니다.",
    loadingText: "PDF 불러오는 중...",
    loadFailedTitle: "PDF를 불러오지 못했습니다",
    loadFailedDescription: "파일 경로나 권한을 확인한 뒤 다시 시도해 주세요.",
    missingSourceTitle: "PDF 소스가 없습니다",
    missingSourceDescription: "미리보기를 위해 유효한 URL, File, Blob, ArrayBuffer를 전달해 주세요.",
  },
  timeInput: {
    openPickerAriaLabel: "시간 선택기 열기",
  },
  select: {
    saved: "선택이 저장되었습니다.",
    needsConfirm: "추가 확인이 필요합니다.",
    invalidValue: "유효하지 않은 값입니다.",
    loading: "불러오는 중…",
    noItems: "표시할 항목이 없습니다.",
    disabled: "사용할 수 없는 상태입니다.",
  },
  combobox: {
    saved: "선택이 저장되었습니다.",
    needsConfirm: "추가 확인이 필요합니다.",
    invalidValue: "유효하지 않은 값입니다.",
    loading: "불러오는 중…",
    noItems: "표시할 항목이 없습니다.",
    disabled: "사용할 수 없는 상태입니다.",
    placeholder: "선택하세요",
    noResults: "결과 없음",
    summaryText: "{count}개 선택",
    selectAllText: "전체 선택",
    clearAllText: "전체 해제",
    toggleClear: "해제",
    toggleAll: "전체",
    searchPlaceholder: "검색...",
  },
  dateInput: {
    weekdaysShort: ["일", "월", "화", "수", "목", "금", "토"],
    openDatePicker: "날짜 선택기 열기",
    prevMonth: "이전 달",
    nextMonth: "다음 달",
    yearSuffix: "년",
    monthSuffix: "월",
  },
  easyEditor: {
    fontSizeDefault: "기본",
    alignLeft: "좌",
    alignCenter: "중앙",
    alignRight: "우",
    alignJustify: "양끝",
    placeholder: "내용을 입력하세요",
    promptLinkUrl: "링크 URL을 입력하세요",
    toolbarBold: "굵게",
    toolbarItalic: "기울임",
    toolbarUnderline: "밑줄",
    toolbarLink: "링크",
    colorReset: "초기화",
    alignSuffix: " 정렬",
    attachImage: "이미지 첨부",
    attachFile: "파일 첨부",
    modeEditor: "에디터 모드",
    modeHtml: "HTML 모드",
    imageUploadFailed: "이미지 업로드에 실패했습니다.",
    fileUploadFailed: "파일 업로드에 실패했습니다.",
  },
};

export default COMMON_LANG_KO;
