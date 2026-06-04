/**
 * 파일명: common/layout/Footer.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 대시보드 공용 푸터(EasyObj/EasyList 기반)
 */

import Link from "next/link";
import { getBoundValue } from "@/app/lib/binding";
import { COMMON_COMPONENT_LANG_KO } from "@/app/common/i18n/lang.ko";
import { readFooterLinkList } from "@/app/common/layout/layoutListReader";

/**
 * @description 레이아웃 하단 공용 푸터(EasyObj/EasyList 전용)
 * @param {Object} props
 * @param {Object} [props.textObj] EasyObj에서 텍스트를 읽을 객체
 * @param {string} [props.textKey] EasyObj 텍스트 키
 * @param {Array|Object} [props.linkList] EasyList 또는 배열 { linkId, linkNm, href, active }
 * @param {React.ReactNode} [props.logo] 좌측 로고/텍스트 영역
 * @param {string} [props.className] 추가 클래스
 * 처리 규칙: 입력값과 상태를 검증해 UI/데이터 흐름을 안전하게 유지한다.
 */
const Footer = ({
  textObj,
  textKey = "footerText",
  linkList,
  logo,
  className = "",
}) => {

  const currentYear = new Date().getFullYear();
  const defaultText = COMMON_COMPONENT_LANG_KO.footer.defaultTextTemplate.replace(
    "{year}",
    String(currentYear),
  );
  const resolvedText =
    (textObj && textKey ? getBoundValue(textObj, textKey) : null) ??
    defaultText;

  const resolvedLinks = readFooterLinkList(linkList).map((footerLinkObj) => ({
    key: footerLinkObj.linkId ?? footerLinkObj.id ?? footerLinkObj.href ?? footerLinkObj.linkNm ?? footerLinkObj.label,
    label:
      footerLinkObj.linkNm ??
      footerLinkObj.label ??
      footerLinkObj.text ??
      COMMON_COMPONENT_LANG_KO.footer.defaultLinkLabel,
    href: footerLinkObj.href,
    active: Boolean(footerLinkObj.active),
  }));

  return (
    <footer
      className={`border-t border-gray-200 bg-white px-6 py-4 text-sm text-gray-600 ${className}`.trim()}
      role="contentinfo"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          {logo ? <div className="shrink-0">{logo}</div> : null}
          <span>{resolvedText}</span>
        </div>
        {resolvedLinks.length > 0 ? (
          <div className="flex flex-wrap gap-3">
            {resolvedLinks.map((footerLinkObj) => {
              const footerLinkKey = footerLinkObj.key || footerLinkObj.href || footerLinkObj.label;
              if (footerLinkObj.href) {
                return (
                  <Link
                    key={footerLinkKey}
                    href={footerLinkObj.href}
                    className={`hover:text-gray-900 ${footerLinkObj.active ? "font-semibold text-gray-900" : ""}`.trim()}
                  >
                    {footerLinkObj.label}
                  </Link>
                );
              }
              return (
                <span key={footerLinkKey} className="text-gray-500">
                  {footerLinkObj.label}
                </span>
              );
            })}
          </div>
        ) : null}
      </div>
    </footer>
  );
};

export default Footer;
