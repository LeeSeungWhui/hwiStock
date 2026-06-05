"use client";

/**
 * 파일명: app/login/view.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 로그인 페이지 클라이언트 뷰
 */

import { useEffect, useRef } from "react";
import EasyObj from "@/app/lib/dataset/EasyObj";
import Button from "@/app/lib/component/Button";
import Input from "@/app/lib/component/Input";
import Checkbox from "@/app/lib/component/Checkbox";
import { apiJSON } from "@/app/lib/runtime/api";
import usePageData from "@/app/lib/hooks/usePageData";
import { PAGE_CONFIG } from "./initData";
import { useGlobalUi } from "@/app/common/store/SharedStore";
import LANG_KO from "./lang.ko";

/**
 * @description 로그인 폼 검증/제출 및 세션 상태 기반 리다이렉트를 담당하는 페이지 뷰를 렌더링. 입력/출력 계약을 함께 명시
 * 처리 규칙: 로그인 성공 시 nextHint(안전 경로) 또는 `/dashboard`로 이동한다.
 */
const LoginView = ({ initialDataObj, initialErrorObj }) => {

  /* 1. 상수 ======================================================================================================================= */
  const minPasswordLength = 8;
  const operatorUsername = String(
    process.env.NEXT_PUBLIC_HWISTOCK_OPERATOR_USERNAME || "operator@hwistock.local",
  ).trim();

  /* 2. 데이터 ======================================================================================================================= */
  const loginObj = EasyObj({
    password: "",
    rememberMe: false,
    errors: {
      password: "",
    },
  });
  const ui = EasyObj({
    pending: false,
    formError: "",
  });
  const passwordRef = useRef(null);
  const errorSummaryRef = useRef(null);
  const focusFrameRef = useRef(null);
  const { showToast } = useGlobalUi();
  const pageMetaObj = initialDataObj?.__pageMeta || {};
  const nextHint = pageMetaObj.nextHint || null;
  const authReason = pageMetaObj.authReason || null;
  const { dataObj, reload } = usePageData({
    pageConfig: PAGE_CONFIG,
    initialDataObj,
    initialErrorObj,
  });
  const sessionData = dataObj.session || null;
  const isAuthed = Boolean(
    sessionData &&
    sessionData.result &&
    sessionData.result.username
  );
  const passwordErrorId = loginObj.errors.password
    ? "login-password-error"
    : undefined;

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
   * @description 로그인 후 이동할 리다이렉트 경로를 안전한 내부 경로로 제한
   * 처리 규칙: 절대 URL/프로토콜/`//` 경로를 차단하고 `/`로 시작하는 내부 경로만 허용한다.
   * @updated 2026-02-27
   */
  const sanitizeRedirect = (candidate) => {
    if (!candidate || typeof candidate !== "string") return null;
    if (!candidate.startsWith("/")) return null;
    if (candidate.startsWith("//")) return null;
    if (/^https?:/i.test(candidate)) return null;
    return candidate;
  };

  /**
   * @description 로그인 폼 입력값을 검증하고 첫 오류를 화면에 노출
   * 실패 동작: 규칙 위반 시 ui.formError 설정 후 해당 입력 필드로 포커스를 이동하고 false를 반환한다.
   * @updated 2026-02-27
   */
  const validateForm = () => {
    loginObj.errors.password = "";
    ui.formError = "";
    let firstIssueObj = null;

    const password = String(loginObj.password || "");

    if (!password) {
      loginObj.errors.password = LANG_KO.view.validation.passwordRequired;
      if (!firstIssueObj) firstIssueObj = { ref: passwordRef, summary: loginObj.errors.password };
    } else if (password.length < minPasswordLength) {
      loginObj.errors.password = LANG_KO.view.validation.passwordMinLength;
      if (!firstIssueObj) firstIssueObj = { ref: passwordRef, summary: loginObj.errors.password };
    }

    if (firstIssueObj) {
      ui.formError = firstIssueObj.summary || LANG_KO.view.error.invalidInput;
      cancelAnimationFrame(focusFrameRef.current);
      focusFrameRef.current = requestAnimationFrame(() => {
        firstIssueObj.ref.current?.focus();
      });
      return false;
    }
    return true;
  };

  /**
   * @description 로그인 제출 요청을 보내고 성공/실패 분기를 적용
   * 실패 동작: API 예외 시 code/statusCode 기준으로 필드/폼 에러를 반영하고 pending 상태를 해제한다.
   * @updated 2026-02-27
   */
  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!validateForm()) return;

    ui.pending = true;
    try {
      const loginPayloadObj = {
        username: operatorUsername,
        password: loginObj.password,
        rememberMe: Boolean(loginObj.rememberMe),
      };
      await apiJSON(PAGE_CONFIG.API.login, {
        method: "POST",
        body: loginPayloadObj,
      });
      await reload?.();
      const redirectPath = sanitizeRedirect(nextHint) || "/dashboard";
      window.location.assign(redirectPath);
      return;
    } catch (error) {
      let backendErrorObj = { message: LANG_KO.view.error.loginFailed };
      if (error?.code === "AUTH_429_RATE_LIMIT") {
        backendErrorObj = { message: LANG_KO.view.error.tooManyAttempts };
      } else if (error?.code === "AUTH_422_INVALID_INPUT") {
        backendErrorObj = { message: LANG_KO.view.error.invalidInput };
      } else if (error?.code === "AUTH_401_INVALID") {
        backendErrorObj = {
          message: LANG_KO.view.error.invalidCredential,
          field: "password",
        };
      } else if (error?.statusCode === 401) {
        backendErrorObj = { message: LANG_KO.view.toast.sessionExpired };
      } else if (error?.message) {
        backendErrorObj = { message: error.message };
      }
      const { message, field } = backendErrorObj;
      if (field === "email" || field === "password") {
        loginObj.errors.password = message;
        cancelAnimationFrame(focusFrameRef.current);
        focusFrameRef.current = requestAnimationFrame(() => {
          passwordRef.current?.focus();
        });
      } else {
        cancelAnimationFrame(focusFrameRef.current);
        focusFrameRef.current = requestAnimationFrame(() => {
          errorSummaryRef.current?.focus();
        });
      }
      ui.formError = message;
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

  /**
   * @description 이미 인증된 사용자는 로그인 화면 렌더 후 대시보드로 이동
   * 처리 규칙: 렌더링 중 navigation 부작용을 만들지 않고 effect에서만 이동한다.
   * @updated 2026-05-31
   */
  useEffect(() => {
    if (!isAuthed) return;
    if (typeof window === "undefined") return;
    const redirectCandidate = typeof nextHint === "string" ? nextHint : "";
    const isInternalRedirect =
      redirectCandidate.startsWith("/") &&
      !redirectCandidate.startsWith("//") &&
      !/^https?:/i.test(redirectCandidate);
    window.location.replace(isInternalRedirect ? redirectCandidate : "/dashboard");
  }, [isAuthed, nextHint]);

  /**
   * @description 인증 실패 사유(authReason)가 전달되면 토스트로 경고를 노출
   * 처리 규칙: code/requestId가 있으면 메타 정보까지 함께 표시한다.
   * @updated 2026-02-28
   */
  useEffect(() => {
    if (!authReason) return;
    const message = authReason?.message
      ? String(authReason.message)
      : LANG_KO.view.toast.sessionExpired;
    const metaPartList = [];
    if (authReason?.code) metaPartList.push(`${LANG_KO.view.toast.codeLabel}: ${authReason.code}`);
    if (authReason?.requestId) {
      metaPartList.push(`${LANG_KO.view.toast.requestIdLabel}: ${authReason.requestId}`);
    }
    const metaText = metaPartList.length ? ` (${metaPartList.join(", ")})` : "";
    showToast(`${message}${metaText}`, { type: "error", duration: 5000 });
  }, [authReason, showToast]);

  /**
   * @description 회원가입 완료 쿼리(`signup=done`)를 1회 토스트로 안내하고 URL에서 제거
   * 처리 규칙: 성공 토스트 노출 후 history.replaceState로 쿼리 파라미터를 정리한다.
   * @updated 2026-02-28
   */
  useEffect(() => {
    if (typeof window === "undefined") return;
    const currentUrl = new URL(window.location.href);
    const signupStatus = currentUrl.searchParams.get("signup");
    if (signupStatus !== "done") return;
    showToast(LANG_KO.view.toast.signupDone, {
      type: "success",
      duration: 4000,
    });
    currentUrl.searchParams.delete("signup");
    const nextSearch = currentUrl.searchParams.toString();
    const nextUrl = nextSearch
      ? `${currentUrl.pathname}?${nextSearch}`
      : currentUrl.pathname;
    window.history.replaceState({}, "", nextUrl);
  }, [showToast]);

  /* 9. 내부 컴포넌트 ============================================================================================================== */

  // 없음

  /* 10. 렌더링 ==================================================================================================================== */
  if (isAuthed) {
    return null;
  }
  return (
    <main className="min-h-screen flex items-center justify-center bg-gray-50 p-4 sm:p-6">
      <div className="flex w-full max-w-5xl mx-4 shadow-xl rounded-2xl overflow-hidden bg-white">
        <aside className="hidden w-2/5 flex-col items-center justify-center space-y-4 bg-gradient-to-br from-[#1e3a5f] to-[#312e81] p-12 text-white lg:flex">
          <h1 className="text-3xl font-bold">{LANG_KO.view.side.title}</h1>
          <p className="max-w-xs text-center text-sm text-white/80">
            {LANG_KO.view.side.subtitle}
          </p>
          <ul className="w-full max-w-xs list-inside list-disc space-y-1 text-left text-sm text-white/90">
            <li>{LANG_KO.view.side.pointList[0]}</li>
            <li>{LANG_KO.view.side.pointList[1]}</li>
            <li>{LANG_KO.view.side.pointList[2]}</li>
          </ul>
        </aside>

        <section className="w-full p-6 sm:p-10 md:p-16 lg:w-3/5">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-semibold text-gray-900 mb-2">
              {LANG_KO.view.form.title}
            </h2>
            <p className="text-sm text-gray-600">
              {LANG_KO.view.form.subtitle}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6" noValidate>
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
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm text-slate-600">
              {LANG_KO.view.form.operatorNotice}
            </div>

            <div>
              <label
                htmlFor="login-password"
                className="block text-sm font-medium text-gray-700"
              >
                {LANG_KO.view.form.passwordLabel}
              </label>
              <div className="mt-2">
                <Input
                  id="login-password"
                  type="password"
                  autoComplete="current-password"
                  togglePassword
                  dataObj={loginObj}
                  dataKey="password"
                  ref={passwordRef}
                  placeholder={LANG_KO.view.form.passwordPlaceholder}
                  aria-describedby={passwordErrorId}
                  error={loginObj.errors.password}
                />
                {loginObj.errors.password && (
                  <p id={passwordErrorId} className="mt-2 text-sm text-red-600">
                    {loginObj.errors.password}
                  </p>
                )}
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-2">
              <Checkbox
                dataObj={loginObj}
                dataKey="rememberMe"
                label={LANG_KO.view.form.rememberMeLabel}
              />
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              className="w-full"
              loading={ui.pending}
            >
              {LANG_KO.view.form.submitLabel}
            </Button>

          </form>
        </section>
      </div>
    </main>
  );
};

export default LoginView;
