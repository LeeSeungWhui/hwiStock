/**
 * 파일명: apiRuntime.test.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-03
 * 설명: apiRequest/apiJSON(SSR/CSR 공통 유틸) 동작 테스트
 */

import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { apiJSON, apiRequest } from "@/app/lib/runtime/api";

function buildJsonResponse(payload, init = {}) {
  return new Response(JSON.stringify(payload), {
    status: 200,
    headers: { "Content-Type": "application/json" },
    ...init,
  });
}

function decodeBase64UrlJson(encoded) {
  const base64 = String(encoded || "")
    .replace(/-/g, "+")
    .replace(/_/g, "/");
  const padded = base64 + "===".slice((base64.length + 3) % 4);
  const decodedText = Buffer.from(padded, "base64").toString("utf8");
  return JSON.parse(decodedText);
}

describe("runtime api", () => {
  beforeEach(() => {
    process.env.VITEST = "1";
    vi.stubGlobal("fetch", vi.fn());
    window.history.replaceState({}, "", "/");
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("상대 경로는 /api/bff 프록시로 요청한다", async () => {
    fetch.mockResolvedValueOnce(
      buildJsonResponse({ status: true, result: { ok: true } }),
    );
    await apiRequest("/api/v1/auth/me", { method: "GET" });

    expect(fetch).toHaveBeenCalledTimes(1);
    const [requestUrl, requestInitObj] = fetch.mock.calls[0];
    expect(requestUrl).toBe("/api/bff/api/v1/auth/me");
    expect(requestInitObj).toMatchObject({ method: "GET", credentials: "include" });
  });

  it("JSON body는 Content-Type=application/json으로 전송한다", async () => {
    fetch.mockResolvedValueOnce(
      buildJsonResponse({ status: true, result: {} }),
    );
    await apiRequest("/api/v1/auth/login", { method: "POST", body: { a: 1 } });

    const [, requestInitObj] = fetch.mock.calls[0];
    expect(
      String(
        requestInitObj?.headers?.["Content-Type"] ||
          requestInitObj?.headers?.["content-type"] ||
          "",
      ),
    ).toBe("application/json");
    expect(requestInitObj.body).toBe(JSON.stringify({ a: 1 }));
  });

  it("PAGE_CONFIG API object 엔트리를 첫 인자로 받아 path/method/authless를 해석한다", async () => {
    fetch.mockResolvedValueOnce(
      buildJsonResponse({ status: true, result: { ok: true } }),
    );

    await apiRequest({
      path: "/api/v1/auth/me",
      method: "GET",
      authless: true,
    });

    expect(fetch).toHaveBeenCalledTimes(1);
    const [requestUrl, requestInitObj] = fetch.mock.calls[0];
    expect(requestUrl).toBe("/api/bff/api/v1/auth/me");
    expect(requestInitObj).toMatchObject({ method: "GET", credentials: "include" });
  });

  it("FormData body는 Content-Type을 강제로 지정하지 않는다", async () => {
    const form = new FormData();
    form.append("file", new Blob(["x"], { type: "text/plain" }), "a.txt");

    fetch.mockResolvedValueOnce(
      buildJsonResponse({ status: true, result: {} }),
    );
    await apiRequest("/api/v1/upload", { method: "POST", body: form });

    const [, requestInitObj] = fetch.mock.calls[0];
    const requestHeaders = requestInitObj?.headers || {};
    const keys = Object.keys(requestHeaders).map((k) => k.toLowerCase());
    expect(keys).not.toContain("content-type");
    expect(requestInitObj.body).toBe(form);
  });

  it("401 + 로그인 페이지 밖이면 UnauthorizedError로 끊고 redirectTo를 제공한다", async () => {
    window.history.replaceState({}, "", "/dashboard?foo=bar");
    fetch.mockResolvedValueOnce(new Response("", { status: 401 }));

    await expect(
      apiRequest("/api/v1/auth/me", { method: "GET" }),
    ).rejects.toMatchObject({
      name: "UnauthorizedError",
      redirectTo: "/login?next=%2Fdashboard%3Ffoo%3Dbar",
    });
  });

  it("401 body에 code/requestId가 있으면 reason으로 전달한다", async () => {
    window.history.replaceState({}, "", "/dashboard");
    fetch.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          status: false,
          code: "AUTH_401_INVALID",
          requestId: "req-123",
          message: "expired",
        }),
        { status: 401, headers: { "Content-Type": "application/json" } },
      ),
    );

    let err = null;
    try {
      await apiRequest("/api/v1/auth/me", { method: "GET" });
    } catch (e) {
      err = e;
    }
    expect(err).toBeTruthy();
    expect(err.name).toBe("UnauthorizedError");

    const u = new URL(err.redirectTo, "http://localhost:5000");
    expect(u.pathname).toBe("/login");
    expect(u.searchParams.get("next")).toBe("/dashboard");

    const reasonEncoded = u.searchParams.get("reason");
    expect(reasonEncoded).toBeTruthy();
    const reason = decodeBase64UrlJson(reasonEncoded);
    expect(reason).toMatchObject({
      code: "AUTH_401_INVALID",
      requestId: "req-123",
    });
  });

  it("401 + /login에서는 응답을 그대로 반환해 로그인 에러 처리가 가능하다", async () => {
    window.history.replaceState({}, "", "/login");
    fetch.mockResolvedValueOnce(
      new Response(
        JSON.stringify({ status: false, code: "AUTH_401_INVALID" }),
        { status: 401 },
      ),
    );

    const res = await apiRequest("/api/v1/auth/login", {
      method: "POST",
      body: { a: 1 },
    });
    expect(res.status).toBe(401);
  });

  it("401 + authless 모드에서는 자동 리다이렉트 없이 응답을 반환한다", async () => {
    window.history.replaceState({}, "", "/dashboard");
    fetch.mockResolvedValueOnce(new Response("", { status: 401 }));

    const res = await apiRequest(
      "/api/v1/auth/me",
      { method: "GET" },
      "authless",
    );
    expect(res.status).toBe(401);
  });

  it("401 + modeOrOptions.authless=true에서도 자동 리다이렉트 없이 응답을 반환한다", async () => {
    window.history.replaceState({}, "", "/dashboard");
    fetch.mockResolvedValueOnce(new Response("", { status: 401 }));

    const res = await apiRequest(
      "/api/v1/auth/me",
      { method: "GET" },
      { authless: true },
    );
    expect(res.status).toBe(401);
  });

  it("apiJSON은 status=false 또는 비정상 statusCode에서 ApiError를 던진다", async () => {
    fetch.mockResolvedValueOnce(
      buildJsonResponse({ status: false, code: "E", message: "nope" }),
    );
    await expect(
      apiJSON("/api/v1/test", { method: "GET" }),
    ).rejects.toMatchObject({ name: "ApiError", code: "E" });

    fetch.mockResolvedValueOnce(
      new Response(JSON.stringify({ status: false, code: "E2" }), {
        status: 500,
        headers: { "Content-Type": "application/json" },
      }),
    );
    await expect(
      apiJSON("/api/v1/test", { method: "GET" }),
    ).rejects.toMatchObject({ name: "ApiError", code: "E2" });
  });
});
