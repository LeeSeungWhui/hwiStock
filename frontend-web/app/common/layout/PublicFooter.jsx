/**
 * 파일명: common/layout/PublicFooter.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 공개 페이지 공통 푸터
 */

import Link from "next/link";
import { COMMON_COMPONENT_LANG_KO } from "@/app/common/i18n/lang.ko";

/**
 * @description 공개 페이지 공통 푸터를 렌더링. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const PublicFooter = () => {
  const currentYear = new Date().getFullYear();
  const copyrightText =
    COMMON_COMPONENT_LANG_KO.publicLayout.copyrightTemplate.replace(
      "{year}",
      String(currentYear),
    );

  return (
    <footer className="mt-16 border-t border-white/10 bg-gray-900">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-4 px-4 py-8 text-sm text-gray-300 sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
        <p className="font-medium text-gray-100">{COMMON_COMPONENT_LANG_KO.publicLayout.brandLabel}</p>
        <p className="text-xs text-gray-400">
          {copyrightText}
        </p>
        <div className="flex flex-wrap items-center gap-3">
          {COMMON_COMPONENT_LANG_KO.publicLayout.footerLinkList.map((menuItemObj) => {
            if (menuItemObj.external) {
              return (
                <a
                  key={menuItemObj.href}
                  href={menuItemObj.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-gray-300 transition hover:text-white"
                >
                  {menuItemObj.label}
                </a>
              );
            }
            return (
              <Link
                key={menuItemObj.href}
                href={menuItemObj.href}
                className="text-gray-300 transition hover:text-white"
              >
                {menuItemObj.label}
              </Link>
            );
          })}
        </div>
      </div>
    </footer>
  );
};

export default PublicFooter;
