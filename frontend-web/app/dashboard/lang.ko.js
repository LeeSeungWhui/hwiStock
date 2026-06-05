/**
 * 파일명: app/dashboard/lang.ko.js
 * 설명: hwiStock 운영 콘솔 dashboard 한국어 리소스
 */

export const LANG_KO = {
  page: {
    metadataTitle: "hwiStock 운영 콘솔",
    endpointMissingLog: "운영 콘솔 엔드포인트가 설정되지 않았습니다.",
    initFetchFailedLog: "운영 콘솔 초기 데이터 조회 실패",
  },
  view: {
    consoleTitle: "hwiStock Lucid Command",
    consoleSubtitle: "읽기 전용 운영 콘솔 · 주문 실행은 runner 전용",
    dataSource: {
      api: "운영 API 연동",
      fixture: "로컬 폴백 스냅샷",
    },
    error: {
      endpointMissing: "운영 콘솔 엔드포인트가 설정되지 않았습니다.",
      fetchFailed: "운영 콘솔 데이터를 불러오지 못했습니다.",
      sectionAriaLabel: "오류 안내",
      requestIdLabel: "requestId",
      codeLabel: "code",
    },
    statusStrip: {
      ariaLabel: "시스템 상태",
      mode: "모드",
      session: "KST/세션",
      venue: "거래 경로",
      killSwitch: "킬스위치",
      serviceHealth: "서비스",
      dataHealth: "데이터 소스",
    },
    readiness: {
      title: "자동매매 준비 상태",
      notReady: "자동매매 준비 전",
      ready: "자동매매 준비 완료",
      paperNetwork: "시세 API 연결",
      paperOrderEnabled: "주문 실행 허용",
      paperOrders: "주문 제출",
      observation: "관찰 승인",
      operational: "운영 준비",
      orderGate: "주문 게이트",
      blockers: "차단 사유",
      serviceVisibilityWarning: "서비스/타이머/대시보드가 보여도 자동매매 준비 완료가 아닐 수 있습니다.",
      fallbackWarning: "폴백 데이터가 포함되어 있습니다. 현재 운영 상태로 해석하지 마세요.",
    },
    panes: {
      summary: "계좌 · 운영 요약",
      data: "보유 · 후보 · 인텔리전스",
      review: "AI · 감사",
    },
    sectionNav: {
      console: "운영 콘솔",
      aiReport: "AI 리포트",
      aiConversation: "AI 대화",
    },
    summary: {
      accountId: "계좌 식별자",
      cash: "가용 현금",
      reserve: "예비금",
      todayPnl: "평가손익",
      realizedPnl: "실현손익",
      openPositions: "보유 포지션",
      riskRejects: "리스크 거절",
      aiJob: "AI 작업",
      reports: "리포트",
    },
    holdings: {
      title: "보유 · 포지션",
      empty: "표시할 보유 종목이 없습니다.",
      columns: {
        symbol: "종목",
        name: "명칭",
        qty: "수량",
        pnl: "손익",
        weight: "비중",
      },
    },
    candidates: {
      title: "후보 · 관심",
      empty: "후보 종목이 없습니다.",
    },
    intelligence: {
      title: "시장 인텔리전스",
      empty: "타임라인 항목이 없습니다.",
    },
    aiReport: {
      title: "AI 리포트",
      subtitle: "저장된 Pro/Flash 분석 문서",
      empty: "저장된 리포트가 없습니다.",
      roleReport: "리포트",
      roleAssistant: "설명",
    },
    aiConversation: {
      title: "AI 대화",
      subtitle: "리포트·상태에 대한 읽기 전용 질의",
      disclaimer: "이 패널은 설명·분석 전용입니다. 주문 실행, 리스크 설정 변경, 자격증명 노출, 서비스 제어는 지원하지 않습니다.",
      inputLabel: "질문 입력",
      inputPlaceholder: "예: 오늘 Flash 리포트에서 거절된 후보는 무엇인가요?",
      submitLabel: "질문 보내기",
      empty: "아직 대화가 없습니다. 저장된 리포트나 현재 상태에 대해 질문해 보세요.",
      pending: "답변을 생성하는 중입니다…",
      unavailable: "AI 대화 백엔드에 연결되지 않았습니다. UI만 준비된 상태입니다.",
      refusedPrefix: "요청 거절",
    },
    audit: {
      title: "감사 · 오류 타임라인",
      empty: "감사 로그가 없습니다.",
    },
    refreshHint: "새로고침",
  },
  layoutMeta: {
    menuList: [
      {
        menuId: "dashboard",
        menuNm: "운영 콘솔",
        href: "/dashboard",
        icon: "ri:RiDashboardLine",
      },
      {
        menuId: "tasks",
        menuNm: "감시 로그",
        href: "/dashboard/tasks",
        icon: "ri:RiListCheck3",
      },
      {
        menuId: "settings",
        menuNm: "운영 정책",
        href: "/dashboard/settings",
        icon: "ri:RiSettings3Line",
      },
    ],
    title: {
      dashboard: "hwiStock 운영 콘솔",
      tasks: "감시 로그",
      settings: "운영 정책",
    },
    subtitle: {
      dashboard: "hwiStock > 운영 콘솔",
      settingsPolicy: "hwiStock > 운영 정책 > 운영 정책",
      settingsConnection: "hwiStock > 운영 정책 > 연결 상태",
      tasksPrefix: "hwiStock > 감시 로그",
      statusPrefix: "상태",
      sortPrefix: "정렬",
      keywordPrefix: "검색",
      pagePrefix: "페이지",
    },
    tasksAllStatus: "전체 상태",
    welcomeText: "hwiStock 운영 모니터링",
    brandName: "hwiStock",
    layoutAction: {
      goHome: "홈으로",
      logout: "로그아웃",
      logoutSuccessToast: "로그아웃에 성공했습니다.",
      logoutFailToast: "로그아웃에 실패했습니다.",
    },
    footerLinkList: [
      { linkId: "console", linkNm: "운영 콘솔", href: "/dashboard" },
      { linkId: "policy", linkNm: "운영 정책", href: "/dashboard/settings" },
    ],
  },
};

export default LANG_KO;
