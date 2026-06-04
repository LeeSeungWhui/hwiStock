/**
 * 파일명: route.js
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: /login 진입 시 refresh_token으로 access_token을 재발급하고 next(=nx)/dashboard로 자동 리다이렉트
 */

import { NextResponse } from "next/server";
import { getBackendHost } from "@/app/common/config/getBackendHost.server";
import {
  AUTH_REASON_COOKIE,
  AUTH_REASON_MAXLEN,
  DEFAULT_NEXT_PATH,
  NX_COOKIE,
  base64UrlEncodeUtf8,
  extractUnauthorizedReason,
  decodeUriComponentValue,
  sanitizeInternalPath,
} from "@/app/lib/runtime/authRedirect";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const REFRESH_PATH = "/api/v1/auth/refresh";

/**
 * 설명: Cookie 헤더 문자열을 단순 파싱(값 디코딩은 별도 처리)
 * 갱신일: 2026-05-23
 */
const parseCookieHeader = (cookieHeader) => {
  const cookieObj = {};
  if (!cookieHeader || typeof cookieHeader !== "string") return cookieObj;
  const cookiePartList = cookieHeader.split(";");
  for (const cookiePart of cookiePartList) {
    const trimmedPart = cookiePart.trim();
    if (!trimmedPart) continue;
    const eqIndex = trimmedPart.indexOf("=");
    if (eqIndex <= 0) continue;
    const cookieNameText = trimmedPart.slice(0, eqIndex).trim();
    const cookieValueText = trimmedPart.slice(eqIndex + 1);
    if (!cookieNameText) continue;
    cookieObj[cookieNameText] = cookieValueText;
  }
  return cookieObj;
}

/**
 * 설명: 백엔드 Set-Cookie를 프런트 도메인에 맞게 정리(Domain 제거 + Path 보장)
 * 갱신일: 2026-05-23
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
 * 설명: 런타임별 Response 헤더 구현 차이 흡수와 Set-Cookie 배열 수집
 * 갱신일: 2026-05-23
 */
const collectSetCookies = (backendResponse) => {
  let setCookies = backendResponse?.headers?.getSetCookie?.() || [];
  if (!setCookies.length) {
    const singleSetCookie = backendResponse?.headers?.get?.("set-cookie");
    if (singleSetCookie) setCookies = [singleSetCookie];
  }
  return setCookies;
}

/**
 * 설명: refresh_token 존재 시 access_token 재발급 및 nx(/dashboard) 이동
 * 갱신일: 2026-05-23
 */
export const GET = async ({ headers, url }) => {
  const cookieHeader = headers.get("cookie") || "";
  const cookies = parseCookieHeader(cookieHeader);
  const refreshToken = cookies.refresh_token || null;
  const rawNext = decodeUriComponentValue(cookies[NX_COOKIE] || null);
  const nextPath = sanitizeInternalPath(rawNext, DEFAULT_NEXT_PATH);

  if (!refreshToken) {
    const redirectResponse = NextResponse.redirect(new URL("/login", url), 307);
    redirectResponse.headers.set("Cache-Control", "no-store");
    return redirectResponse;
  }

  const backendHost = await getBackendHost();
  const refreshUrl = new URL(REFRESH_PATH, backendHost);
  const requestHeaders = new Headers();
  const acceptLanguage = headers.get("accept-language");
  const originHeader = headers.get("origin");
  const refererHeader = headers.get("referer");
  if (acceptLanguage) requestHeaders.set("accept-language", acceptLanguage);
  if (cookieHeader) requestHeaders.set("cookie", cookieHeader);
  if (originHeader) requestHeaders.set("origin", originHeader);
  if (refererHeader) requestHeaders.set("referer", refererHeader);
  requestHeaders.set("content-type", "application/json");

  const refreshResponse = await fetch(refreshUrl, {
    method: "POST",
    headers: requestHeaders,
    redirect: "manual",
    cache: "no-store",
  });

  const setCookies = collectSetCookies(refreshResponse)
    .map(rewriteSetCookie)
    .filter(Boolean);
  const redirectTo = refreshResponse.ok ? nextPath : "/login";

  const redirectResponse = NextResponse.redirect(new URL(redirectTo, url), 307);
  redirectResponse.headers.set("Cache-Control", "no-store");

  if (refreshResponse.ok) {
    redirectResponse.cookies.set(NX_COOKIE, "", { path: "/", maxAge: 0 });
  }
  if (!refreshResponse.ok) {
    const reason = await extractUnauthorizedReason(refreshResponse);
    const reasonEncoded = reason
      ? base64UrlEncodeUtf8(JSON.stringify(reason))
      : null;
    if (reasonEncoded && reasonEncoded.length <= AUTH_REASON_MAXLEN) {
      redirectResponse.cookies.set(AUTH_REASON_COOKIE, reasonEncoded, {
        path: "/",
        httpOnly: true,
        sameSite: "lax",
        maxAge: 60,
      });
    }
  }

  for (const cookie of setCookies) {
    redirectResponse.headers.append("set-cookie", cookie);
  }

  return redirectResponse;
}
