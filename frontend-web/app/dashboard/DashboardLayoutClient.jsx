"use client";

/**
 * 파일명: dashboard/DashboardLayoutClient.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 대시보드 레이아웃 클라이언트 컴포넌트
 */

import { useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import Header from "@/app/common/layout/Header";
import Sidebar from "@/app/common/layout/Sidebar";
import Footer from "@/app/common/layout/Footer";
import Button from "@/app/lib/component/Button";
import Icon from "@/app/lib/component/Icon";
import { apiJSON } from "@/app/lib/runtime/api";
import { useGlobalUi, useUser } from "@/app/common/store/SharedStore";
import { resolveDashboardLayoutMeta } from "./layoutMeta";
import EasyObj from "@/app/lib/dataset/EasyObj";
import LANG_KO from "./lang.ko";

/**
 * @description 대시보드 하위 경로 공통 레이아웃을 렌더링. 입력/출력 계약을 함께 명시
 * 처리 규칙: pathname/searchParams 기반 layoutMeta를 계산해 Header/Sidebar/Footer 공통 셸을 구성한다.
 * @param {{ children: React.ReactNode }} props
 */
const DashboardLayoutClient = ({ children }) => {

  /* 1. 상수 ======================================================================================================================= */

  // 없음

  /* 2. 데이터 ======================================================================================================================= */
  const ui = EasyObj({
    sidebarOpen: false,
    isDesktopViewport: false,
  });
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const searchParamText = searchParams?.toString() || "";
  const { setUser } = useUser();
  const { setLoading, showToast } = useGlobalUi();
  const layoutMeta = resolveDashboardLayoutMeta({
    pathname,
    searchParams,
  });
  const currentYear = new Date().getFullYear();

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
   * @description 로그아웃 API 호출 후 사용자 상태를 비우고 로그인 페이지로 이동
   * 실패 동작: API 실패 시 에러 토스트를 노출하고 로딩 상태를 finally에서 해제한다.
   * @updated 2026-02-27
   */
  const handleLogout = async () => {
    setLoading(true);
    try {
      await apiJSON("/api/v1/auth/logout", { method: "POST" });
      setUser(null);
      showToast(LANG_KO.layoutMeta.layoutAction.logoutSuccessToast, { type: "info" });
      router.push("/login");
    } catch {
      showToast(LANG_KO.layoutMeta.layoutAction.logoutFailToast, { type: "error" });
    } finally {
      setLoading(false);
    }
  };

  /* 8. useEffect ================================================================================================================== */
  /**
   * @description 1024px media query 변경에 맞춰 데스크톱 여부와 sidebarOpen 동기화
   * 처리 규칙: cleanup에서 mediaQuery change 리스너를 제거한다.
   */
  useEffect(() => {
    if (typeof window === "undefined") {
      return undefined;
    }
    const mediaQuery = window.matchMedia("(min-width: 1024px)");

    /**
     * @description 뷰포트 크기에 맞춰 데스크톱 여부와 사이드바 열림 상태를 동기화
     * 처리 규칙: 1024px 이상이면 sidebarOpen=true, 미만이면 false로 맞춘다.
     * @updated 2026-02-27
     */
    const syncViewport = () => {
      ui.isDesktopViewport = mediaQuery.matches;
      ui.sidebarOpen = mediaQuery.matches;
    };

    syncViewport();
    mediaQuery.addEventListener("change", syncViewport);
    return () => mediaQuery.removeEventListener("change", syncViewport);
  }, [ui]);

  /**
   * @description 모바일 뷰포트에서 route 변경 시 사이드바를 닫음
   * 처리 규칙: pathname/searchParams 변경마다 ui.sidebarOpen=false를 반영한다.
   */
  useEffect(() => {
    if (!ui.isDesktopViewport) {
      ui.sidebarOpen = false;
    }
  }, [pathname, searchParamText, ui]);

  /* 9. 내부 컴포넌트 ============================================================================================================== */

  // 없음

  /* 10. 렌더링 ==================================================================================================================== */
  return (
    <div className="flex min-h-screen flex-col bg-gray-50">
      <div className="sticky top-0 z-40">
        <Header
          title={layoutMeta.title}
          subtitle={layoutMeta.subtitle}
          menuList={layoutMeta.menuList}
          subMenuList={layoutMeta.subMenuList}
          onToggleSidebar={() => {
            ui.sidebarOpen = !ui.sidebarOpen;
          }}
          text={layoutMeta.text}
          logo={(
            <Link
              href="/"
              className="inline-flex items-center gap-2 rounded-md border border-blue-100 bg-blue-50 px-2 py-1 text-blue-700 transition hover:bg-blue-100"
            >
              <Icon icon="ri:RiCodeBoxLine" className="text-blue-600" />
              <span className="text-sm font-semibold">{LANG_KO.layoutMeta.brandName}</span>
            </Link>
          )}
        >
          <Button
            size="sm"
            variant="ghost"
            className="px-2 text-gray-600 hover:text-gray-900 sm:px-3"
            onClick={() => {
              router.push("/");
            }}
          >
            <Icon icon="ri:RiHome6Line" className="text-base sm:hidden" />
            <span className="hidden sm:inline">{LANG_KO.layoutMeta.layoutAction.goHome}</span>
          </Button>
          <Button size="sm" variant="secondary" className="px-2 sm:px-3" onClick={handleLogout}>
            {LANG_KO.layoutMeta.layoutAction.logout}
          </Button>
        </Header>
      </div>
      <div className="flex min-h-0 flex-1 items-stretch">
        <Sidebar
          menuList={layoutMeta.menuList}
          subMenuList={layoutMeta.subMenuList}
          isOpen={ui.sidebarOpen}
          onClose={() => {
            ui.sidebarOpen = false;
          }}
          logo={
            <span className="inline-flex items-center rounded-md bg-gradient-to-r from-[#1e3a5f] to-[#312e81] px-2 py-1 text-xs font-semibold text-white">
              {LANG_KO.layoutMeta.brandName}
            </span>
          }
          footerSlot={`© ${currentYear} ${LANG_KO.layoutMeta.brandName}`}
        />
        <main className="min-w-0 flex-1 overflow-y-auto px-4 py-4 lg:px-4">
          {children}
        </main>
      </div>
      <Footer
        logo={<span className="font-semibold text-blue-600">{LANG_KO.layoutMeta.brandName}</span>}
        textObj={{ footerText: `© ${currentYear} ${LANG_KO.layoutMeta.brandName}` }}
        linkList={LANG_KO.layoutMeta.footerLinkList}
      />
    </div>
  );
};

export default DashboardLayoutClient;
