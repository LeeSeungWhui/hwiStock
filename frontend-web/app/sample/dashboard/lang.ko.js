/**
 * 파일명: app/sample/dashboard/lang.ko.js
 * 작성자: LSH
 * 갱신일: 2026-03-04
 * 설명: dashboard 경로 한국어 리소스
 */

export const LANG_KO = {
  page: {
    metadataTitle: "Sample Dashboard | MyWebTemplate",
    metadataDescription: "공개 샘플 대시보드",
  },
  initData: {
    monthlyTrendLabels: ["11월", "12월", "1월", "2월"],
    recentTaskTitles: [
      "랜딩 페이지 공개 퍼널 정리",
      "샘플 허브 카드 구성 보강",
      "CRUD 검색/필터 UX 점검",
      "관리자 화면 탭 전환 QA",
      "포트폴리오 시각 구성 리뉴얼",
    ],
    ctaLabels: {
      crud: "CRUD 샘플 보기",
      admin: "관리자 화면 보기",
    },
  },
  view: {
    monthSuffix: "월",
    statusLabelMap: {
      ready: "준비",
      pending: "대기",
      running: "진행중",
      done: "완료",
      failed: "실패",
    },
    unknown: "알 수 없음",
    statLabel: {
      totalCount: "전체 건수",
      totalAmount: "총 금액",
      activePending: "진행 + 대기",
    },
    table: {
      titleHeader: "제목",
      statusHeader: "상태",
      amountHeader: "금액",
      createdAtHeader: "등록일",
      empty: "표시할 업무가 없습니다.",
    },
    chart: {
      trendTitle: "월별 추이",
      statusTitle: "상태 분포",
      seriesCount: "건수",
      seriesAmount: "금액",
    },
    card: {
      recentTitle: "최근 업무",
      recentSubtitle: "공개 샘플 대시보드는 읽기 전용으로 제공합니다.",
    },
    quickLinkTitle: "바로 가기",
    number: {
      locale: "ko-KR",
      zeroText: "0",
    },
    misc: {
      defaultStatusCode: "ready",
    },
  },
};

export default LANG_KO;
