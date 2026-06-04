"use client";

/**
 * 파일명: sample/form/view.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 공개 복합 폼 샘플 페이지 뷰(DB 폼 메타/제출 연동)
 */

import { useEffect, useMemo } from "react";
import { useGlobalUi } from "@/app/common/store/SharedStore";
import Button from "@/app/lib/component/Button";
import Card from "@/app/lib/component/Card";
import CheckButton from "@/app/lib/component/CheckButton";
import Input from "@/app/lib/component/Input";
import Select from "@/app/lib/component/Select";
import Textarea from "@/app/lib/component/Textarea";
import EasyObj from "@/app/lib/dataset/EasyObj";
import { PAGE_CONFIG } from "./initData";
import { usePageData } from "@/app/lib/hooks/usePageData";
import { apiJSON } from "@/app/lib/runtime/api";
import LANG_KO from "./lang.ko";

/**
 * @description 공개 복합 폼 샘플 화면을 렌더링. 입력/출력 계약을 함께 명시
 * 처리 규칙: 선택 코드/최근 제출 메타는 DB에서 로드하고, 제출 버튼은 public sample API로 저장한다.
 */
const FormDemoView = ({ initialDataObj, initialErrorObj }) => {

  /* 1. 상수 ======================================================================================================================= */
  const stepList = LANG_KO.view.stepList;
  const categorySourceList = LANG_KO.initData.categoryOptions;
  const featureSourceList = LANG_KO.initData.featureOptions;
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  const formSeedObj = {
    name: "",
    email: "",
    phone: "",
    category: "",
    startDate: "",
    endDate: "",
    budgetRange: "",
    requirement: "",
    referenceUrl: "",
    attachmentName: "",
    selectedFeatures: [],
  };
  const stepErrorSeedObj = {
    name: "",
    email: "",
    phone: "",
    category: "",
    startDate: "",
    endDate: "",
    budgetRange: "",
  };

  /* 2. 데이터 ======================================================================================================================= */
  const { mode: pageMode, dataObj, isLoading } = usePageData({
    pageConfig: PAGE_CONFIG,
    initialDataObj,
    initialErrorObj,
  });
  const initialMetaResult = useMemo(
    () => dataObj?.meta?.result || {},
    [dataObj?.meta?.result],
  );
  const { showToast } = useGlobalUi();
  const ui = EasyObj({
    step: 1,
    isSubmitting: false,
    form: { ...formSeedObj },
    stepOneErrors: { ...stepErrorSeedObj },
  });
  const formMetaObj = EasyObj(initialMetaResult);
  const latestSubmissionObj = EasyObj(initialMetaResult.latestSubmission || {});
  const categoryCodeList = formMetaObj?.categoryCodeList || [];
  const featureCodeList = formMetaObj?.featureCodeList || [];
  const categoryOptionList = categorySourceList.filter((categoryOptionObj) => (
    categoryOptionObj.value === "" || categoryCodeList.includes(categoryOptionObj.value)
  ));
  const featureOptionList = featureSourceList.filter((featureOptionObj) => featureCodeList.includes(featureOptionObj.key));
  const categoryLabelMap = Object.fromEntries(
    categoryOptionList.map((categoryOptionObj) => [categoryOptionObj.value, categoryOptionObj.text]),
  );
  const featureLabelMap = Object.fromEntries(
    featureOptionList.map((featureOptionObj) => [featureOptionObj.key, featureOptionObj.label]),
  );

  /* 3. UI ========================================================================================================================= */
  const stepOneErrorIds = {
    name: ui.stepOneErrors.name ? "demo-form-name-error" : undefined,
    email: ui.stepOneErrors.email ? "demo-form-email-error" : undefined,
    phone: ui.stepOneErrors.phone ? "demo-form-phone-error" : undefined,
    category: ui.stepOneErrors.category ? "demo-form-category-error" : undefined,
    startDate: ui.stepOneErrors.startDate ? "demo-form-start-date-error" : undefined,
    endDate: ui.stepOneErrors.endDate ? "demo-form-end-date-error" : undefined,
    budgetRange: ui.stepOneErrors.budgetRange ? "demo-form-budget-range-error" : undefined,
  };
  const summaryRows = [
    { label: LANG_KO.view.summaryLabel.name, value: ui.form.name || "-" },
    { label: LANG_KO.view.summaryLabel.email, value: ui.form.email || "-" },
    { label: LANG_KO.view.summaryLabel.phone, value: ui.form.phone || "-" },
    {
      label: LANG_KO.view.summaryLabel.category,
      value: categoryLabelMap[ui.form.category] || "-",
    },
    {
      label: LANG_KO.view.summaryLabel.period,
      value: `${ui.form.startDate || "-"} ~ ${ui.form.endDate || "-"}`,
    },
    { label: LANG_KO.view.summaryLabel.budgetRange, value: ui.form.budgetRange || "-" },
    {
      label: LANG_KO.view.summaryLabel.features,
      value: ui.form.selectedFeatures.length > 0
        ? ui.form.selectedFeatures.map((featureCode) => featureLabelMap[featureCode] || featureCode).join(", ")
        : "-",
    },
    { label: LANG_KO.view.summaryLabel.requirement, value: ui.form.requirement || "-" },
    { label: LANG_KO.view.summaryLabel.referenceUrl, value: ui.form.referenceUrl || "-" },
    { label: LANG_KO.view.summaryLabel.attachmentName, value: ui.form.attachmentName || "-" },
  ];

  /* 4. 팝업 ======================================================================================================================= */

  // 없음

  /* 5. 기타 ======================================================================================================================= */

  // 없음

  /* 6. 커스텀 훅 =================================================================================================================== */

  // 없음

  /* 7. 함수 ======================================================================================================================= */

  /**
   * @description 요청 단계 번호 보정과 현재 단계 갱신
   * 처리 규칙: 숫자 변환 뒤 1~3 범위로 clamp한 값을 ui.step에 반영한다.
   * @param {number} nextStep
   */
  const moveStep = (nextStep) => {
    ui.step = Math.min(3, Math.max(1, Number(nextStep || 1)));
  };

  /**
   * @description 1단계 입력 유효성을 검사하고 오류 상태를 갱신
   * 실패 동작: 오류가 하나라도 있으면 토스트를 노출하고 false를 반환한다.
   * @returns {boolean}
   */
  const validateStepOne = () => {
    const nextStepErrorObj = { ...stepErrorSeedObj };
    const formName = String(ui.form.name || "").trim();
    const email = String(ui.form.email || "").trim();
    const phone = String(ui.form.phone || "").trim();
    const category = String(ui.form.category || "").trim();
    const startDate = String(ui.form.startDate || "").trim();
    const endDate = String(ui.form.endDate || "").trim();
    const budgetRange = String(ui.form.budgetRange || "").trim();

    if (!formName) nextStepErrorObj.name = LANG_KO.view.validation.nameRequired;
    if (!email || !emailPattern.test(email)) nextStepErrorObj.email = LANG_KO.view.validation.emailInvalid;
    if (!phone) nextStepErrorObj.phone = LANG_KO.view.validation.phoneRequired;
    if (!category) nextStepErrorObj.category = LANG_KO.view.validation.categoryRequired;
    if (!startDate) nextStepErrorObj.startDate = LANG_KO.view.validation.startDateRequired;
    if (!endDate) nextStepErrorObj.endDate = LANG_KO.view.validation.endDateRequired;
    if (!budgetRange) nextStepErrorObj.budgetRange = LANG_KO.view.validation.budgetRangeRequired;
    const hasInvalidDateRange = startDate && endDate && startDate > endDate;
    if (hasInvalidDateRange) {
      nextStepErrorObj.endDate = LANG_KO.view.validation.endDateAfterStartDate;
    }

    const hasError = Object.values(nextStepErrorObj).some(Boolean);
    ui.stepOneErrors = nextStepErrorObj;
    if (hasError) {
      showToast(LANG_KO.view.validation.requiredFieldToast, { type: "error" });
      return false;
    }
    return true;
  };

  /**
   * @description 기능 코드를 selectedFeatures 배열에서 토글
   * 처리 규칙: 이미 존재하면 제거하고, 없으면 배열 끝에 추가한다.
   * @param {string} featureCode
   */
  const toggleFeature = (featureCode) => {
    const exists = ui.form.selectedFeatures.includes(featureCode);
    if (exists) {
      ui.form.selectedFeatures = ui.form.selectedFeatures.filter((featureCodeValue) => featureCodeValue !== featureCode);
      return;
    }
    ui.form.selectedFeatures = [...ui.form.selectedFeatures, featureCode];
  };

  /**
   * @description DB에 폼 제출을 저장하고 최신 메타를 로컬 상태에 반영
   * 실패 동작: API 실패 시 에러 토스트를 노출하고 현재 입력값은 유지한다.
   */
  const submitForm = async () => {
    ui.isSubmitting = true;
    try {
      const submitResponse = await apiJSON(
        PAGE_CONFIG.API.submit,
        {
          method: "POST",
          body: {
            ...ui.form,
            selectedFeatures: [...ui.form.selectedFeatures],
          },
        },
        { authless: true },
      );
      latestSubmissionObj.copy(submitResponse?.result || {});
      formMetaObj.submissionCount = Number(formMetaObj.submissionCount || 0) + 1;
      ui.form = { ...formSeedObj };
      ui.stepOneErrors = { ...stepErrorSeedObj };
      ui.step = 1;
      showToast(LANG_KO.view.action.submitSuccessToast, { type: "success" });
    } catch (err) {
      showToast(err?.message || LANG_KO.view.error.submitFailed, { type: "error" });
    } finally {
      ui.isSubmitting = false;
    }
  };

  /* 8. useEffect ================================================================================================================== */
  /**
   * @description SSR 초기 메타 스냅샷 변경 시 form 메타/최근 제출 객체 동기화
   * 처리 규칙: meta 전체는 formMetaObj.copy, latestSubmission은 별도 copy로 반영
   */
  useEffect(() => {
    formMetaObj.copy(initialMetaResult);
    latestSubmissionObj.copy(initialMetaResult.latestSubmission || {});
  }, [dataObj?.meta?.result, formMetaObj, initialMetaResult, latestSubmissionObj]);

  /* 9. 내부 컴포넌트 ============================================================================================================== */

  // 없음

  /* 10. 렌더링 ==================================================================================================================== */
  return (
    <div className="mx-auto w-full max-w-4xl px-4 py-8 sm:px-6 lg:px-8" data-page-mode={pageMode}>
      <section className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">{LANG_KO.view.page.title}</h1>
        <p className="mt-2 text-sm text-gray-600">
          {LANG_KO.view.page.subtitle}
        </p>
      </section>

      <section className="mb-5 grid gap-3 md:grid-cols-2">
        <Card title={`${LANG_KO.view.card.submissionTitlePrefix} ${Number(formMetaObj.submissionCount || 0).toLocaleString("ko-KR")}${LANG_KO.view.card.submissionTitleSuffix}`}>
          <p className="text-sm text-gray-600">
            {LANG_KO.view.card.submissionDescription}
          </p>
        </Card>
        <Card title={LANG_KO.view.card.latestSubmissionTitle}>
          {latestSubmissionObj?.id ? (
            <div className="space-y-1 text-sm text-gray-700">
              <p>{latestSubmissionObj?.name || "-"}</p>
              <p>{latestSubmissionObj?.email || "-"}</p>
              <p>{latestSubmissionObj?.createdAt || "-"}</p>
            </div>
          ) : (
            <p className="text-sm text-gray-500">{LANG_KO.view.card.latestSubmissionEmpty}</p>
          )}
        </Card>
      </section>

      <ol className="mb-5 grid gap-2 sm:grid-cols-3">
        {stepList.map((stepItem) => (
          <li
            key={stepItem.step}
            className={`rounded-lg border px-4 py-3 text-sm ${
              stepItem.step === ui.step
                ? "border-blue-500 bg-blue-50 text-blue-700"
                : "border-gray-200 bg-white text-gray-500"
            }`}
          >
            {stepItem.step}. {stepItem.label}
          </li>
        ))}
      </ol>

      {isLoading ? (
        <Card title={LANG_KO.view.page.loadingCardTitle}>
          <p className="text-sm text-gray-600">{LANG_KO.view.page.loadingCardBody}</p>
        </Card>
      ) : null}

      {ui.step === 1 ? (
        <Card title={LANG_KO.view.card.step1Title}>
          <div className="grid gap-3 md:grid-cols-2">
            <label className="block space-y-1">
              <span className="text-sm font-medium text-gray-700">{LANG_KO.view.summaryLabel.name}</span>
              <Input
                dataObj={ui}
                dataKey="form.name"
                placeholder={LANG_KO.view.input.namePlaceholder}
                error={ui.stepOneErrors.name}
                aria-describedby={stepOneErrorIds.name}
              />
              {ui.stepOneErrors.name ? <p id={stepOneErrorIds.name} className="text-xs text-red-600">{ui.stepOneErrors.name}</p> : null}
            </label>

            <label className="block space-y-1">
              <span className="text-sm font-medium text-gray-700">{LANG_KO.view.summaryLabel.email}</span>
              <Input
                dataObj={ui}
                dataKey="form.email"
                placeholder={LANG_KO.view.input.emailPlaceholder}
                type="email"
                error={ui.stepOneErrors.email}
                aria-describedby={stepOneErrorIds.email}
              />
              {ui.stepOneErrors.email ? <p id={stepOneErrorIds.email} className="text-xs text-red-600">{ui.stepOneErrors.email}</p> : null}
            </label>

            <label className="block space-y-1">
              <span className="text-sm font-medium text-gray-700">{LANG_KO.view.summaryLabel.phone}</span>
              <Input
                dataObj={ui}
                dataKey="form.phone"
                placeholder={LANG_KO.view.input.phonePlaceholder}
                error={ui.stepOneErrors.phone}
                aria-describedby={stepOneErrorIds.phone}
              />
              {ui.stepOneErrors.phone ? <p id={stepOneErrorIds.phone} className="text-xs text-red-600">{ui.stepOneErrors.phone}</p> : null}
            </label>

            <label className="block space-y-1">
              <span className="text-sm font-medium text-gray-700">{LANG_KO.view.summaryLabel.category}</span>
              <Select
                dataObj={ui}
                dataKey="form.category"
                dataList={categoryOptionList}
                error={ui.stepOneErrors.category}
                aria-describedby={stepOneErrorIds.category}
              />
              {ui.stepOneErrors.category ? <p id={stepOneErrorIds.category} className="text-xs text-red-600">{ui.stepOneErrors.category}</p> : null}
            </label>

            <label className="block space-y-1">
              <span className="text-sm font-medium text-gray-700">{LANG_KO.view.summaryLabel.startDate}</span>
              <Input
                dataObj={ui}
                dataKey="form.startDate"
                type="date"
                error={ui.stepOneErrors.startDate}
                aria-describedby={stepOneErrorIds.startDate}
              />
              {ui.stepOneErrors.startDate ? <p id={stepOneErrorIds.startDate} className="text-xs text-red-600">{ui.stepOneErrors.startDate}</p> : null}
            </label>

            <label className="block space-y-1">
              <span className="text-sm font-medium text-gray-700">{LANG_KO.view.summaryLabel.endDate}</span>
              <Input
                dataObj={ui}
                dataKey="form.endDate"
                type="date"
                error={ui.stepOneErrors.endDate}
                aria-describedby={stepOneErrorIds.endDate}
              />
              {ui.stepOneErrors.endDate ? <p id={stepOneErrorIds.endDate} className="text-xs text-red-600">{ui.stepOneErrors.endDate}</p> : null}
            </label>

            <label className="block space-y-1 md:col-span-2">
              <span className="text-sm font-medium text-gray-700">{LANG_KO.view.summaryLabel.budgetRange}</span>
              <Input
                dataObj={ui}
                dataKey="form.budgetRange"
                placeholder={LANG_KO.view.input.budgetRangePlaceholder}
                error={ui.stepOneErrors.budgetRange}
                aria-describedby={stepOneErrorIds.budgetRange}
              />
              {ui.stepOneErrors.budgetRange ? <p id={stepOneErrorIds.budgetRange} className="text-xs text-red-600">{ui.stepOneErrors.budgetRange}</p> : null}
            </label>
          </div>
        </Card>
      ) : null}

      {ui.step === 2 ? (
        <Card title={LANG_KO.view.card.step2Title}>
          <div className="space-y-3">
            <label className="block space-y-1">
              <span className="text-sm font-medium text-gray-700">{LANG_KO.view.summaryLabel.requirement}</span>
              <Textarea
                dataObj={ui}
                dataKey="form.requirement"
                placeholder={LANG_KO.view.input.requirementPlaceholder}
                rows={5}
              />
            </label>

            <div className="space-y-1">
              <span className="text-sm font-medium text-gray-700">{LANG_KO.view.summaryLabel.features}</span>
              <div className="flex flex-wrap gap-2">
                {featureOptionList.map((featureItem) => {
                  const isSelected = ui.form.selectedFeatures.includes(featureItem.key);

                  // rule-gate: allow-controlled-binding - 다중 선택 토글은 selectedFeatures 배열 포함/제거 제어가 필요함
                  return (
                    <CheckButton
                      key={featureItem.key}
                      checked={isSelected}
                      onChange={() => toggleFeature(featureItem.key)}
                    >
                      {featureItem.label}
                    </CheckButton>
                  );
                })}
              </div>
            </div>

            <label className="block space-y-1">
              <span className="text-sm font-medium text-gray-700">{LANG_KO.view.summaryLabel.referenceUrl}</span>
              <Input
                dataObj={ui}
                dataKey="form.referenceUrl"
                placeholder={LANG_KO.view.input.referenceUrlPlaceholder}
              />
            </label>

            <label className="block space-y-1">
              <span className="text-sm font-medium text-gray-700">{LANG_KO.view.summaryLabel.attachmentName}</span>

              {/* raw file input 예외 사유: 공용 lib/component에 파일 선택 전용 컴포넌트가 없어 브라우저 기본 picker 사용 */}
              <input
                type="file"
                className="block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700"
                onChange={(event) => {
                  const nextFile = event?.target?.files?.[0];
                  ui.form.attachmentName = nextFile?.name || "";
                }}
              />
              {ui.form.attachmentName ? <p className="text-xs text-gray-500">{ui.form.attachmentName}</p> : null}
            </label>
          </div>
        </Card>
      ) : null}

      {ui.step === 3 ? (
        <Card title={LANG_KO.view.card.step3Title}>
          <ul className="space-y-2 text-sm text-gray-700">
            {summaryRows.map((summaryItem) => (
              <li
                key={summaryItem.label}
                className="grid grid-cols-[96px_1fr] gap-2 sm:grid-cols-[120px_1fr]"
              >
                <span className="font-medium text-gray-500">{summaryItem.label}</span>
                <span>{summaryItem.value}</span>
              </li>
            ))}
          </ul>
        </Card>
      ) : null}

      <div className="mt-4 flex flex-col-reverse gap-2 sm:flex-row sm:items-center sm:justify-between">
        <Button
          variant="secondary"
          onClick={() => moveStep(ui.step - 1)}
          disabled={ui.step === 1 || ui.isSubmitting}
          className="w-full sm:w-auto"
        >
          {LANG_KO.view.action.prev}
        </Button>
        {ui.step < 3 ? (
          <Button
            variant="primary"
            className="w-full sm:w-auto"
            onClick={() => {
              if (ui.step === 1) {
                const isValid = validateStepOne();
                if (!isValid) return;
                ui.stepOneErrors = { ...stepErrorSeedObj };
              }
              moveStep(ui.step + 1);
            }}
          >
            {LANG_KO.view.action.next}
          </Button>
        ) : (
          <Button
            variant="primary"
            className="w-full sm:w-auto"
            onClick={submitForm}
            disabled={ui.isSubmitting}
          >
            {LANG_KO.view.action.submit}
          </Button>
        )}
      </div>
    </div>
  );
};

export default FormDemoView;
