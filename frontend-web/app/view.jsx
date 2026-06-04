"use client";

/**
 * 파일명: app/view.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 루트 랜딩 페이지 뷰
 */

import Link from "next/link";
import Image from "next/image";
import Icon from "@/app/lib/component/Icon";
import { PAGE_CONFIG } from "@/app/initData";
import { normalizePageConfig } from "@/app/lib/runtime/pageData";
import LANG_KO from "@/app/lang.ko";

/**
 * @description 루트 랜딩 페이지를 렌더링. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const HomeView = () => {

  /* 1. 상수 ======================================================================================================================= */
  const landingHeroObj = {
    title: LANG_KO.initData.hero.title,
    subtitle: LANG_KO.initData.hero.subtitle,
    primaryCta: { href: "/sample", label: LANG_KO.initData.hero.primaryCtaLabel },
    secondaryCta: { href: "/component", label: LANG_KO.initData.hero.secondaryCtaLabel },
    previewImage: {
      src: "/images/landing/demo-dashboard.png",
      alt: LANG_KO.initData.hero.previewImageAlt,
    },
  };
  const landingServiceList = LANG_KO.initData.services;
  const landingGalleryList = LANG_KO.initData.gallery;
  const landingStackList = LANG_KO.initData.stackList;
  const landingBottomCtaObj = {
    title: LANG_KO.initData.bottomCta.title,
    subtitle: LANG_KO.initData.bottomCta.subtitle,
    demo: { href: "/sample", label: LANG_KO.initData.bottomCta.label },
  };

  /* 2. 데이터 ======================================================================================================================= */
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

  // 없음

  /* 8. useEffect ================================================================================================================== */

  // 없음

  /* 9. 내부 컴포넌트 ============================================================================================================== */

  // 없음

  /* 10. 렌더링 ==================================================================================================================== */
  return (
    <>
      <section
        className="overflow-hidden rounded-3xl bg-gradient-to-br from-[#1e3a5f] to-[#312e81] px-6 py-10 text-white shadow-xl sm:px-10 sm:py-14"
        data-page-mode={pageMode}
      >
        <div className="grid gap-8 lg:grid-cols-[1.2fr_0.8fr] lg:items-center">
          <div>
            <h1 className="text-3xl font-bold leading-tight sm:text-4xl">
              {landingHeroObj.title}
            </h1>
            <p className="mt-4 text-sm text-white/80 sm:text-base">
              {landingHeroObj.subtitle}
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link
                href={landingHeroObj.primaryCta.href}
                className="inline-flex items-center rounded-md bg-blue-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-400"
              >
                {landingHeroObj.primaryCta.label}
              </Link>
              <Link
                href={landingHeroObj.secondaryCta.href}
                className="inline-flex items-center rounded-md border border-white/50 px-4 py-2 text-sm font-semibold text-white transition hover:bg-white/10"
              >
                {landingHeroObj.secondaryCta.label}
              </Link>
            </div>
          </div>

          <div className="mx-auto w-full max-w-sm rotate-2 rounded-2xl border border-white/20 bg-white/10 p-4 shadow-2xl">
            <div className="rounded-xl bg-white p-4 text-gray-900">
              <p className="text-xs font-semibold text-blue-600">{LANG_KO.view.previewBadge}</p>
              <p className="mt-2 text-sm font-semibold">{LANG_KO.view.previewTitle}</p>
              <div className="relative mt-4 overflow-hidden rounded-lg border border-gray-200">
                <Image
                  src={landingHeroObj.previewImage.src}
                  alt={landingHeroObj.previewImage.alt}
                  width={640}
                  height={360}
                  className="h-auto w-full"
                  priority
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="mt-10">
        <h2 className="text-2xl font-bold text-gray-900">{LANG_KO.view.section.services}</h2>
        <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {landingServiceList.map((serviceItem) => (
            <article
              key={serviceItem.title}
              className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
            >
              <Icon
                icon={serviceItem.icon}
                className="text-xl text-blue-600"
                ariaLabel={serviceItem.title}
                decorative={false}
              />
              <h3 className="mt-3 text-base font-semibold text-gray-900">
                {serviceItem.title}
              </h3>
              <p className="mt-2 text-sm leading-6 text-gray-600">
                {serviceItem.description}
              </p>
            </article>
          ))}
        </div>
      </section>

      <section className="mt-10">
        <h2 className="text-2xl font-bold text-gray-900">{LANG_KO.view.section.gallery}</h2>
        <div className="mt-5 grid gap-4 md:grid-cols-3">
          {landingGalleryList.map((galleryItem) => (
            <Link
              key={galleryItem.href}
              href={galleryItem.href}
              className="group overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm transition hover:shadow-md"
            >
              <div className="relative h-40 overflow-hidden bg-gradient-to-br from-blue-50 to-indigo-50">
                <Image
                  src={galleryItem.imageSrc}
                  alt={galleryItem.imageAlt}
                  fill
                  className="object-cover transition duration-300 group-hover:scale-105"
                  sizes="(min-width: 768px) 33vw, 100vw"
                />
              </div>
              <div className="p-4">
                <h3 className="text-base font-semibold text-gray-900 group-hover:text-blue-600">
                  {galleryItem.title}
                </h3>
                <p className="mt-2 text-sm text-gray-600">{galleryItem.description}</p>
              </div>
            </Link>
          ))}
        </div>
      </section>

      <section className="mt-10">
        <h2 className="text-2xl font-bold text-gray-900">{LANG_KO.view.section.stack}</h2>
        <div className="mt-5 flex flex-wrap gap-2">
          {landingStackList.map((stackName) => (
            <span
              key={stackName}
              className="rounded-full bg-blue-50 px-3 py-1.5 text-sm text-blue-700 transition hover:-translate-y-0.5"
            >
              {stackName}
            </span>
          ))}
        </div>
      </section>

      <section className="mt-10 rounded-2xl bg-blue-50 px-6 py-8">
        <h2 className="text-2xl font-bold text-gray-900">{landingBottomCtaObj.title}</h2>
        <p className="mt-2 text-sm text-gray-600">{landingBottomCtaObj.subtitle}</p>
        <div className="mt-5 flex flex-wrap gap-3">
          <Link
            href={landingBottomCtaObj.demo.href}
            className="inline-flex items-center rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700"
          >
            {landingBottomCtaObj.demo.label}
          </Link>
        </div>
      </section>
    </>
  );
};

export default HomeView;
