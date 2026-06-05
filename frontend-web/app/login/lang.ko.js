/**
 * 파일명: app/login/lang.ko.js
 * 작성자: LSH
 * 갱신일: 2026-06-05
 * 설명: hwiStock 운영 콘솔 로그인 경로 한국어 리소스
 */

export const LANG_KO = {
  page: {
    metadataTitle: "Login | hwiStock",
  },
  view: {
    toast: {
      sessionExpired: "세션이 만료되었습니다. 다시 로그인해 주세요.",
      signupDone: "회원가입이 완료되었습니다. 로그인해 주세요.",
      codeLabel: "code",
      requestIdLabel: "requestId",
    },
    error: {
      tooManyAttempts: "로그인 시도가 너무 많습니다. 잠시 후 다시 시도해 주세요.",
      invalidCredential: "비밀번호가 올바르지 않습니다.",
      loginFailed: "로그인에 실패했습니다.",
      invalidInput: "입력값을 확인해 주세요.",
    },
    validation: {
      passwordRequired: "비밀번호를 입력해주세요",
      passwordMinLength: "비밀번호는 최소 8자 이상이어야 합니다",
    },
    side: {
      title: "hwiStock 운영 콘솔",
      subtitle: "운영자 인증",
      pointList: [
        "운영자 비밀번호로 운영 콘솔에 접근합니다",
        "운영 상태와 업무 데이터를 읽기 전용으로 확인합니다",
        "주문·매매 실행은 이 화면에서 제공하지 않습니다",
      ],
    },
    form: {
      title: "로그인",
      subtitle: "운영자 비밀번호를 입력하세요",
      operatorNotice: "아이디 입력 없이 운영자 비밀번호만 확인합니다.",
      passwordLabel: "비밀번호",
      passwordPlaceholder: "비밀번호를 입력하세요",
      rememberMeLabel: "로그인 상태 유지",
      submitLabel: "로그인",
    },
  },
};

export default LANG_KO;
