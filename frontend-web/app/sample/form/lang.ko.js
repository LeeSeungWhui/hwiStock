/**
 * 파일명: app/sample/form/lang.ko.js
 * 작성자: LSH
 * 갱신일: 2026-03-04
 * 설명: form 경로 한국어 리소스
 */

export const LANG_KO = {
  page: {
    metadataTitle: "Form Sample | MyWebTemplate",
    metadataDescription: "공개 복합 폼 샘플 화면",
  },
  initData: {
    categoryOptions: [
      { value: "", text: "분류 선택" },
      { value: "web", text: "웹개발" },
      { value: "app", text: "앱개발" },
      { value: "api", text: "API개발" },
      { value: "etc", text: "기타" },
    ],
    featureOptions: [
      { key: "login", label: "로그인" },
      { key: "board", label: "게시판" },
      { key: "payment", label: "결제" },
      { key: "chart", label: "차트" },
      { key: "admin", label: "관리자" },
    ],
  },
  view: {
    stepList: [
      { step: 1, label: "기본 정보" },
      { step: 2, label: "상세 정보" },
      { step: 3, label: "확인/제출" },
    ],
    summaryLabel: {
      name: "이름",
      email: "이메일",
      phone: "연락처",
      category: "분류",
      startDate: "시작일",
      endDate: "종료일",
      period: "기간",
      budgetRange: "예산 범위",
      features: "우선 기능",
      requirement: "요청사항",
      referenceUrl: "참고 URL",
      attachmentName: "첨부파일",
    },
    validation: {
      nameRequired: "이름을 입력해주세요.",
      emailInvalid: "올바른 이메일 형식을 입력해주세요.",
      phoneRequired: "연락처를 입력해주세요.",
      categoryRequired: "분류를 선택해주세요.",
      startDateRequired: "시작일을 입력해주세요.",
      endDateRequired: "종료일을 입력해주세요.",
      budgetRangeRequired: "예산 범위를 입력해주세요.",
      endDateAfterStartDate: "종료일은 시작일 이후여야 합니다.",
      requiredFieldToast: "필수 입력값을 확인해주세요.",
    },
    page: {
      title: "복합 폼 샘플",
      subtitle: "스텝 전환/유효성 안내/제출 요약 흐름을 공개 페이지에서 체험할 수 있습니다.",
      loadingCardTitle: "로딩 중",
      loadingCardBody: "데이터를 준비하는 중입니다...",
    },
    card: {
      step1Title: "기본 정보",
      step2Title: "상세 정보",
      step3Title: "확인/제출",
      submissionTitlePrefix: "누적 제출",
      submissionTitleSuffix: "건",
      submissionDescription: "공개 sample 폼은 제출 시 DB에 저장되고, 최신 제출 이력도 함께 갱신된다.",
      latestSubmissionTitle: "최근 제출",
      latestSubmissionEmpty: "아직 저장된 제출 이력이 없습니다.",
    },
    input: {
      namePlaceholder: "이름",
      emailPlaceholder: "이메일",
      phonePlaceholder: "연락처",
      budgetRangePlaceholder: "예) 300만 ~ 500만",
      requirementPlaceholder: "요청사항",
      referenceUrlPlaceholder: "참고 URL",
    },
    action: {
      prev: "이전",
      next: "다음",
      submit: "제출하기",
      submitSuccessToast: "신청이 완료되었습니다",
    },
    error: {
      submitFailed: "제출에 실패했습니다.",
    },
  },
};

export default LANG_KO;
