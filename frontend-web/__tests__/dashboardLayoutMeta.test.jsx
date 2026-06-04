import { resolveDashboardLayoutMeta } from "@/app/dashboard/layoutMeta";

describe("dashboard layout meta", () => {
  test("감시 로그 경로에서 메뉴 활성화와 breadcrumb를 계산한다", () => {
    const layoutMeta = resolveDashboardLayoutMeta({
      pathname: "/dashboard/tasks",
      searchParams: new URLSearchParams({
        q: "로그",
        status: "running",
        sort: "amt_desc",
        page: "2",
      }),
    });

    expect(layoutMeta.title).toBe("감시 로그");
    expect(layoutMeta.subtitle).toContain("hwiStock > 감시 로그");
    expect(layoutMeta.subtitle).toContain("상태: 진행중");
    expect(layoutMeta.subtitle).toContain("정렬: 금액 높은순");
    expect(layoutMeta.subtitle).toContain("검색: 로그");
    expect(layoutMeta.subtitle).toContain("페이지: 2");
    expect(layoutMeta.menuList.find((menuItemObj) => menuItemObj.menuId === "tasks")?.active).toBe(true);
    expect(layoutMeta.menuList.find((menuItemObj) => menuItemObj.menuId === "tasks")?.menuNm).toBe("감시 로그");
    expect(
      layoutMeta.subMenuList.find((subMenuItemObj) => subMenuItemObj.subMenuId === "running")?.active
    ).toBe(true);
  });

  test("운영 콘솔 경로면 operator-console breadcrumb를 반환한다", () => {
    const layoutMeta = resolveDashboardLayoutMeta({
      pathname: "/dashboard",
      searchParams: new URLSearchParams(),
    });

    expect(layoutMeta.title).toBe("hwiStock 운영 콘솔");
    expect(layoutMeta.subtitle).toBe("hwiStock > 운영 콘솔");
    expect(layoutMeta.menuList.find((menuItemObj) => menuItemObj.menuId === "dashboard")?.menuNm).toBe(
      "운영 콘솔"
    );
    expect(layoutMeta.menuList.find((menuItemObj) => menuItemObj.menuId === "dashboard")?.active).toBe(
      true
    );
    expect(layoutMeta.subMenuList).toEqual([]);
    expect(layoutMeta.text).toBe("hwiStock 운영 모니터링");
    expect(layoutMeta.menuList.find((menuItemObj) => menuItemObj.menuId === "settings")?.menuNm).toBe(
      "운영 정책"
    );
  });

  test("운영 정책 경로면 탭 기준 breadcrumb를 반환한다", () => {
    const layoutMeta = resolveDashboardLayoutMeta({
      pathname: "/dashboard/settings",
      searchParams: new URLSearchParams({ tab: "connection" }),
    });

    expect(layoutMeta.title).toBe("운영 정책");
    expect(layoutMeta.subtitle).toBe("hwiStock > 운영 정책 > 연결 상태");
    expect(layoutMeta.menuList.find((menuItemObj) => menuItemObj.menuId === "settings")?.active).toBe(
      true
    );
  });
});
