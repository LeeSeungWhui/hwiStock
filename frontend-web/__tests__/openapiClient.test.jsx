/**
 * 파일명: openapiClient.test.jsx
 * 작성자: LSH
 * 갱신일: 2026-01-18
 * 설명: OpenAPI(operationId) 기반 호출 유틸(openapiRequest/openapiJSON) 테스트
 */

import { beforeEach, afterEach, describe, expect, it, vi } from "vitest";

function buildJsonResponse(payload, init = {}) {
  return new Response(JSON.stringify(payload), {
    status: 200,
    headers: { "Content-Type": "application/json" },
    ...init,
  });
}

const OPENAPI_SPEC = {
  openapi: "3.0.0",
  info: { title: "test", version: "0" },
  paths: {
    "/api/v1/auth/me": {
      get: {
        operationId: "auth_me",
        responses: { 200: { description: "OK" } },
      },
    },
    "/api/v1/items": {
      get: {
        operationId: "list_items",
        parameters: [
          {
            name: "page",
            in: "query",
            required: false,
            schema: { type: "integer" },
          },
        ],
        responses: { 200: { description: "OK" } },
      },
    },
  },
};

describe("openapiClient", () => {
  beforeEach(() => {
    process.env.VITEST = "1";
    vi.resetModules();
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("openapiJSON은 operationId로 호출하고 /api/bff 경유로 요청한다", async () => {
    fetch
      .mockResolvedValueOnce(buildJsonResponse(OPENAPI_SPEC))
      .mockResolvedValueOnce(
        buildJsonResponse({
          status: true,
          message: "success",
          result: { username: "u" },
          requestId: "r",
        }),
      );

    const { openapiJSON } = await import("@/app/lib/runtime/openapiClient");
    const authMeBodyObj = await openapiJSON("auth_me");

    expect(authMeBodyObj?.result?.username).toBe("u");
    expect(fetch).toHaveBeenCalledTimes(2);
    expect(fetch.mock.calls[0][0]).toBe("/api/bff/openapi.json");
    expect(fetch.mock.calls[1][0]).toBe("/api/bff/api/v1/auth/me");
  });

  it("openapiRequest는 query 파라미터를 URL에 반영한다", async () => {
    fetch
      .mockResolvedValueOnce(buildJsonResponse(OPENAPI_SPEC))
      .mockResolvedValueOnce(
        buildJsonResponse({
          status: true,
          message: "success",
          result: [],
          requestId: "r",
        }),
      );

    const { openapiRequest } = await import("@/app/lib/runtime/openapiClient");
    const res = await openapiRequest("list_items", { page: 2 });

    expect(res.status).toBe(200);
    expect(fetch).toHaveBeenCalledTimes(2);
    expect(fetch.mock.calls[1][0]).toBe("/api/bff/api/v1/items?page=2");
  });

  it("OpenAPI 스키마는 1회만 로드한다(캐시)", async () => {
    fetch
      .mockResolvedValueOnce(buildJsonResponse(OPENAPI_SPEC))
      .mockResolvedValueOnce(
        buildJsonResponse({
          status: true,
          message: "success",
          result: { username: "u" },
          requestId: "r1",
        }),
      )
      .mockResolvedValueOnce(
        buildJsonResponse({
          status: true,
          message: "success",
          result: { username: "u2" },
          requestId: "r2",
        }),
      );

    const { openapiJSON } = await import("@/app/lib/runtime/openapiClient");
    await openapiJSON("auth_me");
    await openapiJSON("auth_me");

    const openapiFetchCount = fetch.mock.calls.filter(
      (c) => c[0] === "/api/bff/openapi.json",
    ).length;
    expect(openapiFetchCount).toBe(1);
  });
});
