/**
 * 파일명: app/sample/portfolio/lang.ko.js
 * 작성자: LSH
 * 갱신일: 2026-03-04
 * 설명: portfolio 경로 한국어 리소스
 */

export const LANG_KO = {
  page: {
    metadataTitle: "Portfolio | MyWebTemplate",
    metadataDescription:
      "프로젝트 요약, 역할, 신뢰 포인트를 한 페이지에서 보여주는 웹 포트폴리오",
  },
  view: {
    heroBadge: "PUBLIC PORTFOLIO",
    sectionTitle: {
      overview: "프로젝트 개요",
      profile: "Developer Profile (열고 닫기)",
      featuredProjects: "대표 프로젝트",
      careerTimeline: "회사별 경력(요약)",
      education: "학력",
      research: "경험/활동",
      strengths: "주요 강점",
      architecture: "작동 흐름",
      demoFlow: "샘플 동선",
      technicalNotes: "기술 상세 노트 (필요할 때만 열기)",
    },
    label: {
      developer: "담당 개발자",
      moveSample: "샘플 이동",
      status: "상태",
      architectureDescription:
        "화면에서 요청한 정보가 어떤 단계로 처리되는지, 이해하기 쉽게 단순화해서 표현했습니다.",
    },
    overviewCard: {
      taskCount: "업무 샘플 데이터",
      adminUserCount: "관리자 샘플 사용자",
      formSubmissionCount: "최근 폼 제출",
      countSuffix: "건",
      userSuffix: "명",
    },
  },
  initData: {
    content: {
      hero: {
        title: "실무용 웹서비스 템플릿 포트폴리오",
        subtitle:
          "관리자 화면이 필요한 서비스라면, 바로 체험하고 의사결정할 수 있게 구성한 샘플 포트폴리오입니다.",
        cta: [
          { href: "/sample", label: "샘플 바로 체험" },
          { href: "/component", label: "구성 요소 보기", variant: "outline" },
        ],
        summary: [
          "처음 보는 사람도 1분 안에 주요 화면을 체험할 수 있게 설계",
          "실제 운영에서 자주 쓰는 화면 흐름(로그인/대시보드/업무관리) 중심 구성",
          "추가 기능 확장과 유지보수를 고려한 안정적인 기본 뼈대 제공",
        ],
      },
      overview: [
        {
          label: "프로젝트 형태",
          value: "관리자 웹서비스 템플릿",
        },
        {
          label: "주요 제공 화면",
          value: "로그인, 대시보드, 업무관리, 설정",
        },
        {
          label: "즉시 체험 가능",
          value: "/sample, /sample/dashboard, /sample/crud",
        },
      ],
      features: [
        {
          title: "처음 써도 이해되는 화면",
          detail:
            "중요한 정보가 한눈에 보이도록 정보 배치와 흐름을 단순하게 구성했습니다.",
        },
        {
          title: "실무형 업무 동선",
          detail:
            "조회, 검색, 등록, 수정, 삭제까지 실제 운영 흐름에 맞춘 패턴으로 구성했습니다.",
        },
        {
          title: "빠른 커스터마이징",
          detail:
            "브랜드 색상/문구/메뉴 구조만 바꿔도 빠르게 서비스형 화면으로 전환할 수 있습니다.",
        },
      ],
      architectureFlow: [
        {
          icon: "👤",
          title: "사용자 화면",
          description: "고객이 웹에서 바로 사용",
        },
        {
          icon: "🛡️",
          title: "접근 제어",
          description: "로그인 상태와 권한 확인",
        },
        {
          icon: "⚙️",
          title: "서비스 처리",
          description: "데이터 저장/조회와 응답",
        },
      ],
      profile: {
        name: "LSH",
        role: "풀스택 웹 개발자",
        tagline:
          "요구사항 정리부터 구현, 운영 반영까지 이어지는 실무형 프로젝트를 중심으로 경력을 쌓아왔습니다.",
        quickFacts: [
          "총 경력 8년 6개월",
          "현재 앨엔소프트 개발팀 차장",
          "웹/앱 구축 및 운영 경험",
          "근무지역 서울",
        ],
        strengths: [
          "관리자 화면, 업무 시스템, 채용/평판조회 플랫폼 구축 경험",
          "초기 구축부터 유지보수/고도화까지 이어지는 프로젝트 수행",
          "변경이 잦은 요구사항에서도 구조를 단순하게 유지하는 방식 선호",
        ],
        featuredProjects: [
          {
            title: "EY한영 Korea Portal Mobile Project",
            period: "2024.07 ~ 2024.12",
            summary: "기존 Korea Portal의 모바일 WebApp 버전 구축",
            stack: "React · Tailwind CSS · Nginx",
          },
          {
            title: "Refercheck 평판조회사이트 구축",
            period: "2024.10 ~ 진행중",
            summary: "평판조회 요청/응답 관리 중심의 서비스 구축",
            stack: "Spring Boot · React · Tailwind CSS · AuroraDB · Nginx",
          },
          {
            title: "대양그룹 DSCM 수주입력 자동화 시스템",
            period: "2023.12 ~ 2024.03",
            summary: "모바일 발주 및 진행현황 제공 SCM 플랫폼 구축",
            stack: "전자정부 Framework · Spring Boot · React · MySQL",
          },
          {
            title: "대양그룹/태림 TMS 구축",
            period: "2020.10 ~ 2023.02",
            summary: "운송관리시스템 웹/앱 구축 및 리포트 화면 개발",
            stack: "Nexacro · Java · Oracle · Android Studio · UbiReport",
          },
        ],
        careerTimeline: [
          {
            company: "앨엔소프트",
            period: "2024.04 ~ 재직중",
            position: "개발팀 차장",
            summary: "웹 및 앱 개발",
            highlights: [
              "AnyApply 채용사이트 구축 (2024.04 ~ 진행중)",
              "EY한영 Korea Portal Mobile Project (2024.07 ~ 2024.12)",
              "Refercheck 평판조회사이트 구축 (2024.10 ~ 진행중)",
            ],
          },
          {
            company: "조앤소프트",
            period: "2021.10 ~ 2024.03",
            position: "임시직/프리랜서",
            summary: "웹 및 앱 개발",
            highlights: [
              "대양그룹/태림 TMS 구축 (Nexacro, Java, Oracle)",
              "KT DS BizMate App 유지보수 (Android Studio, Swift)",
              "LG U+ 정보현행화 및 대양그룹 DSCM 자동화 시스템 구축",
            ],
          },
          {
            company: "알앤비소프트 · 네오지앤피",
            period: "2020.10 ~ 2021.09",
            position: "임시직/프리랜서",
            summary: "운송관리시스템(TMS) 구축",
            highlights: [
              "Nexacro 기반 운송관리 웹페이지 개발",
              "출력용 리포트 페이지 개발(UbiReport)",
            ],
          },
          {
            company: "와이비에스",
            period: "2018.02 ~ 2020.07",
            position: "기업부설연구소 매니저",
            summary: "교통/모빌리티 데이터 기반 SW 개발",
            highlights: [
              "교통카드 데이터 가공 및 분석 시스템 개발",
              "운전자/차량 데이터 동기화 및 모니터링 SW 개발",
              "교통예보 시스템 고도화 및 데이터 품질 개선",
            ],
          },
          {
            company: "슈어소프트테크",
            period: "2016.12 ~ 2017.07",
            position: "SE사업본부 연구원",
            summary: "신뢰성 검증 및 임베디드 SW 프로젝트 참여",
            highlights: [
              "AUTOSAR 기반 ISJB 개발",
              "다기능 레이더(L-SAM) 신뢰성 시험",
            ],
          },
        ],
        education: [
          {
            school: "연세대학교(원주) 컴퓨터공학",
            detail: "4년제 졸업",
          },
        ],
        research: [
          "연세대학교 모바일 소프트웨어 연구실 (2015.08 ~ 2016.06)",
          "안드로이드 앱 안전성 테스트 및 예외처리 관련 학술 발표 참여",
        ],
      },
      role: [
        "요구사항 분석 및 화면 구조 설계",
        "기능 구현과 데이터 흐름 연결",
        "검수/수정 반영 및 문서 정리",
      ],
      reliability: [
        "변경 시 동작 점검 가능한 테스트 세트 운영",
        "접근 가능한 페이지와 보호 페이지를 분리 운영",
        "규칙 문서와 실제 구현 정합성 유지",
      ],
      demoFlow: [
        {
          name: "CRUD 샘플",
          path: "/sample/crud",
          note: "업무 목록 조회부터 등록/수정/삭제까지 한 번에 체험",
          imageSrc: "/images/landing/demo-crud.png",
          imageAlt: "CRUD 관리 샘플 화면 미리보기",
        },
        {
          name: "복합 폼 샘플",
          path: "/sample/form",
          note: "단계별 입력과 검증, 제출 흐름을 직관적으로 확인",
          imageSrc: "/images/landing/demo-form.png",
          imageAlt: "복합 폼 샘플 화면 미리보기",
        },
        {
          name: "관리자 화면 샘플",
          path: "/sample/admin",
          note: "관리 기능 탭 구성과 운영 화면 구조를 빠르게 확인",
          imageSrc: "/images/landing/demo-admin.png",
          imageAlt: "관리자 화면 샘플 미리보기",
        },
      ],
      technicalNotes: [
        "프론트엔드: Next.js 15(App Router), React 19",
        "백엔드: FastAPI + SQLAlchemy",
        "인증: HttpOnly Cookie 기반 세션 처리, Access/Refresh 회전 흐름 분리",
        "API 계층: BFF 라우트로 요청 경로를 통일해 SSR/CSR 동작 차이를 최소화",
        "미들웨어: 공개 경로/보호 경로 분리, 만료 토큰 재부트스트랩 후 목적지 복귀",
        "응답 규약: success/error 스키마와 code 체계를 백엔드 전 구간에 일관 적용",
        "데이터 계층: SQL 파일 분리 및 쿼리 로더 감시로 운영 중 수정 추적성 확보",
        "품질 게이트: lint/test/rule-gate 기준으로 회귀를 조기에 차단",
        "테스트: 백엔드 API/서비스 테스트 + 프론트 런타임/뷰 테스트 분리 운영",
        "운영 구성: 공개 샘플 경로와 인증 보호 경로를 분리해 샘플/실사용 혼선을 최소화",
      ],
    },
  },
};

export default LANG_KO;
