"use client";

/**
 * 파일명: common/layout/Header.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 대시보드용 상단 헤더 내비게이션 (EasyObj/EasyList 기반)
 */

import { useEffect, useRef } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import Button from "@/app/lib/component/Button";
import Icon from "@/app/lib/component/Icon";
import EasyObj from "@/app/lib/dataset/EasyObj";
import { COMMON_COMPONENT_LANG_KO } from "@/app/common/i18n/lang.ko";
import { readMenuList, readSubMenuList } from "@/app/common/layout/layoutListReader";

/**
 * @description 햄버거/메뉴/텍스트 영역을 포함한 대시보드 상단 헤더 컴포넌트(EasyList 기반).
 * 처리 규칙: 메뉴 활성/서브메뉴 펼침/외부 클릭 닫기 상태를 통합 관리한다.
 * @param {Object} props
 * @param {string} props.title 헤더 타이틀
 * @param {string} [props.subtitle] 타이틀 보조 설명
 * @param {Array|Object} [props.menuList] EasyList 또는 배열 { menuId, menuNm, href?, active?, icon? }
 * @param {Array|Object} [props.subMenuList] EasyList 또는 배열 { menuId, subMenuId, subMenuNm, href?, active? }
 * @param {Function} [props.onToggleSidebar] 사이드바 토글 핸들러(있으면 햄버거 표시)
 * @param {React.ReactNode} [props.logo] 로고 슬롯(img, span 등)
 * @param {React.ReactNode} [props.actions] 우측 액션 영역
 * @param {React.ReactNode} [props.text] 우측 표시 텍스트/커스텀 슬롯 영역(사용자명 등)
 * @param {string} [props.className] 추가 클래스
 */
const Header = ({
  title = COMMON_COMPONENT_LANG_KO.header.defaultTitle,
  subtitle,
  menuList,
  subMenuList,
  onToggleSidebar,
  actions,
  logo,
  text,
  children,
  className = "",
}) => {

  const ui = EasyObj({ openMenu: null });
  const navRef = useRef(null);
  const pathname = usePathname();
  const resolvedMenus = readMenuList(menuList).map((menuItemObj) => ({
    key: menuItemObj.menuId ?? menuItemObj.key ?? menuItemObj.id ?? menuItemObj.menuNm,
    label:
      menuItemObj.menuNm ??
      menuItemObj.label ??
      menuItemObj.title ??
      COMMON_COMPONENT_LANG_KO.header.defaultMenuLabel,
    href: menuItemObj.href,
    active: Boolean(menuItemObj.active),
    icon: menuItemObj.icon,
  }));

  const subMenuMap = readSubMenuList(subMenuList).reduce((subMenuMapObj, subMenuItem) => {
    const menuId = subMenuItem.menuId ?? subMenuItem.parentMenuId;
    if (!menuId) return subMenuMapObj;
    const subMenuItemList = subMenuMapObj.get(menuId) || [];
    subMenuItemList.push({
      key: subMenuItem.subMenuId ?? subMenuItem.subMenuNm ?? subMenuItem.subMenuCode ?? subMenuItem.menuId,
      label:
        subMenuItem.subMenuNm ??
        subMenuItem.label ??
        subMenuItem.title ??
        COMMON_COMPONENT_LANG_KO.header.defaultSubMenuLabel,
      href: subMenuItem.href,
      active: Boolean(subMenuItem.active),
      icon: subMenuItem.icon,
    });
    subMenuMapObj.set(menuId, subMenuItemList);
    return subMenuMapObj;
  }, new Map());

  const hasExplicitActive =
    resolvedMenus.some((menuItemObj) => Boolean(menuItemObj.active)) ||
    Array.from(subMenuMap.values()).some((childMenuList) =>
      childMenuList.some((child) => Boolean(child.active)),
    );

  /**
   * @description document pointerdown으로 nav 바깥 클릭 시 열린 메뉴 닫기
   * 처리 규칙: cleanup에서 pointerdown 리스너를 제거하고 ui.openMenu=null을 반영한다.
   */
  useEffect(() => {

    /**
     * @description 네비게이션 바깥 영역 클릭 시 열린 메뉴 닫기.
     * 처리 규칙: pointerdown 이벤트 target이 navRef 외부면 `ui.openMenu`를 null로 초기화한다.
     * @updated 2026-02-27
     */
    const handleNavPointerDown = (event) => {
      if (navRef.current && !navRef.current.contains(event.target)) {
        ui.openMenu = null;
      }
    };

    document.addEventListener("pointerdown", handleNavPointerDown);
    return () => document.removeEventListener("pointerdown", handleNavPointerDown);
  }, [ui]);

  /**
   * @description href가 현재 pathname과 활성 매칭되는지 판정
   * 처리 규칙: 완전 일치 또는 하위 경로(prefix/) 일치를 활성으로 처리한다.
   * @updated 2026-02-27
   */
  const isPathActive = (href) => {
    if (!href || !pathname) {
      return false;
    }
    if (pathname === href) {
      return true;
    }
    if (pathname.startsWith(`${href}/`)) {
      return true;
    }
    return false;
  };

  /**
   * @description 하위 메뉴 항목 활성 여부를 판정하는 내부 규칙 함수.
   * 처리 규칙: child.active 우선, 명시 active가 없을 때만 pathname 매칭으로 활성 여부를 추론한다.
   * @updated 2026-02-27
   */
  const isChildActive = (child) => {
    if (child.active) {
      return true;
    }
    if (hasExplicitActive) {
      return false;
    }
    return isPathActive(child.href);
  };

  /**
   * @description 상위 메뉴 항목 활성 여부를 계산하는 내부 규칙 함수.
   * 처리 규칙: menuItemObj.active 우선, child 활성 여부를 반영하고 명시 active가 없을 때만 경로 매칭을 사용한다.
   * @updated 2026-02-27
   */
  const isItemActive = (menuItemObj, childMenuList = []) => {
    if (menuItemObj.active) {
      return true;
    }
    if (childMenuList.some((child) => isChildActive(child))) {
      return true;
    }
    if (hasExplicitActive) {
      return false;
    }
    return isPathActive(menuItemObj.href);
  };

  /**
   * @description 서브메뉴 선택 이벤트를 반영
   * 처리 규칙: menuItemObj.onClick이 있으면 호출하고 선택 후 openMenu를 닫는다.
   * @updated 2026-02-27
   */
  const handleMenuSelect = (menuItemObj) => {
    if (typeof menuItemObj.onClick === "function") menuItemObj.onClick();
    ui.openMenu = null;
  };

  return (
    <header
      className={`border-b border-gray-200 bg-white shadow-sm ${className}`.trim()}

    >
      <div className="flex min-h-16 items-center justify-between gap-2 px-3 sm:gap-3 sm:px-4">
        <div className="flex min-w-0 items-center gap-2 sm:gap-3">
          {typeof onToggleSidebar === "function" ? (
            <Button
              variant="ghost"
              size="sm"
              aria-label={COMMON_COMPONENT_LANG_KO.header.toggleSidebarAriaLabel}
              onClick={onToggleSidebar}
              className="px-2 py-1 text-gray-700"
            >
              <Icon icon="ri:RiMenuLine" size="1.25em" />
            </Button>
          ) : null}
          {logo ? <div className="flex shrink-0 items-center">{logo}</div> : null}
          <div className="min-w-0 leading-tight">
            <div className="truncate text-sm font-semibold text-gray-900 sm:text-base">
              {title}
            </div>
            {subtitle && (
              <div className="hidden truncate text-xs text-gray-500 sm:block">
                {subtitle}
              </div>
            )}
          </div>
        </div>
        <nav
          ref={navRef}
          className="hidden items-center gap-2 md:flex"
          aria-label={COMMON_COMPONENT_LANG_KO.header.primaryMenuAriaLabel}
        >
          {resolvedMenus.map((menuItemObj) => {
            const childMenuList = subMenuMap.get(menuItemObj.key) || [];
            const menuKey = menuItemObj.key || menuItemObj.label || menuItemObj.href;
            const isActive = isItemActive(menuItemObj, childMenuList);
            const hasChildren = childMenuList.length > 0;
            const menuButtonClassName = [
              "inline-flex items-center gap-2 rounded-md border border-transparent px-3 py-2 text-sm font-medium transition-colors",
              isActive
                ? "bg-blue-50 text-blue-700 ring-1 ring-blue-100"
                : "text-gray-700 hover:bg-gray-100",
            ].join(" ");
            if (hasChildren) {
              const isOpen = ui.openMenu === menuKey;
              return (
                <div key={menuKey} className="relative">
                  <Button
                    variant="ghost"
                    size="sm"
                    aria-haspopup="menu"
                    aria-expanded={isOpen ? "true" : "false"}
                    onClick={() => {
                      ui.openMenu = isOpen ? null : menuKey;
                    }}
                    className={menuButtonClassName}
                  >
                    <span>{menuItemObj.label}</span>
                    <Icon icon="ri:RiArrowDownSLine" size="1.1em" />
                  </Button>
                  <div
                    className={`absolute right-0 top-full mt-2 w-56 rounded-lg border border-gray-200 bg-white shadow-md ${
                      isOpen ? "block" : "hidden"
                    }`}
                    role="menu"
                    aria-label={`${menuItemObj.label} ${COMMON_COMPONENT_LANG_KO.header.subMenuAriaSuffix}`}
                  >
                    <ul className="py-1">
                      {childMenuList.map((child) => {
                        const childKey = child.key || child.label || child.href;
                        const isChildMenuActive = isChildActive(child);
                        const linkClassName = [
                          "flex w-full items-start gap-2 px-3 py-2 text-sm transition-colors",
                          isChildMenuActive
                            ? "bg-blue-50 text-blue-700"
                            : "text-gray-700 hover:bg-gray-50",
                        ].join(" ");
                        return (
                          <li key={childKey}>
                            {child.href ? (
                              <Link
                                href={child.href}
                                onClick={() => handleMenuSelect(child)}
                                className={linkClassName}
                                role="menuitem"
                                aria-current={isChildMenuActive ? "page" : undefined}
                              >
                                <span
                                  className={`font-medium ${isChildMenuActive ? "text-blue-700" : "text-gray-900"}`}
                                >
                                  {child.label}
                                </span>
                                {child.description && (
                                  <span
                                    className={`text-xs ${isChildMenuActive ? "text-blue-700" : "text-gray-500"}`}
                                  >
                                    {child.description}
                                  </span>
                                )}
                              </Link>
                            ) : (
                              <button
                                type="button"
                                onClick={() => handleMenuSelect(child)}
                                className={linkClassName}
                                role="menuitem"
                                aria-current={isChildMenuActive ? "page" : undefined}
                              >
                                <span
                                  className={`font-medium ${isChildMenuActive ? "text-blue-700" : "text-gray-900"}`}
                                >
                                  {child.label}
                                </span>
                                {child.description && (
                                  <span
                                    className={`text-xs ${isChildMenuActive ? "text-blue-700" : "text-gray-500"}`}
                                  >
                                    {child.description}
                                  </span>
                                )}
                              </button>
                            )}
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                </div>
              );
            }
            if (menuItemObj.href) {
              return (
                <Link
                  key={menuKey}
                  href={menuItemObj.href}
                  className={menuButtonClassName}
                  aria-current={isActive ? "page" : undefined}
                >
                  {menuItemObj.label}
                </Link>
              );
            }
            return (
              <button
                key={menuKey}
                type="button"
                onClick={() => handleMenuSelect(menuItemObj)}
                className={menuButtonClassName}
              >
                {menuItemObj.label}
              </button>
            );
          })}

        </nav>
        <div className="flex shrink-0 items-center gap-1.5 sm:gap-2">
          {actions}
          {text ? (
            <div className="hidden max-w-[256px] items-center gap-2 truncate text-sm text-gray-700 sm:flex">
              {text}
            </div>
          ) : null}
          {children}
        </div>
      </div>
    </header>
  );
};

/**
 * @description Header 컴포넌트 엔트리를 외부에 노출
 * 처리 규칙: 상태 로직이 결합된 Header 컴포넌트를 default export 한다.
 */
export default Header;
