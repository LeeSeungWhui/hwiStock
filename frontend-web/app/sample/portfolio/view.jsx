"use client";

/**
 * 파일명: sample/portfolio/view.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 공개 포트폴리오 페이지 뷰(시각 중심 리뉴얼)
 */

import Image from "next/image";
import Link from "next/link";
import { PAGE_CONFIG } from "./initData";
import { usePageData } from "@/app/lib/hooks/usePageData";
import LANG_KO from "./lang.ko";

/**
 * @description 공개 포트폴리오 콘텐츠를 시각 섹션으로 구성해 렌더링. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const PortfolioView = ({ initialDataObj, initialErrorObj }) => {

  /* 1. 상수 ======================================================================================================================= */
  const samplePortfolioContent = LANG_KO.initData.content;

  /* 2. 데이터 ======================================================================================================================= */
  const { mode: pageMode, dataObj } = usePageData({
    pageConfig: PAGE_CONFIG,
    initialDataObj,
    initialErrorObj,
  });
  const overview = dataObj?.overview?.result || {};
  const dashboard = dataObj?.dashboard?.result || {};
  const overviewCardList = [
    {
      label: LANG_KO.view.overviewCard.taskCount,
      value: `${Number(overview?.taskCount || 0).toLocaleString("ko-KR")}${LANG_KO.view.overviewCard.countSuffix}`,
    },
    {
      label: LANG_KO.view.overviewCard.adminUserCount,
      value: `${Number(overview?.adminUserCount || 0).toLocaleString("ko-KR")}${LANG_KO.view.overviewCard.userSuffix}`,
    },
    {
      label: LANG_KO.view.overviewCard.formSubmissionCount,
      value: `${Number(overview?.formSubmissionCount || 0).toLocaleString("ko-KR")}${LANG_KO.view.overviewCard.countSuffix}`,
    },
  ];
  const recentTaskList = (dashboard?.recentList || []).slice(0, 3);

  /* 3. UI ========================================================================================================================= */

  // 없음

  /* 4. 팝업 ======================================================================================================================= */

  // 없음

  /* 5. 기타 ======================================================================================================================= */

  // 없음

  /* 6. 커스텀 훅 =================================================================================================================== */

  // 없음

  /* 7. 함수 ======================================================================================================================= */

  // 없음

  /* 8. useEffect ================================================================================================================== */

  // 없음

  /* 9. 내부 컴포넌트 ============================================================================================================== */

  // 없음

  /* 10. 렌더링 ==================================================================================================================== */
  return (
    <>
      <section
        className="overflow-hidden rounded-3xl bg-gradient-to-br from-[#1e3a5f] to-[#312e81] px-6 py-10 text-white shadow-xl sm:px-10"
        data-page-mode={pageMode}
      >
        <p className="text-xs font-semibold tracking-wide text-blue-100">
          {LANG_KO.view.heroBadge}
        </p>
        <h1 className="mt-3 text-3xl font-bold leading-tight sm:text-4xl">
          {samplePortfolioContent.hero.title}
        </h1>
        <p className="mt-4 max-w-3xl text-sm text-blue-50 sm:text-base">
          {samplePortfolioContent.hero.subtitle}
        </p>
        <ul className="mt-5 space-y-2 text-sm text-blue-50">
          {samplePortfolioContent.hero.summary.map((line) => (
            <li key={line} className="flex items-start gap-2">
              <span className="mt-1 h-1.5 w-1.5 rounded-full bg-blue-200" aria-hidden />
              <span>{line}</span>
            </li>
          ))}
        </ul>
        <div className="mt-6 flex flex-wrap gap-3">
          {samplePortfolioContent.hero.cta.map((ctaItem) => (
            <Link
              key={ctaItem.href}
              href={ctaItem.href}
              className={`inline-flex items-center rounded-md px-4 py-2 text-sm font-semibold transition ${
                ctaItem.variant === "outline"
                  ? "border border-blue-200 text-blue-50 hover:bg-white/10"
                  : "bg-blue-500 text-white hover:bg-blue-400"
              }`}
            >
              {ctaItem.label}
            </Link>
          ))}
        </div>
      </section>

      <section className="mt-8">
        <h2 className="text-2xl font-bold text-gray-900">{LANG_KO.view.sectionTitle.overview}</h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          {overviewCardList.map((overviewCardObj) => (
            <article
              key={overviewCardObj.label}
              className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm"
            >
              <p className="text-xs text-gray-500">{overviewCardObj.label}</p>
              <p className="mt-2 text-sm font-semibold text-gray-900">{overviewCardObj.value}</p>
            </article>
          ))}
        </div>
        {recentTaskList.length > 0 ? (
          <div className="mt-4 grid gap-3 md:grid-cols-3">
            {recentTaskList.map((recentTaskObj) => (
              <article
                key={recentTaskObj.id}
                className="rounded-xl border border-blue-100 bg-blue-50 p-4"
              >
                <p className="text-xs text-blue-700">{recentTaskObj.createdAt || "-"}</p>
                <p className="mt-2 text-sm font-semibold text-gray-900">{recentTaskObj.title || "-"}</p>
                <p className="mt-1 text-xs text-gray-600">
                  {LANG_KO.view.label.status}: {recentTaskObj.status || "-"}
                </p>
              </article>
            ))}
          </div>
        ) : null}
      </section>

      <section className="mt-8 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
        <details open={false}>
          <summary className="cursor-pointer list-none text-2xl font-bold text-gray-900">
            {LANG_KO.view.sectionTitle.profile}
          </summary>
          <p className="mt-2 text-sm text-gray-600">{samplePortfolioContent.profile.tagline}</p>
          <div className="mt-4">
            <p className="text-sm text-gray-500">{LANG_KO.view.label.developer}</p>
            <p className="text-lg font-semibold text-gray-900">
              {samplePortfolioContent.profile.name} · {samplePortfolioContent.profile.role}
            </p>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            {(samplePortfolioContent.profile.quickFacts || []).map((fact) => (
              <span
                key={fact}
                className="rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700"
              >
                {fact}
              </span>
            ))}
          </div>

          <ul className="mt-4 space-y-2 text-sm text-gray-700">
            {(samplePortfolioContent.profile.strengths || []).map((line) => (
              <li key={line} className="flex items-start gap-2">
                <span className="mt-1 h-1.5 w-1.5 rounded-full bg-blue-500" aria-hidden />
                <span>{line}</span>
              </li>
            ))}
          </ul>

          <div className="mt-6">
            <h3 className="text-base font-semibold text-gray-900">{LANG_KO.view.sectionTitle.featuredProjects}</h3>
            <div className="mt-3 grid gap-3 md:grid-cols-2">
              {(samplePortfolioContent.profile.featuredProjects || []).map((projectItem) => (
                <article
                  key={projectItem.title}
                  className="rounded-xl border border-gray-200 bg-gray-50 p-4"
                >
                  <p className="text-sm font-semibold text-gray-900">{projectItem.title}</p>
                  <p className="mt-1 text-xs text-gray-500">{projectItem.period}</p>
                  <p className="mt-2 text-sm text-gray-700">{projectItem.summary}</p>
                  <p className="mt-2 text-xs text-gray-600">{projectItem.stack}</p>
                </article>
              ))}
            </div>
          </div>

          <div className="mt-6">
            <h3 className="text-base font-semibold text-gray-900">{LANG_KO.view.sectionTitle.careerTimeline}</h3>
            <div className="mt-3 space-y-2">
              {(samplePortfolioContent.profile.careerTimeline || []).map((companyItem) => (
                <details
                  key={companyItem.company}
                  className="rounded-lg border border-gray-200 bg-white p-3"
                >
                  <summary className="cursor-pointer list-none text-sm font-semibold text-gray-900">
                    {companyItem.company} · {companyItem.period}
                  </summary>
                  <p className="mt-2 text-xs text-gray-500">
                    {companyItem.position} · {companyItem.summary}
                  </p>
                  <ul className="mt-2 space-y-1 text-sm text-gray-700">
                    {(companyItem.highlights || []).map((line) => (
                      <li key={line} className="flex items-start gap-2">
                        <span className="mt-1 h-1.5 w-1.5 rounded-full bg-gray-400" aria-hidden />
                        <span>{line}</span>
                      </li>
                    ))}
                  </ul>
                </details>
              ))}
            </div>
          </div>

          <div className="mt-6">
            <h3 className="text-base font-semibold text-gray-900">{LANG_KO.view.sectionTitle.education}</h3>
            <div className="mt-3 grid gap-2 md:grid-cols-2">
              {(samplePortfolioContent.profile.education || []).map((educationItem) => (
                <article
                  key={educationItem.school}
                  className="rounded-lg border border-gray-200 bg-white p-3"
                >
                  <p className="text-sm font-semibold text-gray-900">{educationItem.school}</p>
                  {educationItem.period ? (
                    <p className="mt-1 text-xs text-gray-500">{educationItem.period}</p>
                  ) : null}
                  <p className="mt-1 text-xs text-gray-600">{educationItem.detail}</p>
                </article>
              ))}
            </div>
          </div>

          <div className="mt-6">
            <h3 className="text-base font-semibold text-gray-900">{LANG_KO.view.sectionTitle.research}</h3>
            <ul className="mt-2 space-y-1 text-sm text-gray-700">
              {(samplePortfolioContent.profile.research || []).map((line) => (
                <li key={line} className="flex items-start gap-2">
                  <span className="mt-1 h-1.5 w-1.5 rounded-full bg-indigo-500" aria-hidden />
                  <span>{line}</span>
                </li>
              ))}
            </ul>
          </div>
        </details>
      </section>

      <section className="mt-8">
        <h2 className="text-2xl font-bold text-gray-900">{LANG_KO.view.sectionTitle.strengths}</h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          {samplePortfolioContent.features.map((featureObj) => (
            <article
              key={featureObj.title}
              className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm"
            >
              <h3 className="text-sm font-semibold text-gray-900">{featureObj.title}</h3>
              <p className="mt-2 text-sm leading-6 text-gray-600">{featureObj.detail}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="mt-8 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
        <h2 className="text-2xl font-bold text-gray-900">{LANG_KO.view.sectionTitle.architecture}</h2>
        <p className="mt-2 text-sm text-gray-600">
          {LANG_KO.view.label.architectureDescription}
        </p>
        <div className="mt-5 grid gap-3 md:grid-cols-[1fr_auto_1fr_auto_1fr]">
          {samplePortfolioContent.architectureFlow.map((stepItem, index) => (
            <div key={stepItem.title} className="contents">
              <div className="relative min-h-[116px] rounded-xl border border-blue-100 bg-white px-4 py-4 text-center shadow-sm">
                <p className="text-2xl" aria-hidden>
                  {stepItem.icon}
                </p>
                <p className="mt-2 text-sm font-semibold text-gray-900">{stepItem.title}</p>
                <p className="mt-1 text-xs text-gray-600">{stepItem.description}</p>
              </div>
              {index < samplePortfolioContent.architectureFlow.length - 1 ? (
                <div className="hidden items-center justify-center text-xl text-gray-400 md:flex">
                  →
                </div>
              ) : null}
            </div>
          ))}
        </div>
      </section>

      <section className="mt-8">
        <h2 className="text-2xl font-bold text-gray-900">{LANG_KO.view.sectionTitle.demoFlow}</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {samplePortfolioContent.demoFlow.map((demoFlowObj) => (
            <article
              key={demoFlowObj.path}
              className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm"
            >
              <div className="relative h-40 w-full bg-gray-100">
                <Image
                  src={demoFlowObj.imageSrc}
                  alt={demoFlowObj.imageAlt}
                  fill
                  className="object-cover"
                  sizes="(max-width: 768px) 100vw, 33vw"
                />
              </div>
              <div className="space-y-2 p-4">
                <h3 className="text-base font-semibold text-gray-900">{demoFlowObj.name}</h3>
                <p className="text-sm text-gray-600">{demoFlowObj.note}</p>
                <Link
                  href={demoFlowObj.path}
                  className="inline-flex items-center rounded-md bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-blue-700"
                >
                  {LANG_KO.view.label.moveSample}
                </Link>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="mt-8">
        <details className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm" open={false}>
          <summary className="cursor-pointer list-none text-base font-semibold text-gray-900">
            {LANG_KO.view.sectionTitle.technicalNotes}
          </summary>
          <ul className="mt-3 space-y-2 text-sm text-gray-700">
            {samplePortfolioContent.technicalNotes.map((line) => (
              <li key={line} className="flex items-start gap-2">
                <span className="mt-1 h-1.5 w-1.5 rounded-full bg-indigo-500" aria-hidden />
                <span>{line}</span>
              </li>
            ))}
          </ul>
        </details>
      </section>
    </>
  );
};

export default PortfolioView;
