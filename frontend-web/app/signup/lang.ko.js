/**
 * 파일명: app/signup/lang.ko.js
 * 작성자: LSH
 * 갱신일: 2026-02-25
 * 설명: signup 경로 한국어 리소스
 */

export const LANG_KO = {
  page: {
    metadataTitle: "Signup | MyWebTemplate",
  },
  view: {
    toast: {
      signupDone: "회원가입이 완료되었습니다. 로그인해 주세요.",
    },
    error: {
      userExists: "이미 사용 중인 이메일입니다.",
      invalidInput: "입력값을 다시 확인해주세요.",
      signupFailed: "회원가입에 실패했습니다.",
      requestIdLabel: "requestId",
    },
    validation: {
      nameMinLength: "이름은 2자 이상 입력해주세요.",
      emailInvalid: "올바른 이메일 형식을 입력해주세요.",
      passwordMinLength: "비밀번호는 8자 이상 입력해주세요.",
      passwordConfirmMismatch: "비밀번호 확인이 일치하지 않습니다.",
      agreeTermsRequired: "약관 동의는 필수입니다.",
    },
    form: {
      title: "회원가입",
      subtitle: "새 계정을 만들고 로그인해서 대시보드를 확인하세요.",
      nameLabel: "이름",
      namePlaceholder: "이름을 입력해주세요",
      emailLabel: "이메일",
      emailPlaceholder: "이메일을 입력해주세요",
      passwordLabel: "비밀번호",
      passwordPlaceholder: "비밀번호를 입력해주세요",
      passwordConfirmLabel: "비밀번호 확인",
      passwordConfirmPlaceholder: "비밀번호를 다시 입력해주세요",
      agreeTermsLabel: "이용약관에 동의합니다.",
      submitLabel: "회원가입",
      loginGuidePrefix: "이미 계정이 있으신가요?",
      loginLinkLabel: "로그인",
    },
  },
};

export default LANG_KO;
