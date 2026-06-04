"use client";

/**
 * 파일명: forgot-password/view.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 비밀번호 찾기 페이지 클라이언트 뷰
 */

import { useEffect, useRef } from "react";
import EasyObj from "@/app/lib/dataset/EasyObj";
import Button from "@/app/lib/component/Button";
import Input from "@/app/lib/component/Input";
import Link from "next/link";
import { PAGE_CONFIG } from "./initData";
import { normalizePageConfig } from "@/app/lib/runtime/pageData";
import { apiJSON } from "@/app/lib/runtime/api";
import LANG_KO from "./lang.ko";

/**
 * @description 비밀번호 찾기 이메일 입력/검증/제출 상태를 관리하는 화면을 렌더링. 입력/출력 계약을 함께 명시
 * 처리 규칙: 유효한 이메일 제출 시 submitted 상태로 전환해 안내 메시지를 노출한다.
 */
const ForgotPasswordView = () => {

  /* 1. 상수 ======================================================================================================================= */
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  /* 2. 데이터 ======================================================================================================================= */
  const formObj = EasyObj({
    email: "",
    errors: {
      email: "",
    },
  });
  const ui = EasyObj({
    pending: false,
    submitted: false,
    formError: "",
  });
  const emailRef = useRef(null);
  const errorSummaryRef = useRef(null);
  const focusFrameRef = useRef(null);
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
   * @description 이메일 입력값을 trim/lowercase 후 형식을 점검
   * 실패 동작: 형식 불일치 시 에러 메시지 설정 후 이메일 입력으로 포커스를 이동하고 false를 반환한다.
   * @updated 2026-02-27
   */
  const validate = () => {
    formObj.errors.email = "";
    ui.formError = "";
    const email = String(formObj.email || "").trim().toLowerCase();
    formObj.email = email;
    if (!email || !emailPattern.test(email)) {
      formObj.errors.email = LANG_KO.view.validation.emailInvalid;
      ui.formError = formObj.errors.email;
      cancelAnimationFrame(focusFrameRef.current);
      focusFrameRef.current = requestAnimationFrame(() => {
        emailRef.current?.focus();
      });
      return false;
    }
    return true;
  };

  /**
   * @description 비밀번호 찾기 요청 제출 흐름을 진행
   * 실패 동작: 비동기 처리 실패 시 ui.formError를 노출하고 에러 요약 영역으로 포커스를 이동한다.
   * @updated 2026-02-27
   */
  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!validate()) return;
    ui.pending = true;
    ui.submitted = false;
    try {
      await apiJSON(
        PAGE_CONFIG.API.requestPasswordReset,
        {
          method: "POST",
          body: {
            email: formObj.email,
          },
        },
        { authless: true },
      );
      ui.submitted = true;
    } catch {
      ui.formError = LANG_KO.view.error.requestFailed;
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
    <main className="min-h-screen flex items-center justify-center bg-gray-50 p-6" data-page-mode={pageMode}>
      <section className="w-full max-w-xl rounded-2xl bg-white p-10 shadow-xl">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-semibold text-gray-900">{LANG_KO.view.form.title}</h1>
          <p className="mt-2 text-sm text-gray-600">
            {LANG_KO.view.form.subtitle}
          </p>
        </div>

        {ui.submitted ? (
          <div className="rounded-md border border-green-200 bg-green-50 p-4 text-sm text-green-700">
            {LANG_KO.view.form.submittedMessage}
          </div>
        ) : null}

        <form onSubmit={handleSubmit} className="mt-5 space-y-5" noValidate>
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
            <label htmlFor="forgot-email" className="block text-sm font-medium text-gray-700">
              {LANG_KO.view.form.emailLabel}
            </label>
            <div className="mt-2">
              <Input
                id="forgot-email"
                type="email"
                dataObj={formObj}
                dataKey="email"
                ref={emailRef}
                placeholder={LANG_KO.view.form.emailPlaceholder}
                error={formObj.errors.email}
              />
              {formObj.errors.email ? (
                <p className="mt-2 text-sm text-red-600">{formObj.errors.email}</p>
              ) : null}
            </div>
          </div>

          <Button type="submit" variant="primary" size="lg" className="w-full" loading={ui.pending}>
            {LANG_KO.view.form.submitLabel}
          </Button>
        </form>

        <div className="mt-6 text-center text-sm text-gray-600">
          <Link href="/login" className="font-medium text-blue-600 hover:text-blue-500">
            {LANG_KO.view.form.backToLoginLabel}
          </Link>
        </div>
      </section>
    </main>
  );
};

export default ForgotPasswordView;
