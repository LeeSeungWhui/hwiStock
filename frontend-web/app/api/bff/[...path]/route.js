/**
 * 파일명: route.js
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Backend API 프록시(BFF) 라우트. Access/Refresh HttpOnly 쿠키를 받아 Authorization 헤더로 전달
 */

import { NextResponse } from "next/server";
import { getBackendHost } from "@/app/common/config/getBackendHost.server";
import { createHash } from "node:crypto";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const SKIP_HEADERS = new Set(["connection", "content-length", "host"]);
const REFRESH_PATH = "/api/v1/auth/refresh";
const LOGIN_PATH = "/api/v1/auth/login";
const LOGOUT_PATH = "/api/v1/auth/logout";
const ACCESS_COOKIE_NAME = "access_token";

// refresh_token 기반 singleflight(동시 탭/요청 경합 완화)

const refreshInflight = new Map();

/**
 * @description path 세그먼트와 쿼리를 백엔드 대상 URL로 조합
 * 처리 규칙: pathSegments가 비어 있으면 `/`를 사용하고, backendHost 기준 URL 객체를 반환한다.
 * @updated 2026-02-27
 */
const toBackendUrl = (
  pathSegments = [],
  search = "",
  backendHost = "http://127.0.0.1:5001",
) => {
  const normalizedPath =
    Array.isArray(pathSegments) && pathSegments.length
      ? `/${pathSegments.join("/")}`
      : "/";
  return new URL(`${normalizedPath}${search}`, backendHost);
}

/**
 * @description 클라이언트 요청 헤더를 백엔드 전달용 헤더로 복제
 * 처리 규칙: hop-by-hop/authorization 헤더는 제외하고 accessToken이 있으면 Bearer 헤더를 재주입한다.
 * @updated 2026-02-27
 */
const cloneRequestHeaders = (req, accessToken = null) => {
  const proxyHeaders = new Headers();
  req.headers.forEach((value, key) => {
    if (SKIP_HEADERS.has(key.toLowerCase())) return;
    if (key.toLowerCase() === "authorization") return;
    proxyHeaders.set(key, value);
  });
  if (accessToken) proxyHeaders.set("authorization", `Bearer ${accessToken}`);
  return proxyHeaders;
}

/**
 * @description 백엔드 Set-Cookie 값을 프론트 도메인 기준으로 재작성
 * 처리 규칙: Domain 속성은 제거하고 Path 속성이 없으면 `Path=/`를 강제한다.
 * @updated 2026-02-27
 */
const rewriteSetCookie = (rawValue) => {
  if (!rawValue || typeof rawValue !== "string") return null;
  const cookieSegmentList = rawValue.split(";");
  const rewrittenSegmentList = [];
  for (const cookieSegment of cookieSegmentList) {
    const trimmedSegment = cookieSegment.trim();
    if (!trimmedSegment) continue;
    const cookiePartLower = trimmedSegment.toLowerCase();
    if (cookiePartLower.startsWith("domain=")) continue;
    rewrittenSegmentList.push(trimmedSegment);
  }
  const hasPath = rewrittenSegmentList.some((cookieSegment) =>
    cookieSegment.toLowerCase().startsWith("path="),
  );
  if (!hasPath) rewrittenSegmentList.push("Path=/");
  return rewrittenSegmentList.join("; ");
}

/**
 * @description Response에서 Set-Cookie 목록을 수집
 * 처리 규칙: `getSetCookie()` 우선, 미지원 환경에서는 단일 `set-cookie` 헤더를 배열로 보정한다.
 * @updated 2026-02-27
 */
const collectSetCookies = (backendResponse) => {
  let setCookieList = backendResponse.headers.getSetCookie?.() || [];
  if (!setCookieList.length) {
    const singleSetCookie = backendResponse.headers.get("set-cookie");
    if (singleSetCookie) setCookieList = [singleSetCookie];
  }
  return setCookieList;
}

/**
 * @description Cookie 목록에서 지정 쿠키의 값만 추출
 * 처리 규칙: 각 쿠키의 첫 key=value 페어를 파싱해 이름이 일치하는 항목의 값을 반환한다.
 * @updated 2026-02-27
 */
const readCookieValue = (setCookieList, cookieName) => {
  if (!Array.isArray(setCookieList) || !cookieName) return null;
  for (const cookie of setCookieList) {
    if (!cookie || typeof cookie !== "string") continue;
    const firstPair = cookie.split(";")[0] || "";
    const eqIndex = firstPair.indexOf("=");
    if (eqIndex <= 0) continue;
    const cookieNameText = firstPair.slice(0, eqIndex).trim();
    if (cookieNameText !== cookieName) continue;
    const cookieValueText = firstPair.slice(eqIndex + 1);
    return cookieValueText || null;
  }
  return null;
}

/**
 * @description refresh token을 singleflight key 용 해시로 변환. 입력/출력 계약을 함께 명시
 * 처리 규칙: SHA-256 hex 문자열을 반환하고 해시 실패/무효 입력은 null을 반환한다.
 * @updated 2026-02-27
 */
const hashToken = (token) => {
  if (!token || typeof token !== "string") return null;
  try {
    return createHash("sha256").update(token).digest("hex");
  } catch {
    return null;
  }
}

/**
 * @description 현재 백엔드 경로에서 refresh 재시도가 가능한지 판정
 * 처리 규칙: refresh/login/logout 경로는 재시도 대상에서 제외한다.
 * @updated 2026-02-27
 */
const shouldAttemptRefresh = (backendPathname) => {
  if (!backendPathname || typeof backendPathname !== "string") return false;
  if (backendPathname === REFRESH_PATH) return false;
  if (backendPathname === LOGIN_PATH) return false;
  if (backendPathname === LOGOUT_PATH) return false;
  return true;
}

/**
 * @description 현재 HTTP 메서드가 요청 본문을 갖는지 판별
 * 처리 규칙: GET/HEAD만 false로 처리하고 그 외 메서드는 true를 반환한다.
 * @updated 2026-02-27
 */
const hasRequestBody = (requestMethod) => {
  const upperMethod = String(requestMethod || "GET").toUpperCase();
  return !(upperMethod === "GET" || upperMethod === "HEAD");
}

/**
 * @description 프록시 재시도용 요청 본문 스트림 쌍을 준비
 * 처리 규칙: `ReadableStream.tee()` 가능 시 primary/retry를 분리하고, 미지원이면 재시도 불가로 표시한다.
 * @updated 2026-02-27
 */
const splitRetryBody = (req) => {
  if (!req?.body) {
    return { primaryBody: undefined, retryBody: undefined, canRetry: true };
  }
  if (typeof req.body.tee === "function") {
    const [primaryBody, retryBody] = req.body.tee();
    return { primaryBody, retryBody, canRetry: true };
  }
  return { primaryBody: req.body, retryBody: null, canRetry: false };
}

/**
 * @description fetch init에 요청 본문을 안전하게 주입
 * 처리 규칙: body가 Stream이면 `duplex: 'half'`를 함께 지정한다.
 * @updated 2026-02-27
 */
const attachBody = (requestInitObj, requestBody) => {
  if (typeof requestBody === "undefined") return;
  requestInitObj.body = requestBody;
  if (typeof ReadableStream !== "undefined" && requestBody instanceof ReadableStream) {
    requestInitObj.duplex = "half";
  }
}

/**
 * @description refresh 요청을 singleflight로 한 번만 실행해 토큰을 회전
 * 처리 규칙: 동일 refresh token 해시키의 동시 요청은 기존 inflight Promise를 재사용한다.
 * @updated 2026-02-27
 */
const refreshOnce = async (req, backendHost) => {
  const refreshToken = req.cookies.get("refresh_token")?.value || null;
  const tokenKey = hashToken(refreshToken);
  if (!tokenKey) {
    return { isRefreshSucceeded: false, accessToken: null, setCookieList: [] };
  }

  const inflight = refreshInflight.get(tokenKey);
  if (inflight) return inflight;

  const refreshUrl = new URL(REFRESH_PATH, backendHost);
  const refreshHeaders = cloneRequestHeaders(req, null);
  let requestOrigin = req.nextUrl?.origin || "";
  if (!requestOrigin) {
    try {
      requestOrigin = new URL(req.url || "").origin;
    } catch {
      requestOrigin = "";
    }
  }

  // refresh는 쿠키 기반이므로 Authorization은 붙이지 않는다.
  refreshHeaders.delete("authorization");
  if (!refreshHeaders.has("origin") && requestOrigin) {
    refreshHeaders.set("origin", requestOrigin);
  }
  if (!refreshHeaders.has("referer") && requestOrigin) {
    refreshHeaders.set("referer", `${requestOrigin}/`);
  }
  if (!refreshHeaders.has("content-type")) {
    refreshHeaders.set("content-type", "application/json");
  }

  const refreshTask = fetch(refreshUrl, {
    method: "POST",
    headers: refreshHeaders,
    redirect: "manual",
    cache: "no-store",
  })
    .then(async (refreshResponse) => {
      const refreshSetCookieList = collectSetCookies(refreshResponse)
        .map(rewriteSetCookie)
        .filter(Boolean);
      const accessToken =
        readCookieValue(refreshSetCookieList, ACCESS_COOKIE_NAME) || null;

      if (!refreshResponse.ok || !accessToken) {
        return {
          isRefreshSucceeded: false,
          accessToken: null,
          setCookieList: refreshSetCookieList,
        };
      }
      return {
        isRefreshSucceeded: true,
        accessToken,
        setCookieList: refreshSetCookieList,
      };
    });

  refreshInflight.set(tokenKey, refreshTask);
  try {
    return await refreshTask;
  } finally {
    refreshInflight.delete(tokenKey);
  }
}

/**
 * @description BFF 프록시 요청을 중계하고 필요 시 refresh 재시도 흐름을 운영
 * 처리 규칙: 401 응답에서 refresh 1회 후 재시도하고, refresh/원응답의 Set-Cookie를 병합해 클라이언트로 반환한다.
 * @updated 2026-02-27
 */
const proxy = async (req, context = {}) => {

  const routeParamsObj = await context?.params;
  const backendHost = await getBackendHost();
  const accessToken = req.cookies.get("access_token")?.value || null;
  const backendUrl = toBackendUrl(routeParamsObj?.path, req.nextUrl.search, backendHost);
  const proxyHeaders = cloneRequestHeaders(req, accessToken);

  const requestInitObj = {
    method: req.method,
    headers: proxyHeaders,
    redirect: "manual",
    cache: "no-store",
  };

  const hasBody = hasRequestBody(req.method);
  const bodyPair = hasBody
    ? splitRetryBody(req)
    : { primaryBody: undefined, retryBody: undefined, canRetry: true };
  attachBody(requestInitObj, bodyPair.primaryBody);

  let backendResponse = await fetch(backendUrl, requestInitObj);
  let refreshOutcomeObj = {
    isRefreshSucceeded: false,
    accessToken: null,
    setCookieList: [],
  };

  // 401이면 refresh 1회만 수행한 뒤 재시도한다(동시 탭/요청 경합은 singleflight로 흡수).
  if (backendResponse.status === 401) {
    if (shouldAttemptRefresh(backendUrl.pathname)) {
      refreshOutcomeObj = await refreshOnce(req, backendHost);
      if (refreshOutcomeObj.isRefreshSucceeded && refreshOutcomeObj.accessToken) {
        const retryHeaders = cloneRequestHeaders(req, refreshOutcomeObj.accessToken);
        const retryInitObj = {
          method: req.method,
          headers: retryHeaders,
          redirect: "manual",
          cache: "no-store",
        };
        if (hasBody && !bodyPair.canRetry) {

          // 한글설명: 메모리 전체 버퍼링 재시도는 금지한다.
          // 한글설명: refresh 쿠키만 반영하고 원 요청 재시도는 생략한다.
        } else {
          attachBody(retryInitObj, bodyPair.retryBody);
          backendResponse = await fetch(backendUrl, retryInitObj);
        }
      }
    }
  }

  const responseHeaders = new Headers();
  backendResponse.headers.forEach((value, key) => {
    if (key.toLowerCase() === "set-cookie") return;
    responseHeaders.append(key, value);
  });

  // refresh 결과의 Set-Cookie(회전/삭제)를 우선 반영한다.
  for (const cookie of refreshOutcomeObj.setCookieList || []) {
    responseHeaders.append("set-cookie", cookie);
  }

  for (const cookie of collectSetCookies(backendResponse)) {
    const rewritten = rewriteSetCookie(cookie);
    if (rewritten) responseHeaders.append("set-cookie", rewritten);
  }

  return new NextResponse(backendResponse.body, {
    status: backendResponse.status,
    headers: responseHeaders,
  });
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
export const HEAD = proxy;
export const OPTIONS = proxy;
