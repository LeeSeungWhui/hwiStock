import { vi } from "vitest";

import { PAGE_CONFIG as DASHBOARD_PAGE_CONFIG } from "@/app/dashboard/initData";
import {
  isSsrMode,
  listPageApiEntries,
  loadPageDataObj,
  loadServerPageData,
} from "@/app/lib/runtime/pageData";

describe("dashboard data strategy", () => {
  it("MODE가 SSR일 때만 SSR 모드로 판단한다", () => {
    expect(isSsrMode("SSR")).toBe(true);
    expect(isSsrMode("ssr")).toBe(true);
    expect(isSsrMode("CSR")).toBe(false);
    expect(isSsrMode("")).toBe(false);
  });

  it("대시보드 PAGE_CONFIG는 operator API 엔트리를 가진다", () => {
    const apiEntryList = listPageApiEntries(DASHBOARD_PAGE_CONFIG);
    const keyList = apiEntryList.map(([apiKey]) => apiKey);

    expect(keyList).toEqual(["operator"]);
  });

  it("CSR 모드면 서버 초기 조회를 건너뛴다", async () => {
    const fetcher = vi.fn();
    const result = await loadServerPageData({
      pageConfig: {
        MODE: "CSR",
        API: {
          operator: "/api/v1/hwistock/runner/operator-snapshot",
        },
      },
      fetcher,
    });

    expect(fetcher).not.toHaveBeenCalled();
    expect(result).toEqual({
      mode: "CSR",
      dataObj: {},
      errorObj: {},
      hasError: false,
    });
  });

  it("SSR 모드면 operator snapshot을 조회해 초기 데이터를 만든다", async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValueOnce({
        result: {
          schema_version: "operator_console_snapshot/v0",
          status: { mode: "paper_sandbox" },
          summary: { operationalTradingReadiness: false },
        },
      });

    const result = await loadServerPageData({
      pageConfig: DASHBOARD_PAGE_CONFIG,
      fetcher,
    });

    expect(fetcher).toHaveBeenCalledTimes(1);
    expect(fetcher).toHaveBeenNthCalledWith(1, "/api/v1/hwistock/runner/operator-snapshot", {
      method: "GET",
    });
    expect(result.dataObj.operator).toEqual({
      result: {
        schema_version: "operator_console_snapshot/v0",
        status: { mode: "paper_sandbox" },
        summary: { operationalTradingReadiness: false },
      },
    });
    expect(result.errorObj).toEqual({});
    expect(result.hasError).toBe(false);
  });

  it("SSR 초기 조회 실패 시 errorObj로 정규화한다", async () => {
    const fetchError = new Error("fetch failed");
    fetchError.code = "DASHBOARD_500";
    fetchError.requestId = "rid-dashboard-1";
    fetchError.statusCode = 500;
    const fetcher = vi.fn().mockRejectedValueOnce(fetchError);

    const result = await loadPageDataObj({
      pageConfig: DASHBOARD_PAGE_CONFIG,
      fetcher,
    });

    expect(result.errorObj.operator).toMatchObject({
      message: "fetch failed",
      code: "DASHBOARD_500",
      requestId: "rid-dashboard-1",
      statusCode: 500,
    });
    expect(result.hasError).toBe(true);
  });
});
