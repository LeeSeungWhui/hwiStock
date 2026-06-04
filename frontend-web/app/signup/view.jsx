"use client";

/**
 * 파일명: signup/view.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 회원가입 페이지 클라이언트 뷰
 */

import { useEffect, useRef } from "react";
import EasyObj from "@/app/lib/dataset/EasyObj";
import Button from "@/app/lib/component/Button";
import Checkbox from "@/app/lib/component/Checkbox";
import Input from "@/app/lib/component/Input";
import Link from "next/link";
import { apiJSON } from "@/app/lib/runtime/api";
import { normalizePageConfig } from "@/app/lib/runtime/pageData";
import { useGlobalUi } from "@/app/common/store/SharedStore";
import { PAGE_CONFIG } from "./initData";
import LANG_KO from "./lang.ko";

/**
 * @description 회원가입 입력 검증/제출/에러 포커스 이동을 담당하는 화면을 렌더링. 입력/출력 계약을 함께 명시
 * 처리 규칙: 가입 성공 시 성공 토스트 표시 후 `/login?signup=done`으로 이동한다.
 */
const SignupView = () => {

  /* 1. 상수 ======================================================================================================================= */
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  /* 2. 데이터 ======================================================================================================================= */
  const signupObj = EasyObj({
    name: "",
    email: "",
    password: "",
    passwordConfirm: "",
    agreeTerms: false,
    errors: {
      name: "",
      email: "",
      password: "",
      passwordConfirm: "",
      agreeTerms: "",
    },
  });
  const ui = EasyObj({
    pending: false,
    formError: "",
  });
  const nameRef = useRef(null);
  const emailRef = useRef(null);
  const passwordRef = useRef(null);
  const passwordConfirmRef = useRef(null);
  const agreeTermsRef = useRef(null);
  const errorSummaryRef = useRef(null);
  const focusFrameRef = useRef(null);
  const { showToast } = useGlobalUi();
  const pageMode = normalizePageConfig(PAGE_CONFIG).MODE;

  /* 3. UI ========================================================================================================================= */

  // 없음

  /* 4. 팝업 ======================================================================================================================= */

  // 없음

  /* 5. 기타 ======================================================================================================================= */

  // 없음

  /* 6. 커스텀 훅 =================================================================================================================== */
  // 없음

  /* 7. 함수 ======================================================================================================================= */

  /**
   * @description 이름/이메일/비밀번호/약관 동의 조건을 검증하고 에러 상태를 설정. 입력/출력 계약을 함께 명시
   * 실패 동작: 첫 오류 메시지를 ui.formError에 기록하고 해당 필드로 포커스를 이동한 뒤 false를 반환한다.
   * @updated 2026-02-27
   */
  const validateForm = () => {
    signupObj.errors.name = "";
    signupObj.errors.email = "";
    signupObj.errors.password = "";
    signupObj.errors.passwordConfirm = "";
    signupObj.errors.agreeTerms = "";
    ui.formError = "";
    let firstIssueObj = null;
    const signupName = String(signupObj.name || "").trim();
    const email = String(signupObj.email || "").trim().toLowerCase();
    const password = String(signupObj.password || "");
    const passwordConfirm = String(signupObj.passwordConfirm || "");
    const agreeTerms = Boolean(signupObj.agreeTerms);

    signupObj.name = signupName;
    signupObj.email = email;

    if (!signupName || signupName.length < 2) {
      signupObj.errors.name = LANG_KO.view.validation.nameMinLength;
      if (!firstIssueObj) firstIssueObj = { ref: nameRef, message: signupObj.errors.name };
    }
    if (!email || !emailPattern.test(email)) {
      signupObj.errors.email = LANG_KO.view.validation.emailInvalid;
      if (!firstIssueObj) firstIssueObj = { ref: emailRef, message: signupObj.errors.email };
    }
    if (!password || password.length < 8) {
      signupObj.errors.password = LANG_KO.view.validation.passwordMinLength;
      if (!firstIssueObj) firstIssueObj = { ref: passwordRef, message: signupObj.errors.password };
    }
    if (passwordConfirm !== password) {
      signupObj.errors.passwordConfirm = LANG_KO.view.validation.passwordConfirmMismatch;
      if (!firstIssueObj) firstIssueObj = {
        ref: passwordConfirmRef,
        message: signupObj.errors.passwordConfirm,
      };
    }
    if (!agreeTerms) {
      signupObj.errors.agreeTerms = LANG_KO.view.validation.agreeTermsRequired;
      if (!firstIssueObj) firstIssueObj = { ref: agreeTermsRef, message: signupObj.errors.agreeTerms };
    }

    if (firstIssueObj) {
      ui.formError = firstIssueObj.message;
      cancelAnimationFrame(focusFrameRef.current);
      focusFrameRef.current = requestAnimationFrame(() => {
        firstIssueObj.ref.current?.focus();
      });
      return false;
    }
    return true;
  };

  /**
   * @description 회원가입 API 요청을 전송하고 결과에 맞는 후속 동작을 반영
   * 실패 동작: 코드별 에러 메시지를 필드/폼에 반영하고 오류 요약 영역으로 포커스를 이동한다.
   * @updated 2026-02-27
   */
  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!validateForm()) return;

    ui.pending = true;
    try {
      await apiJSON(PAGE_CONFIG.API.signup, {
        method: "POST",
        body: {
          name: String(signupObj.name || "").trim(),
          email: String(signupObj.email || "").trim().toLowerCase(),
          password: String(signupObj.password || ""),
        },
      }, { authless: true });
      showToast(LANG_KO.view.toast.signupDone, { type: "success" });
      window.location.assign("/login?signup=done");
    } catch (error) {
      if (error?.code === "AUTH_409_USER_EXISTS") {
        signupObj.errors.email = LANG_KO.view.error.userExists;
        ui.formError = signupObj.errors.email;
        cancelAnimationFrame(focusFrameRef.current);
        focusFrameRef.current = requestAnimationFrame(() => {
          emailRef.current?.focus();
        });
        return;
      }
      if (error?.code === "AUTH_422_INVALID_INPUT") {
        ui.formError = LANG_KO.view.error.invalidInput;
      } else {
        const requestIdText = error?.requestId
          ? ` (${LANG_KO.view.error.requestIdLabel}: ${error.requestId})`
          : "";
        ui.formError = `${error?.message || LANG_KO.view.error.signupFailed}${requestIdText}`;
      }
      cancelAnimationFrame(focusFrameRef.current);
      focusFrameRef.current = requestAnimationFrame(() => {
        errorSummaryRef.current?.focus();
      });
    } finally {
      ui.pending = false;
    }
  };

  /* 8. useEffect ================================================================================================================== */
  /**
   * @description 페이지 해제 시 pending focus frame을 정리
   * 처리 규칙: 검증/에러 처리 직후 예약된 focus 콜백이 unmount 뒤 실행되지 않게 차단한다.
   */
  useEffect(() => () => cancelAnimationFrame(focusFrameRef.current), []);

  /* 9. 내부 컴포넌트 ============================================================================================================== */

  // 없음

  /* 10. 렌더링 ==================================================================================================================== */
  return (
    <main className="min-h-screen flex items-center justify-center bg-gray-50 p-4 sm:p-6" data-page-mode={pageMode}>
      <section className="w-full max-w-xl rounded-2xl bg-white p-6 shadow-xl sm:p-10">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-semibold text-gray-900">{LANG_KO.view.form.title}</h1>
          <p className="mt-2 text-sm text-gray-600">
            {LANG_KO.view.form.subtitle}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5" noValidate>
          {ui.formError ? (
            <div
              ref={errorSummaryRef}
              tabIndex={-1}
              role="alert"
              aria-live="assertive"
              className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700"
            >
              {ui.formError}
            </div>
          ) : null}

          <div>
            <label htmlFor="signup-name" className="block text-sm font-medium text-gray-700">
              {LANG_KO.view.form.nameLabel}
            </label>
            <div className="mt-2">
              <Input
                id="signup-name"
                dataObj={signupObj}
                dataKey="name"
                ref={nameRef}
                placeholder={LANG_KO.view.form.namePlaceholder}
                error={signupObj.errors.name}
              />
              {signupObj.errors.name ? (
                <p className="mt-2 text-sm text-red-600">{signupObj.errors.name}</p>
              ) : null}
            </div>
          </div>

          <div>
            <label htmlFor="signup-email" className="block text-sm font-medium text-gray-700">
              {LANG_KO.view.form.emailLabel}
            </label>
            <div className="mt-2">
              <Input
                id="signup-email"
                type="email"
                dataObj={signupObj}
                dataKey="email"
                ref={emailRef}
                placeholder={LANG_KO.view.form.emailPlaceholder}
                error={signupObj.errors.email}
              />
              {signupObj.errors.email ? (
                <p className="mt-2 text-sm text-red-600">{signupObj.errors.email}</p>
              ) : null}
            </div>
          </div>

          <div>
            <label htmlFor="signup-password" className="block text-sm font-medium text-gray-700">
              {LANG_KO.view.form.passwordLabel}
            </label>
            <div className="mt-2">
              <Input
                id="signup-password"
                type="password"
                dataObj={signupObj}
                dataKey="password"
                ref={passwordRef}
                placeholder={LANG_KO.view.form.passwordPlaceholder}
                error={signupObj.errors.password}
              />
              {signupObj.errors.password ? (
                <p className="mt-2 text-sm text-red-600">{signupObj.errors.password}</p>
              ) : null}
            </div>
          </div>

          <div>
            <label htmlFor="signup-password-confirm" className="block text-sm font-medium text-gray-700">
              {LANG_KO.view.form.passwordConfirmLabel}
            </label>
            <div className="mt-2">
              <Input
                id="signup-password-confirm"
                type="password"
                dataObj={signupObj}
                dataKey="passwordConfirm"
                ref={passwordConfirmRef}
                placeholder={LANG_KO.view.form.passwordConfirmPlaceholder}
                error={signupObj.errors.passwordConfirm}
              />
              {signupObj.errors.passwordConfirm ? (
                <p className="mt-2 text-sm text-red-600">{signupObj.errors.passwordConfirm}</p>
              ) : null}
            </div>
          </div>

          <div>
            <Checkbox
              dataObj={signupObj}
              dataKey="agreeTerms"
              label={LANG_KO.view.form.agreeTermsLabel}
              ref={agreeTermsRef}
            />
            {signupObj.errors.agreeTerms ? (
              <p className="mt-2 text-sm text-red-600">{signupObj.errors.agreeTerms}</p>
            ) : null}
          </div>

          <Button type="submit" variant="primary" size="lg" className="w-full" loading={ui.pending}>
            {LANG_KO.view.form.submitLabel}
          </Button>
        </form>

        <div className="mt-6 text-center text-sm text-gray-600">
          {`${LANG_KO.view.form.loginGuidePrefix} `}{" "}
          <Link href="/login" className="font-medium text-blue-600 hover:text-blue-500">
            {LANG_KO.view.form.loginLinkLabel}
          </Link>
        </div>
      </section>
    </main>
  );
};

export default SignupView;
