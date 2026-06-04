/**
 * 파일명: app/sample/lang.ko.js
 * 작성자: LSH
 * 갱신일: 2026-03-04
 * 설명: sample 경로 한국어 리소스
 */

export const LANG_KO = {
  page: {
    metadataTitle: "Sample Hub | MyWebTemplate",
    metadataDescription: "공개 샘플 허브",
  },
  view: {
    heroBadge: "PUBLIC SAMPLE HUB",
    openSampleButton: "샘플 열기",
    extraSectionTitle: "추가 자료",
    statLabel: {
      taskCount: "업무 샘플",
      adminUserCount: "관리자 사용자",
      formSubmissionCount: "폼 제출",
    },
  },
  initData: {
    header: {
      title: "샘플 페이지 모음",
      subtitle:
        "대시보드/CRUD/복합 폼/관리자 화면을 바로 확인하고, 필요한 샘플로 한 번에 이동할 수 있습니다.",
    },
    cardList: [
      {
        href: "/sample/dashboard",
        title: "샘플 대시보드",
        description: "요약 지표, 차트, 최근 업무 목록을 읽기 전용으로 확인합니다.",
        icon: "ri:RiBarChart2Line",
        badge: "P0",
      },
      {
        href: "/sample/crud",
        title: "CRUD 관리 샘플",
        description: "검색/필터/드로어 기반 등록·수정·삭제 흐름을 체험합니다.",
        icon: "ri:RiTableLine",
        badge: "P0",
      },
      {
        href: "/sample/form",
        title: "복합 폼 샘플",
        description: "스텝 검증과 제출 요약 흐름을 확인합니다.",
        icon: "ri:RiFileEditLine",
        badge: "P1",
      },
      {
        href: "/sample/admin",
        title: "관리자 화면 샘플",
        description: "사용자/권한/시스템 설정 탭 구성을 확인합니다.",
        icon: "ri:RiShieldUserLine",
        badge: "P1",
      },
    ],
    extraLinkList: [
      {
        href: "/component",
        label: "컴포넌트 문서 보기",
      },
      {
        href: "/sample/portfolio",
        label: "포트폴리오 요약 보기",
      },
    ],
  },
  layoutMeta: {
    menuList: [
      {
        menuId: "demo",
        menuNm: "샘플 허브",
        href: "/sample",
        icon: "ri:RiApps2Line",
      },
      {
        menuId: "dashboard",
        menuNm: "샘플 대시보드",
        href: "/sample/dashboard",
        icon: "ri:RiBarChart2Line",
      },
      {
        menuId: "crud",
        menuNm: "CRUD 관리",
        href: "/sample/crud",
        icon: "ri:RiTableLine",
      },
      {
        menuId: "form",
        menuNm: "복합 폼",
        href: "/sample/form",
        icon: "ri:RiFileEditLine",
      },
      {
        menuId: "admin",
        menuNm: "관리자 화면",
        href: "/sample/admin",
        icon: "ri:RiShieldUserLine",
      },
    ],
    title: {
      demo: "샘플 허브",
      dashboard: "샘플 대시보드",
      form: "복합 폼 샘플",
      admin: "관리자 화면 샘플",
      default: "CRUD 관리 샘플",
    },
    subtitle: {
      demo: "공개 샘플 > 허브",
      dashboard: "공개 샘플 > 샘플 대시보드",
      form: "공개 샘플 > 복합 폼",
      admin: "공개 샘플 > 관리자 화면",
      default: "공개 샘플 > CRUD 관리",
    },
    helperText: "샘플 화면을 체험할 수 있어요.",
    brandName: "MyWebTemplate",
    footerLinkList: [
      { linkId: "demo", linkNm: "샘플 허브", href: "/sample" },
      { linkId: "component", linkNm: "컴포넌트", href: "/component" },
      { linkId: "portfolio", linkNm: "포트폴리오", href: "/sample/portfolio" },
    ],
  },
};

export default LANG_KO;
