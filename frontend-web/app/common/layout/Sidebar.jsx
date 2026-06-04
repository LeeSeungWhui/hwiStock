"use client";

/**
 * 파일명: common/layout/Sidebar.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 햄버거/화살표 토글이 가능한 공용 사이드바(EasyList 기반)
 */

import { useCallback, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import Icon from "@/app/lib/component/Icon";
import { getBoundValue, setBoundValue } from "@/app/lib/binding";
import EasyObj from "@/app/lib/dataset/EasyObj";
import { COMMON_COMPONENT_LANG_KO } from "@/app/common/i18n/lang.ko";
import { readMenuList, readSubMenuList } from "@/app/common/layout/layoutListReader";

/**
 * @description 햄버거/접힘/하위 메뉴 토글을 지원하는 공용 사이드바 컴포넌트.
 * 처리 규칙: 메뉴 활성 상태, 접힘 상태, 그룹 펼침 상태를 통합 관리해 데스크톱/모바일 UI를 동기화한다.
 * @param {Object} props
 * @param {Array|Object} [props.menuList] EasyList 또는 배열 { menuId, menuNm, href?, active?, icon?, badge? }
 * @param {Array|Object} [props.subMenuList] EasyList 또는 배열 { menuId, subMenuId, subMenuNm, href?, active?, icon?, badge? }
 * @param {boolean} [props.isOpen=true] 모바일/데스크톱 전체 표시 여부
 * @param {Function} [props.onClose] 사이드바 닫기 핸들러
 * @param {React.ReactNode} [props.logo] 로고 슬롯
 * @param {React.ReactNode} [props.footerSlot] 하단 푸터 슬롯
 * @param {string} [props.className] 추가 클래스
 * @param {Object} [props.dataObj] EasyObj 바인딩 객체(접힘 상태 저장용)
 * @param {string} [props.collapsedKey=sidebarCollapsed] EasyObj에 저장할 필드명
 */
const Sidebar = ({
  menuList,
  subMenuList,
  isOpen = true,
  onClose,
  logo,
  footerSlot,
  className = "",
  dataObj,
  collapsedKey = "sidebarCollapsed",
}) => {
  const initialCollapsed =
    dataObj && collapsedKey ? Boolean(getBoundValue(dataObj, collapsedKey)) : false;
  const ui = EasyObj({
    collapsed: initialCollapsed,
    expanded: {},
  });
  const pathname = usePathname();

  const resolvedItems = readMenuList(menuList).map((menuItemObj) => ({
    key: menuItemObj.menuId ?? menuItemObj.key ?? menuItemObj.id ?? menuItemObj.menuNm,
    label: menuItemObj.menuNm ?? menuItemObj.label ?? COMMON_COMPONENT_LANG_KO.sidebar.defaultMenuLabel,
    href: menuItemObj.href,
    active: Boolean(menuItemObj.active),
    icon: menuItemObj.icon,
    badge: menuItemObj.badge ?? menuItemObj.count,
    description: menuItemObj.description,
  }));

  const subMenuMap = readSubMenuList(subMenuList).reduce((subMenuMapObj, subMenuItem) => {
    const menuId = subMenuItem.menuId ?? subMenuItem.parentMenuId;
    if (!menuId) return subMenuMapObj;
    const subMenuItemList = subMenuMapObj.get(menuId) || [];
    subMenuItemList.push({
      key: subMenuItem.subMenuId ?? subMenuItem.subMenuNm ?? subMenuItem.menuId,
      label: subMenuItem.subMenuNm ?? subMenuItem.label ?? COMMON_COMPONENT_LANG_KO.sidebar.defaultSubMenuLabel,
      href: subMenuItem.href,
      active: Boolean(subMenuItem.active),
      icon: subMenuItem.icon,
      badge: subMenuItem.badge ?? subMenuItem.count,
      description: subMenuItem.description,
    });
    subMenuMapObj.set(menuId, subMenuItemList);
    return subMenuMapObj;
  }, new Map());

  const hasExplicitActive =
    resolvedItems.some((menuItemObj) => Boolean(menuItemObj.active)) ||
    Array.from(subMenuMap.values()).some((childMenuList) =>
      childMenuList.some((child) => Boolean(child.active)),
    );

  /**
   * @description dataObj collapsedKey 바인딩 값을 ui.collapsed에 동기화
   * 처리 규칙: dataObj/collapsedKey 변경마다 getBoundValue 결과를 ui.collapsed에 반영한다.
   */
  useEffect(() => {
    if (!dataObj || !collapsedKey) return;
    ui.collapsed = Boolean(getBoundValue(dataObj, collapsedKey));
  }, [dataObj, collapsedKey, ui]);

  /**
   * @description 사이드바 접힘 상태를 토글
   * 처리 규칙: ui.collapsed를 반전하고 dataObj 바인딩이 있으면 동일 값을 저장한다.
   * @updated 2026-02-27
   */
  const toggleCollapsed = () => {
    const nextCollapsed = !ui.collapsed;
    ui.collapsed = nextCollapsed;
    if (dataObj && collapsedKey) setBoundValue(dataObj, collapsedKey, nextCollapsed);
  };

  /**
   * @description 하위 메뉴 그룹의 펼침 상태를 토글
   * 처리 규칙: `ui.expanded[key]` 값을 반전해 그룹별 open/close를 제어한다.
   * @updated 2026-02-27
   */
  const toggleGroup = (key) => {
    ui.expanded = { ...ui.expanded, [key]: !ui.expanded[key] };
  };

  /**
   * @description href가 현재 pathname과 활성 매칭되는지 판정
   * 처리 규칙: 완전 일치 또는 하위 경로(prefix/) 일치를 활성으로 처리한다.
   * @updated 2026-02-27
   */
  const isPathActive = useCallback((href) => {
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
  }, [pathname]);

  /**
   * @description 하위 메뉴 항목 활성 여부를 판정하는 내부 규칙 함수.
   * 처리 규칙: child.active 우선, 명시 active가 없을 때만 pathname 매칭으로 활성 여부를 추론한다.
   * @updated 2026-02-27
   */
  const isChildActive = useCallback((child) => {
    if (child.active) {
      return true;
    }
    if (hasExplicitActive) {
      return false;
    }
    return isPathActive(child.href);
  }, [hasExplicitActive, isPathActive]);

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
   * @description 활성 하위 메뉴가 있으면 해당 그룹 ui.expanded를 자동으로 펼침
   * 처리 규칙: pathname/resolvedItems 변경 시 활성 child가 있는 menuKey만 true로 설정한다.
  */
  useEffect(() => {
    const nextExpandedObj = { ...ui.expanded };
    let hasChanged = false;
    resolvedItems.forEach((menuItemObj) => {
      const menuKey = menuItemObj.key || menuItemObj.label || menuItemObj.href;
      const childMenuList = subMenuMap.get(menuItemObj.key) || [];
      if (childMenuList.some((child) => isChildActive(child))) {
        if (!nextExpandedObj[menuKey]) {
          nextExpandedObj[menuKey] = true;
          hasChanged = true;
        }
      }
    });
    if (hasChanged) {
      ui.expanded = nextExpandedObj;
    }
  }, [resolvedItems, pathname, subMenuMap, ui, isChildActive]);

  const sidebarContent = (
    <>
      {logo ? (
        <div className="px-4 py-3">
          <div
            className={`${ui.collapsed ? "sr-only" : ""} text-sm font-semibold text-gray-900`}
          >
            {logo}
          </div>
        </div>
      ) : null}

      <button
        type="button"
        onClick={toggleCollapsed}
        aria-label={
          ui.collapsed
            ? COMMON_COMPONENT_LANG_KO.sidebar.expandAriaLabel
            : COMMON_COMPONENT_LANG_KO.sidebar.collapseAriaLabel
        }
        className="absolute -right-3 top-1/2 -translate-y-1/2 hidden h-8 w-8 items-center justify-center rounded-full border border-gray-200 bg-white text-gray-600 shadow-sm hover:bg-gray-50 lg:flex"
      >
        <Icon
          icon={ui.collapsed ? "ri:RiArrowRightSLine" : "ri:RiArrowLeftSLine"}
          size="1.2em"
        />
      </button>

      <button
        type="button"
        onClick={onClose}
        aria-label={COMMON_COMPONENT_LANG_KO.sidebar.closeAriaLabel}
        className="absolute right-2 top-2 rounded-md p-2 text-gray-500 hover:bg-gray-100 lg:hidden"
      >
        <Icon icon="ri:RiCloseLine" size="1.1em" />
      </button>

      <nav
        className="flex-1 overflow-y-auto px-3 py-4"
        aria-label={COMMON_COMPONENT_LANG_KO.sidebar.menuAriaLabel}
      >
        <ul className="space-y-1">
          {resolvedItems.map((menuItemObj) => {
            const menuKey = menuItemObj.key || menuItemObj.label || menuItemObj.href;
            const childMenuList = subMenuMap.get(menuItemObj.key) || [];
            const isActive = isItemActive(menuItemObj, childMenuList);
            const hasChildren = childMenuList.length > 0;
            const isOpenGroup = ui.expanded[menuKey] || false;
            const childListClassName = isOpenGroup ? "mt-1 space-y-1" : "hidden";
            const childListPaddingClassName = ui.collapsed ? "" : "pl-3";
            const navItemClassName = [
              "group flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
              isActive
                ? "bg-blue-50 text-blue-700 font-semibold ring-1 ring-blue-100"
                : "text-gray-700 hover:bg-gray-50",
            ].join(" ");

            const menuContent = (
              <div className="flex w-full items-center gap-3">
                {menuItemObj.icon ? (
                  <Icon icon={menuItemObj.icon} size="1.1em" ariaLabel={menuItemObj.label} />
                ) : null}
                <span className={`${ui.collapsed ? "sr-only" : "truncate"}`}>
                  {menuItemObj.label}
                </span>
                {menuItemObj.badge && !ui.collapsed ? (
                  <span className="ml-auto rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-700">
                    {menuItemObj.badge}
                  </span>
                ) : null}
                {hasChildren ? (
                  <Icon
                    icon={
                      isOpenGroup ? "ri:RiArrowUpSLine" : "ri:RiArrowDownSLine"
                    }
                    size="1em"
                    className={`ml-auto text-gray-500 ${ui.collapsed ? "hidden" : ""}`}
                  />
                ) : null}
              </div>
            );

            let menuActionNode = null;
            if (hasChildren) {
              menuActionNode = (
                <>
                  <button
                    type="button"
                    className={navItemClassName}
                    onClick={() => toggleGroup(menuKey)}
                    aria-expanded={isOpenGroup ? "true" : "false"}
                    aria-controls={`${menuKey}-children-${ui.collapsed ? "mini" : "full"}`}
                    title={menuItemObj.label}
                  >
                    {menuContent}
                  </button>
                  <ul
                    id={`${menuKey}-children-${ui.collapsed ? "mini" : "full"}`}
                    className={`${childListClassName} ${childListPaddingClassName}`}
                    aria-label={`${menuItemObj.label} ${COMMON_COMPONENT_LANG_KO.sidebar.subMenuAriaSuffix}`}
                  >
                    {childMenuList.map((child) => {
                      const childKey = child.key || child.label || child.href;
                      const isChildMenuActive = isChildActive(child);
                      const childClassName = [
                        "group flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                        isChildMenuActive
                          ? "bg-blue-50 text-blue-700 font-semibold ring-1 ring-blue-100"
                          : "text-gray-700 hover:bg-gray-50",
                      ].join(" ");
                      const subMenuContent = (
                        <div className="flex w-full items-center gap-3 pl-2">
                          {child.icon ? (
                            <Icon
                              icon={child.icon}
                              size="1.05em"
                              ariaLabel={child.label}
                            />
                          ) : (
                            <span
                              className="h-1.5 w-1.5 rounded-full bg-gray-300"
                              aria-hidden
                            />
                          )}
                          <span
                            className={`${ui.collapsed ? "sr-only" : "truncate"}`}
                          >
                            {child.label}
                          </span>
                          {child.badge && !ui.collapsed ? (
                            <span className="ml-auto rounded-full bg-gray-50 px-2 py-0.5 text-xs text-gray-600">
                              {child.badge}
                            </span>
                          ) : null}
                        </div>
                      );
                      if (child.href) {
                        return (
                          <li key={childKey}>
                            <Link
                              href={child.href}
                              className={childClassName}
                              aria-current={isChildMenuActive ? "page" : undefined}
                              title={child.label}
                            >
                              {subMenuContent}
                            </Link>
                          </li>
                        );
                      }
                      return (
                        <li key={childKey}>
                          <button
                            type="button"
                            className={childClassName}
                            onClick={child.onClick}
                            title={child.label}
                          >
                            {subMenuContent}
                          </button>
                        </li>
                      );
                    })}
                  </ul>
                </>
              );
            } else if (menuItemObj.href) {
              menuActionNode = (
                <Link
                  href={menuItemObj.href}
                  className={navItemClassName}
                  aria-current={isActive ? "page" : undefined}
                  title={menuItemObj.label}
                >
                  {menuContent}
                </Link>
              );
            } else {
              menuActionNode = (
                <button
                  type="button"
                  onClick={menuItemObj.onClick}
                  className={navItemClassName}
                  title={menuItemObj.label}
                >
                  {menuContent}
                </button>
              );
            }

            return (
              <li key={menuKey}>
                {menuActionNode}
              </li>
            );
          })}

        </ul>
      </nav>
      {footerSlot ? (
        <div className="border-t border-gray-100 p-3 text-xs text-gray-500">
          {footerSlot}
        </div>
      ) : null}
    </>
  );

  const sideWidthClassName = ui.collapsed ? "w-16" : "w-64";
  const sideShiftClassName = isOpen
    ? "translate-x-0"
    : "-translate-x-full pointer-events-none lg:pointer-events-auto lg:translate-x-0";

  return (
    <>
      <div
        className={`fixed inset-0 z-30 bg-gray-900/30 lg:hidden ${isOpen ? "" : "hidden"}`}
        onClick={onClose}
        aria-hidden="true"
      />
      <aside
        className={`fixed bottom-0 left-0 top-16 z-40 flex h-auto flex-none flex-col overflow-visible border-r border-gray-200 bg-white shadow-sm transition-all duration-200 lg:static lg:top-auto lg:bottom-auto lg:left-auto lg:min-h-full ${sideWidthClassName} ${sideShiftClassName} ${className}`.trim()}
        aria-label={COMMON_COMPONENT_LANG_KO.sidebar.navigationAriaLabel}
      >
        {sidebarContent}
      </aside>
    </>
  );
};

/**
 * @description Sidebar 컴포넌트 엔트리를 외부에 노출
 * 처리 규칙: 상태 로직이 연결된 Sidebar 컴포넌트를 default export 한다.
 */
export default Sidebar;
