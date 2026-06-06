"use client";

/**
 * 파일명: dashboard/DashboardLayoutClient.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 대시보드 레이아웃 클라이언트 컴포넌트
 */

import { useEffect, useRef } from "react";
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
  const uiRef = useRef(ui);
  uiRef.current = ui;
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
      const layoutUi = uiRef.current;
      layoutUi.isDesktopViewport = mediaQuery.matches;
      layoutUi.sidebarOpen = mediaQuery.matches;
    };

    syncViewport();
    mediaQuery.addEventListener("change", syncViewport);
    return () => mediaQuery.removeEventListener("change", syncViewport);
  }, []);

  /**
   * @description 모바일 뷰포트에서 route 변경 시 사이드바를 닫음
   * 처리 규칙: pathname/searchParams 변경마다 ui.sidebarOpen=false를 반영한다.
   */
  useEffect(() => {
    const layoutUi = uiRef.current;
    if (!layoutUi.isDesktopViewport) {
      layoutUi.sidebarOpen = false;
    }
  }, [pathname, searchParamText]);

  /* 9. 내부 컴포넌트 ============================================================================================================== */

  // 없음

  /* 10. 렌더링 ==================================================================================================================== */
  return (
    <div className="flex min-h-screen flex-col bg-slate-950 text-slate-100">
      <div className="sticky top-0 z-40">
        <Header
          title={<span className="text-slate-100">{layoutMeta.title}</span>}
          subtitle={<span className="text-slate-400">{layoutMeta.subtitle}</span>}
          menuList={layoutMeta.menuList}
          subMenuList={layoutMeta.subMenuList}
          onToggleSidebar={() => {
            ui.sidebarOpen = !ui.sidebarOpen;
          }}
          text={<span className="text-slate-400">{layoutMeta.text}</span>}
          className={[
            "!border-slate-800 !bg-slate-950/95 !shadow-lg !shadow-black/20 backdrop-blur",
            "[&_button]:!border-slate-700 [&_button]:!text-slate-300 [&_button]:hover:!bg-slate-800/80 [&_button]:hover:!text-slate-100",
            "[&_nav_a]:!border-slate-800 [&_nav_a]:!bg-slate-900/70 [&_nav_a]:!text-slate-300 [&_nav_a]:hover:!bg-slate-800/80 [&_nav_a]:hover:!text-slate-100",
            "[&_nav_a[aria-current='page']]:!border-cyan-500/50 [&_nav_a[aria-current='page']]:!bg-cyan-950/40 [&_nav_a[aria-current='page']]:!text-cyan-200",
            "[&_nav_button]:!border-slate-800 [&_nav_button]:!bg-slate-900/70 [&_nav_button]:!text-slate-300 [&_nav_button]:hover:!bg-slate-800/80 [&_nav_button]:hover:!text-slate-100",
            "[&_nav_div[role='menu']]:!border-slate-700 [&_nav_div[role='menu']]:!bg-slate-900 [&_nav_div[role='menu']]:!shadow-xl [&_nav_div[role='menu']]:!shadow-black/30",
            "[&_nav_div[role='menu']_a]:!text-slate-300 [&_nav_div[role='menu']_a]:hover:!bg-slate-800/80 [&_nav_div[role='menu']_a]:hover:!text-slate-100",
            "[&_nav_div[role='menu']_a[aria-current='page']]:!bg-cyan-950/40 [&_nav_div[role='menu']_a[aria-current='page']]:!text-cyan-200",
          ].join(" ")}
          logo={(
            <Link
              href="/"
              className="inline-flex items-center gap-2 rounded-md border border-slate-700 bg-slate-900/90 px-2.5 py-1.5 text-cyan-200 transition hover:border-cyan-500/40 hover:bg-slate-800/90"
            >
              <Icon icon="ri:RiCodeBoxLine" className="text-cyan-300" />
              <span className="text-sm font-semibold">{LANG_KO.layoutMeta.brandName}</span>
            </Link>
          )}
        >
          <Button
            size="sm"
            variant="ghost"
            className="border border-transparent px-2 text-slate-300 hover:border-slate-700 hover:bg-slate-800/80 hover:text-slate-100 sm:px-3"
            onClick={() => {
              router.push("/");
            }}
          >
            <Icon icon="ri:RiHome6Line" className="text-base sm:hidden" />
            <span className="hidden sm:inline">{LANG_KO.layoutMeta.layoutAction.goHome}</span>
          </Button>
          <Button
            size="sm"
            variant="secondary"
            className="border border-cyan-500/40 bg-cyan-950/40 px-2 text-cyan-100 hover:border-cyan-400/60 hover:bg-cyan-900/50 sm:px-3"
            onClick={handleLogout}
          >
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
            <span className="inline-flex items-center rounded-md border border-slate-700 bg-slate-900/90 px-2.5 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-cyan-200">
              {LANG_KO.layoutMeta.brandName}
            </span>
          }
          footerSlot={<span className="text-slate-500">© {currentYear} {LANG_KO.layoutMeta.brandName}</span>}
          className={[
            "!border-slate-800 !bg-slate-950/95 !shadow-xl !shadow-black/30",
            "[&_.text-gray-900]:!text-slate-100 [&_.text-gray-700]:!text-slate-300 [&_.text-gray-600]:!text-slate-300 [&_.text-gray-500]:!text-slate-500",
            "[&_.border-gray-200]:!border-slate-800 [&_.border-gray-100]:!border-slate-800",
            "[&_.bg-white]:!bg-slate-950/95 [&_.bg-gray-100]:!bg-slate-800/80 [&_.bg-gray-50]:!bg-slate-900/70",
            "[&_[aria-current='page']]:!bg-cyan-950/40 [&_[aria-current='page']]:!text-cyan-200 [&_[aria-current='page']]:!ring-cyan-500/30",
            "[&_button]:hover:!bg-slate-800/80 [&_a]:hover:!bg-slate-800/70",
          ].join(" ")}
        />
        <main className="min-w-0 flex-1 overflow-y-auto bg-slate-950 px-3 py-3 lg:px-3">
          {children}
        </main>
      </div>
      <Footer
        logo={<span className="font-semibold uppercase tracking-[0.18em] text-cyan-200">{LANG_KO.layoutMeta.brandName}</span>}
        textObj={{ footerText: `© ${currentYear} ${LANG_KO.layoutMeta.brandName}` }}
        linkList={LANG_KO.layoutMeta.footerLinkList}
        className="!border-slate-800 !bg-slate-950 !text-slate-400 [&_a]:!text-slate-400 [&_a]:hover:!text-slate-100 [&_[class*='text-gray-900']]:!text-slate-100 [&_[class*='text-gray-500']]:!text-slate-500"
      />
    </div>
  );
};

export default DashboardLayoutClient;
