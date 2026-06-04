/**
 * 파일명: pageData.test.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-03
 * 설명: pageData 로더의 API 엔트리 해석/실패 매핑 회귀 테스트
 */

import { describe, expect, it, vi } from "vitest";
import {
  listPageApiEntries,
  loadPageDataObj,
  loadServerPageData,
  normalizePageConfig,
} from "@/app/lib/runtime/pageData";

describe("pageData", () => {
  it("string/object API 엔트리를 공통 스펙으로 정규화한다", () => {
    const pageConfig = normalizePageConfig({
      MODE: "ssr",
      INIT_API: {
        bootstrap: "/api/bootstrap",
      },
      API: {
        list: "/api/list",
        detail: {
          path: "/api/detail",
          method: "POST",
          body: { id: "R-1" },
          authless: true,
          init: {
            headers: {
              "X-Test": "1",
            },
          },
        },
      },
    });

    expect(pageConfig).toEqual({
      MODE: "SSR",
      INIT_API: {
        bootstrap: "/api/bootstrap",
      },
      API: {
        list: "/api/list",
        detail: {
          path: "/api/detail",
          method: "POST",
          body: { id: "R-1" },
          authless: true,
          init: {
            headers: {
              "X-Test": "1",
            },
          },
        },
      },
    });

    expect(listPageApiEntries(pageConfig)).toEqual([
      [
        "bootstrap",
        {
          path: "/api/bootstrap",
          method: "GET",
          body: undefined,
          fetchInit: {},
          options: {},
        },
      ],
    ]);

    expect(listPageApiEntries(pageConfig, "API")).toEqual([
      [
        "list",
        {
          path: "/api/list",
          method: "GET",
          body: undefined,
          fetchInit: {},
          options: {},
        },
      ],
      [
        "detail",
        {
          path: "/api/detail",
          method: "POST",
          body: { id: "R-1" },
          fetchInit: {
            headers: {
              "X-Test": "1",
            },
          },
          options: {
            authless: true,
          },
        },
      ],
    ]);
  });

  it("API 엔트리를 모두 호출하고 path/init/options를 fetcher에 전달한다", async () => {
    const fetcher = vi.fn(async (path, init, options) => ({
      path,
      init,
      options,
    }));

    const loaded = await loadPageDataObj({
      pageConfig: {
        MODE: "SSR",
        INIT_API: {
          list: "/api/list",
          detail: {
            path: "/api/detail",
            method: "POST",
            body: { id: "R-2" },
            authless: true,
            init: {
              headers: {
                "X-Test": "detail",
              },
            },
          },
        },
      },
      fetcher,
    });

    expect(fetcher).toHaveBeenCalledTimes(2);
    expect(fetcher).toHaveBeenNthCalledWith(1, "/api/list", {
      method: "GET",
    });
    expect(fetcher).toHaveBeenNthCalledWith(2, "/api/detail", {
      method: "POST",
      body: { id: "R-2" },
      headers: {
        "X-Test": "detail",
      },
    }, {
      authless: true,
    });
    expect(loaded).toEqual({
      dataObj: {
        list: {
          path: "/api/list",
          init: {
            method: "GET",
          },
          options: undefined,
        },
        detail: {
          path: "/api/detail",
          init: {
            method: "POST",
            body: { id: "R-2" },
            headers: {
              "X-Test": "detail",
            },
          },
          options: {
            authless: true,
          },
        },
      },
      errorObj: {},
      hasError: false,
    });
  });

  it("실패 엔트리는 errorObj에 모으고 성공 데이터는 유지한다", async () => {
    const fetcher = vi.fn(async (path) => {
      if (path === "/api/fail") {
        const error = new Error("boom");
        error.code = "E_FAIL";
        error.requestId = "req-1";
        error.statusCode = 503;
        throw error;
      }
      return {
        result: {
          ok: true,
          path,
        },
      };
    });

    const loaded = await loadPageDataObj({
      pageConfig: {
        MODE: "SSR",
        INIT_API: {
          ok: "/api/ok",
          fail: "/api/fail",
        },
      },
      fetcher,
    });

    expect(loaded.dataObj.ok).toEqual({
      result: {
        ok: true,
        path: "/api/ok",
      },
    });
    expect(loaded.errorObj.fail).toEqual({
      message: "boom",
      code: "E_FAIL",
      requestId: "req-1",
      statusCode: 503,
    });
    expect(loaded.hasError).toBe(true);
  });

  it("CSR mode의 loadServerPageData는 fetcher를 호출하지 않는다", async () => {
    const fetcher = vi.fn(async () => {
      throw new Error("must not be called");
    });

    const loaded = await loadServerPageData({
      pageConfig: {
        MODE: "CSR",
        INIT_API: {
          list: "/api/list",
        },
        API: {
          list: "/api/list",
        },
      },
      fetcher,
    });

    expect(fetcher).not.toHaveBeenCalled();
    expect(loaded).toEqual({
      mode: "CSR",
      dataObj: {},
      errorObj: {},
      hasError: false,
    });
  });
});
