"use client";

/**
 * 파일명: common/layout/PublicGnb.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 공개 페이지 공통 GNB(샘플 드롭다운/모바일 드로어 포함)
 */

import { useEffect, useRef } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import Icon from "@/app/lib/component/Icon";
import EasyObj from "@/app/lib/dataset/EasyObj";
import { COMMON_COMPONENT_LANG_KO } from "@/app/common/i18n/lang.ko";

/**
 * @description 공개 페이지에서 사용하는 상단 GNB를 렌더링. 입력/출력 계약을 함께 명시
 * 처리 규칙: 데스크톱은 hover+pin 드롭다운, 모바일은 토글 드로어 메뉴 구조를 사용한다.
 */
const PublicGnb = () => {
  const pathname = usePathname() || "/";
  const ui = EasyObj({
    mobileOpen: false,
    demoMenuOpen: false,
    demoMenuPinned: false,
  });
  const demoMenuRef = useRef(null);

  const demoPathText = String(pathname || "");
  const isDemoActive =
    demoPathText === "/sample" ||
    (
      demoPathText.startsWith("/sample/") &&
      !demoPathText.startsWith("/sample/portfolio")
    );

  /**
   * @description 데모 메뉴 버튼 클릭 시 pinned/open 상태를 토글
   * 처리 규칙: 이미 pin된 상태에서 재클릭하면 닫고, 그 외에는 pin=true/open=true로 유지한다.
   * @updated 2026-02-27
   */
  const handleToggleDemoMenu = () => {
    if (ui.demoMenuOpen && ui.demoMenuPinned) {
      ui.demoMenuPinned = false;
      ui.demoMenuOpen = false;
      return;
    }
    ui.demoMenuPinned = true;
    ui.demoMenuOpen = true;
  };

  /**
   * @description document pointerdown/keydown으로 데모 드롭다운 닫기 처리
   * 처리 규칙: cleanup에서 outside-click·Escape 리스너를 제거한다.
   */
  useEffect(() => {

    /**
     * @description 데모 메뉴 영역 바깥 포인터 입력에서 드롭다운 닫기
     * 처리 규칙: demoMenuRef 외부 pointerdown 이벤트만 close 대상으로 본다.
     * @updated 2026-02-27
     */
    const handleDocPointerDown = (event) => {
      if (!demoMenuRef.current || demoMenuRef.current.contains(event.target)) {
        return;
      }
      ui.demoMenuPinned = false;
      ui.demoMenuOpen = false;
    };

    /**
     * @description Escape 키 입력으로 데모 드롭다운 닫기
     * 처리 규칙: key 값이 Escape일 때 pinned/open 상태를 직접 해제한다.
     * @updated 2026-02-27
     */
    const handleEscape = (event) => {
      if (event.key === "Escape") {
        ui.demoMenuPinned = false;
        ui.demoMenuOpen = false;
      }
    };

    document.addEventListener("pointerdown", handleDocPointerDown);
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("pointerdown", handleDocPointerDown);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [ui]);

  /**
   * @description route 변경 시 데모 드롭다운 pinned/open 상태 초기화
   * 처리 규칙: pathname 변경마다 demoMenuPinned/demoMenuOpen을 false로 설정한다.
   */
  useEffect(() => {
    ui.demoMenuPinned = false;
    ui.demoMenuOpen = false;
  }, [pathname, ui]);

  return (
    <header className="sticky top-0 z-50 border-b border-white/20 bg-white/80 backdrop-blur">
      <div className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <div className="flex min-w-0 items-center gap-2">
          <button
            type="button"
            className="inline-flex h-10 w-10 items-center justify-center rounded-md border border-gray-200 text-gray-700 md:hidden"
            aria-label={COMMON_COMPONENT_LANG_KO.publicLayout.mobileMenuOpenAriaLabel}
            onClick={() => {
              ui.mobileOpen = !ui.mobileOpen;
            }}
          >
            <Icon
              icon={ui.mobileOpen ? "ri:RiCloseLine" : "ri:RiMenuLine"}
              className="text-lg"
            />
          </button>
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-base font-semibold text-gray-900"
          >
            <Icon icon="ri:RiCodeBoxLine" className="text-blue-600" />
            <span>MyWebTemplate</span>
          </Link>
        </div>

        <nav className="hidden items-center gap-6 text-sm font-medium text-gray-700 md:flex">
          <div
            ref={demoMenuRef}
            className="relative"
            onMouseEnter={() => {
              ui.demoMenuOpen = true;
            }}
            onMouseLeave={() => {
              if (!ui.demoMenuPinned) {
                ui.demoMenuOpen = false;
              }
            }}
          >
            <button
              type="button"
              className={`inline-flex items-center gap-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                isDemoActive
                  ? "bg-blue-50 text-blue-700 ring-1 ring-blue-100"
                  : "text-gray-700 hover:bg-gray-100 hover:text-blue-600"
              }`.trim()}
              aria-haspopup="menu"
              aria-expanded={ui.demoMenuOpen}
              onClick={handleToggleDemoMenu}
            >
              {COMMON_COMPONENT_LANG_KO.publicLayout.demoMenuLabel}
              <Icon icon="ri:RiArrowDownSLine" />
            </button>
            <div
              className={`absolute right-0 top-full w-48 rounded-lg border border-gray-200 bg-white p-2 shadow-lg transition ${
                ui.demoMenuOpen
                  ? "visible opacity-100"
                  : "invisible pointer-events-none opacity-0"
              }`}
              role="menu"
              aria-label={COMMON_COMPONENT_LANG_KO.publicLayout.demoMenuAriaLabel}
            >
              {COMMON_COMPONENT_LANG_KO.publicLayout.demoMenuList.map((menuItemObj) => {
                let isMenuActive = false;
                if (menuItemObj.href === "/sample") {
                  isMenuActive = pathname === "/sample";
                } else if (menuItemObj.href === "/") {
                  isMenuActive = pathname === "/";
                } else {
                  isMenuActive = pathname === menuItemObj.href || pathname.startsWith(`${menuItemObj.href}/`);
                }
                return (
                  <Link
                    key={menuItemObj.href}
                    href={menuItemObj.href}
                    className={`block rounded-md px-3 py-2 text-sm transition-colors ${
                      isMenuActive
                        ? "bg-blue-50 text-blue-700"
                        : "text-gray-700 hover:bg-gray-50 hover:text-blue-600"
                    }`.trim()}
                    onClick={() => {
                      ui.demoMenuPinned = false;
                      ui.demoMenuOpen = false;
                    }}
                    aria-current={isMenuActive ? "page" : undefined}
                  >
                    {menuItemObj.label}
                  </Link>
                );
              })}
            </div>
          </div>

          {COMMON_COMPONENT_LANG_KO.publicLayout.publicMenuList.map((menuItemObj) => {
            let isMenuActive = false;
            if (menuItemObj.href === "/sample") {
              isMenuActive = pathname === "/sample";
            } else if (menuItemObj.href === "/") {
              isMenuActive = pathname === "/";
            } else {
              isMenuActive = pathname === menuItemObj.href || pathname.startsWith(`${menuItemObj.href}/`);
            }
            return (
              <Link
                key={menuItemObj.href}
                href={menuItemObj.href}
                className={`inline-flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                  isMenuActive
                    ? "bg-blue-50 text-blue-700 ring-1 ring-blue-100"
                    : "text-gray-700 hover:bg-gray-100 hover:text-blue-600"
                }`.trim()}
                aria-current={isMenuActive ? "page" : undefined}
              >
                {menuItemObj.label}
              </Link>
            );
          })}
        </nav>

      </div>

      {ui.mobileOpen ? (
        <div className="border-t border-gray-200 bg-white px-4 py-4 md:hidden">
          <div className="space-y-1">
            <p className="px-2 py-1 text-xs font-semibold tracking-wide text-gray-500">
              {COMMON_COMPONENT_LANG_KO.publicLayout.demoMenuLabel}
            </p>
            {COMMON_COMPONENT_LANG_KO.publicLayout.demoMenuList.map((menuItemObj) => {
              let isMenuActive = false;
              if (menuItemObj.href === "/sample") {
                isMenuActive = pathname === "/sample";
              } else if (menuItemObj.href === "/") {
                isMenuActive = pathname === "/";
              } else {
                isMenuActive = pathname === menuItemObj.href || pathname.startsWith(`${menuItemObj.href}/`);
              }
              return (
                <Link
                  key={menuItemObj.href}
                  href={menuItemObj.href}
                  className={`block rounded-md px-2 py-2 text-sm ${
                    isMenuActive
                      ? "bg-blue-50 text-blue-700"
                      : "text-gray-700"
                  }`}
                  onClick={() => {
                    ui.mobileOpen = false;
                  }}
                >
                  {menuItemObj.label}
                </Link>
              );
            })}
          </div>

          <div className="mt-3 space-y-1">
            {COMMON_COMPONENT_LANG_KO.publicLayout.publicMenuList.map((menuItemObj) => {
              let isMenuActive = false;
              if (menuItemObj.href === "/sample") {
                isMenuActive = pathname === "/sample";
              } else if (menuItemObj.href === "/") {
                isMenuActive = pathname === "/";
              } else {
                isMenuActive = pathname === menuItemObj.href || pathname.startsWith(`${menuItemObj.href}/`);
              }
              return (
                <Link
                  key={menuItemObj.href}
                  href={menuItemObj.href}
                  className={`block rounded-md px-2 py-2 text-sm ${
                    isMenuActive
                      ? "bg-blue-50 text-blue-700"
                      : "text-gray-700"
                  }`}
                  onClick={() => {
                    ui.mobileOpen = false;
                  }}
                >
                  {menuItemObj.label}
                </Link>
              );
            })}
          </div>
        </div>
      ) : null}
    </header>
  );
};

export default PublicGnb;
