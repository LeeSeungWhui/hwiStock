/**
 * 파일명: middleware.js
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Next 미들웨어 인증 가드 및 리다이렉트 로직
 */

import { NextResponse } from "next/server";
import { isPublicPath } from "@/app/common/config/publicRoutes";

import {
  AUTH_REASON_COOKIE,
  AUTH_REASON_QUERY_PARAM,
  NX_COOKIE,
  NEXT_QUERY_PARAM,
  sanitizeBase64Url,
  sanitizeInternalPath,
  base64UrlDecodeUtf8,
} from "@/app/lib/runtime/authRedirect";

const JWT_SEGMENT_RE = /^[A-Za-z0-9_-]+$/;
const JWT_MAX_LENGTH = 4096;
const JWT_PAYLOAD_MAX_LENGTH = 4096;

/**
 * @description JWT 세그먼트 문자열 형식을 검증
 * 처리 규칙: 빈 값/비문자열은 false로 처리하고 base64url 허용 문자만 통과시킨다.
 * 반환값: JWT 세그먼트 형식 적합 여부(boolean)
 * @updated 2026-02-28
 */
function isValidJwtSegment(segment) {
  if (!segment || typeof segment !== "string") return false;
  return JWT_SEGMENT_RE.test(segment);
}

/**
 * @description JWT payload에서 exp(만료 시각, epoch seconds)를 안전하게 추출
 * 처리 규칙: 토큰 형식/길이/payload JSON을 검증하고 유효하지 않으면 null을 반환한다.
 * 반환값: 만료 시각(exp) 정수 또는 null
 * @updated 2026-02-28
 */
function getJwtExpSeconds(token) {
  if (!token || typeof token !== "string") return null;
  const normalized = token.trim();
  if (!normalized || normalized.length > JWT_MAX_LENGTH) return null;
  const parts = normalized.split(".");
  if (parts.length !== 3) return null;
  if (!isValidJwtSegment(parts[0]) || !isValidJwtSegment(parts[1])) return null;
  const payloadText = base64UrlDecodeUtf8(parts[1]);
  if (!payloadText || payloadText.length > JWT_PAYLOAD_MAX_LENGTH) return null;
  try {
    const jwtPayloadObj = JSON.parse(payloadText);
    const exp = jwtPayloadObj?.exp;
    if (typeof exp !== "number" || !Number.isFinite(exp)) return null;
    const normalizedExp = Math.trunc(exp);
    if (normalizedExp <= 0) return null;
    return normalizedExp;
  } catch {
    return null;
  }
}

/**
 * @description 현재 시각 기준 JWT 만료 여부를 leeway를 포함해 판정
 * 처리 규칙: exp가 없거나 비정상이면 만료로 간주(false)하고, 유효 시각이면 true를 반환한다.
 * 반환값: 토큰 만료 전 여부(boolean)
 * @updated 2026-02-28
 */
function isJwtNotExpired(token, leewaySeconds = 30) {
  const exp = getJwtExpSeconds(token);
  if (!exp) return false;
  const now = Math.floor(Date.now() / 1000);
  return exp > now + Math.max(0, Number(leewaySeconds) || 0);
}

const QUARANTINE_PATH_PREFIXES = [
  "/sample",
  "/component",
  "/portfolio",
  "/signup",
  "/forgot-password",
];

/**
 * @description 템플릿 잔존 공개/샘플/인증 퍼널 경로 격리 대상 여부
 * 처리 규칙: prefix 일치 또는 prefix/하위 경로만 격리한다.
 * 반환값: 격리 대상 여부(boolean)
 */
function isQuarantinedPath(pathname) {
  if (!pathname || typeof pathname !== "string") return false;
  for (const prefix of QUARANTINE_PATH_PREFIXES) {
    if (pathname === prefix || pathname.startsWith(`${prefix}/`)) {
      return true;
    }
  }
  return false;
}

/**
 * @description 격리 경로 접근 시 /login, /dashboard, /api/session/bootstrap로 보냄
 * 처리 규칙: nx는 항상 /dashboard로 고정하고 템플릿 경로는 보존하지 않는다.
 * 반환값: NextResponse.redirect() 응답 객체
 */
function redirectQuarantinedPath(req, { hasAuthCookie, hasValidAccessToken }) {
  if (hasValidAccessToken) {
    const res = NextResponse.redirect(new URL("/dashboard", req.url));
    res.cookies.set(NX_COOKIE, "", { path: "/", maxAge: 0 });
    res.cookies.set(AUTH_REASON_COOKIE, "", { path: "/", maxAge: 0 });
    return res;
  }
  if (hasAuthCookie) {
    const res = NextResponse.redirect(
      new URL("/api/session/bootstrap", req.url),
    );
    res.cookies.set(NX_COOKIE, "/dashboard", {
      path: "/",
      httpOnly: true,
      sameSite: "lax",
      maxAge: 300,
    });
    if (req.cookies.get(AUTH_REASON_COOKIE)) {
      res.cookies.set(AUTH_REASON_COOKIE, "", { path: "/", maxAge: 0 });
    }
    return res;
  }
  const res = NextResponse.redirect(new URL("/login", req.url));
  res.cookies.set(NX_COOKIE, "/dashboard", {
    path: "/",
    httpOnly: true,
    sameSite: "lax",
    maxAge: 300,
  });
  return res;
}

/**
 * @description 공개/보호 경로 접근 시 인증 쿠키 상태에 맞는 리다이렉트 정책을 수행
 * 처리 규칙: refresh/access 쿠키와 요청 경로를 기준으로 next/login/bootstrap/dashboard 분기를 적용한다.
 * 반환값: NextResponse.next() 또는 NextResponse.redirect() 응답 객체
 * @updated 2026-02-28
 */
export async function middleware(req) {
  const requestUrlObj = new URL(req.url);
  const requestPath = requestUrlObj.pathname;

  // refresh_token이 있어야 인증 상태로 간주한다(access_token 단독/없는 경우는 재인증 유도)
  const hasAuthCookie = Boolean(req.cookies.get("refresh_token"));
  const accessToken = req.cookies.get("access_token")?.value || null;
  const hasValidAccessToken = accessToken
    ? isJwtNotExpired(accessToken, 30)
    : false;
  const purpose = (
    req.headers.get("purpose") ||
    req.headers.get("sec-purpose") ||
    ""
  ).toLowerCase();
  if (purpose.includes("prefetch")) return NextResponse.next();


  if (requestPath.startsWith("/login")) {

    // access_token이 유효한 경우에만 /login에서 대시보드로 보낸다(스테일 refresh_token 루프 방지)
    if (hasValidAccessToken) {
      const res = NextResponse.redirect(new URL("/dashboard", req.url));
      res.cookies.set(NX_COOKIE, "", { path: "/", maxAge: 0 });
      res.cookies.set(AUTH_REASON_COOKIE, "", { path: "/", maxAge: 0 });
      return res;
    }

    const nextParam = requestUrlObj.searchParams.get(NEXT_QUERY_PARAM);
    const reasonParam = requestUrlObj.searchParams.get(AUTH_REASON_QUERY_PARAM);
    if (nextParam || reasonParam) {
      const res = NextResponse.redirect(new URL("/login", req.url));
      if (nextParam) {
        res.cookies.set(NX_COOKIE, sanitizeInternalPath(nextParam), {
          path: "/",
          httpOnly: true,
          sameSite: "lax",
          maxAge: 300,
        });
      }
      const safeReason = sanitizeBase64Url(reasonParam);
      if (safeReason) {
        res.cookies.set(AUTH_REASON_COOKIE, safeReason, {
          path: "/",
          httpOnly: true,
          sameSite: "lax",
          maxAge: 60,
        });
      }
      return res;
    }

    // refresh_token만 있고 access_token이 없는/만료된 상태면, 서버에서 access 재발급 후 목적지로 보내준다.
    if (hasAuthCookie) {
      const res = NextResponse.redirect(
        new URL("/api/session/bootstrap", req.url),
      );
      if (req.cookies.get(AUTH_REASON_COOKIE)) {
        res.cookies.set(AUTH_REASON_COOKIE, "", { path: "/", maxAge: 0 });
      }
      return res;
    }

    // login 페이지에서 표시 후 1회성 정리(요청에는 남아있어 SSR에서 읽을 수 있음)
    if (req.cookies.get(AUTH_REASON_COOKIE)) {
      const res = NextResponse.next();
      res.cookies.set(AUTH_REASON_COOKIE, "", { path: "/", maxAge: 0 });
      return res;
    }
    return NextResponse.next();
  }

  if (isQuarantinedPath(requestPath)) {
    return redirectQuarantinedPath(req, { hasAuthCookie, hasValidAccessToken });
  }

  if (requestPath === "/") {
    if (hasValidAccessToken) {
      const res = NextResponse.redirect(new URL("/dashboard", req.url));
      res.cookies.set(NX_COOKIE, "", { path: "/", maxAge: 0 });
      res.cookies.set(AUTH_REASON_COOKIE, "", { path: "/", maxAge: 0 });
      return res;
    }
    if (hasAuthCookie) {
      const res = NextResponse.redirect(
        new URL("/api/session/bootstrap", req.url),
      );
      res.cookies.set(NX_COOKIE, "/dashboard", {
        path: "/",
        httpOnly: true,
        sameSite: "lax",
        maxAge: 300,
      });
      if (req.cookies.get(AUTH_REASON_COOKIE)) {
        res.cookies.set(AUTH_REASON_COOKIE, "", { path: "/", maxAge: 0 });
      }
      return res;
    }
    return NextResponse.redirect(new URL("/dashboard", req.url));
  }


  if (isPublicPath(requestPath)) {
    if (hasAuthCookie && req.cookies.get(NX_COOKIE)) {
      const res = NextResponse.next();
      res.cookies.set(NX_COOKIE, "", { path: "/", maxAge: 0 });
      return res;
    }
    return NextResponse.next();
  }

  // 보호 경로에서 access_token이 없거나 만료됐지만 refresh_token이 있으면
  // 서버에서 access 재발급 후 원래 경로로 복귀한다(SSR 401 깜빡임/에러 감소).
  if (hasAuthCookie && !hasValidAccessToken) {
    const res = NextResponse.redirect(
      new URL("/api/session/bootstrap", req.url),
    );
    const nextValue = sanitizeInternalPath(requestPath + (requestUrlObj.search || ""));
    res.cookies.set(NX_COOKIE, nextValue, {
      path: "/",
      httpOnly: true,
      sameSite: "lax",
      maxAge: 300,
    });
    if (req.cookies.get(AUTH_REASON_COOKIE)) {
      res.cookies.set(AUTH_REASON_COOKIE, "", { path: "/", maxAge: 0 });
    }
    return res;
  }

  if (!hasAuthCookie) {
    const res = NextResponse.redirect(new URL("/login", req.url));
    const nextValue = sanitizeInternalPath(requestPath + (requestUrlObj.search || ""));

    res.cookies.set(NX_COOKIE, nextValue, {
      path: "/",
      httpOnly: true,
      sameSite: "lax",
      maxAge: 300,
    });
    return res;
  }
  const res = NextResponse.next();
  if (req.cookies.get(NX_COOKIE)) {
    res.cookies.set(NX_COOKIE, "", { path: "/", maxAge: 0 });
  }
  return res;
}

export const config = {

  // 모든 페이지에 적용하되 Next 내부/정적/파비콘 등은 제외
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico|.*\\.).*)"],
};
