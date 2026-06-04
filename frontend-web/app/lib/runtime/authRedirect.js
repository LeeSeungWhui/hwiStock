/**
 * 파일명: authRedirect.js
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: next(nx) 경로 sanitize + auth_reason(base64url JSON) 인코딩/디코딩 공용 유틸(SSR/CSR/미들웨어 공통)
 */

import { parseJsonPayload } from "@/app/lib/runtime/jsonPayload";

export const DEFAULT_NEXT_PATH = "/dashboard";
export const NX_COOKIE = "nx";
export const NEXT_QUERY_PARAM = "next";
export const AUTH_REASON_COOKIE = "auth_reason";
export const AUTH_REASON_QUERY_PARAM = "reason";
export const AUTH_REASON_MAXLEN = 900;

/**
 * 설명: 내부 경로(절대 경로)만 허용하고, 아니면 fallback을 반환
 * 갱신일: 2026-05-23
 */
export const sanitizeInternalPath = (candidate, defaultPath = DEFAULT_NEXT_PATH) => {
  if (!candidate || typeof candidate !== "string") return defaultPath;
  if (!candidate.startsWith("/")) return defaultPath;
  if (candidate.startsWith("//")) return defaultPath;
  return candidate;
}

/**
 * 설명: cookie/query 값이 URL 인코딩된 경우 안전하게 디코딩
 * 갱신일: 2026-05-23
 */
export const decodeUriComponentValue = (value) => {
  if (typeof value !== "string") return null;
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

/**
 * 설명: base64url 문자셋/길이 규칙 검증과 허용 토큰 통과
 * 갱신일: 2026-05-23
 */
export const sanitizeBase64Url = (value, maxLen = AUTH_REASON_MAXLEN) => {
  if (!value || typeof value !== "string") return null;
  if (maxLen && value.length > maxLen) return null;
  if (!/^[A-Za-z0-9_-]+$/.test(value)) return null;
  return value;
}

/**
 * 설명: UTF-8 문자열을 base64url로 인코딩(브라우저/Node/테스트 환경 호환)
 * 갱신일: 2026-05-23
 */
export const base64UrlEncodeUtf8 = (text) => {
  if (typeof text !== "string") return null;
  try {
    if (typeof TextEncoder !== "undefined" && typeof btoa === "function") {
      const bytes = new TextEncoder().encode(text);
      let binary = "";
      const chunkSize = 0x8000;
      for (let byteIndex = 0; byteIndex < bytes.length; byteIndex += chunkSize) {
        const chunk = bytes.subarray(byteIndex, byteIndex + chunkSize);
        binary += String.fromCharCode(...chunk);
      }
      const base64 = btoa(binary);
      return base64.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
    }
  } catch {

  }
  try {
    if (typeof Buffer !== "undefined") {
      return Buffer.from(text, "utf8")
        .toString("base64")
        .replace(/\+/g, "-")
        .replace(/\//g, "_")
        .replace(/=+$/g, "");
    }
  } catch {

    // 무시
  }
  return null;
}

/**
 * 설명: base64url(UTF-8) 문자열을 디코딩(브라우저/Edge/Node 호환)
 * 갱신일: 2026-05-23
 */
export const base64UrlDecodeUtf8 = (input) => {
  if (!input || typeof input !== "string") return null;
  const authReasonToken = sanitizeBase64Url(input, 0);
  if (!authReasonToken) return null;
  const base64 = authReasonToken.replace(/-/g, "+").replace(/_/g, "/");
  const padded = base64 + "===".slice((base64.length + 3) % 4);

  try {
    if (typeof atob === "function" && typeof TextDecoder !== "undefined") {
      const binary = atob(padded);
      const bytes = Uint8Array.from(binary, (charValue) =>
        charValue.charCodeAt(0),
      );
      return new TextDecoder().decode(bytes);
    }
  } catch {

  }

  try {
    if (typeof Buffer !== "undefined") {
      return Buffer.from(padded, "base64").toString("utf8");
    }
  } catch {

    // 무시
  }
  return null;
}

/**
 * 설명: null/배열을 제외한 plain object 여부를 판별
 * 갱신일: 2026-05-23
 */
const isPlainObject = (value) => {
  if (!value || typeof value !== "object") return false;
  if (Array.isArray(value)) return false;
  return true;
}

/**
 * 설명: auth_reason(base64url JSON) 안전 파싱으로 code/requestId/message만 반환. 입력/출력 계약 명시
 * 갱신일: 2026-05-23
 */
export const parseAuthReason = (encoded, maxLen = AUTH_REASON_MAXLEN) => {
  const encodedReasonToken = sanitizeBase64Url(encoded, maxLen);
  if (!encodedReasonToken) return null;
  const decodedText = base64UrlDecodeUtf8(encodedReasonToken);
  if (!decodedText) return null;
  try {
    const parsed = JSON.parse(decodedText);
    if (!isPlainObject(parsed)) return null;
    const code = typeof parsed.code === "string" ? parsed.code : null;
    const requestId =
      typeof parsed.requestId === "string" ? parsed.requestId : null;
    const message = typeof parsed.message === "string" ? parsed.message : null;
    const hasAuthReason = code || requestId || message;
    if (!hasAuthReason) return null;
    return {
      ...(code ? { code } : {}),
      ...(requestId ? { requestId } : {}),
      ...(message ? { message } : {}),
    };
  } catch {
    return null;
  }
}

/**
 * 설명: 401 응답 본문에서 code/requestId/message를 추출(JSON만)
 * 갱신일: 2026-05-23
 */
export const extractUnauthorizedReason = async (response) => {
  if (!response || typeof response.clone !== "function") return null;
  try {
    const authErrorText = await response.clone().text();
    const authErrorBodyObj = parseJsonPayload(authErrorText, { context: "AuthReason" });
    if (!isPlainObject(authErrorBodyObj)) return null;
    const code =
      typeof authErrorBodyObj.code === "string" ? authErrorBodyObj.code : null;
    const requestId =
      typeof authErrorBodyObj.requestId === "string"
        ? authErrorBodyObj.requestId
        : null;
    const message =
      typeof authErrorBodyObj.message === "string"
        ? authErrorBodyObj.message
        : null;
    const hasAuthReason = code || requestId || message;
    if (!hasAuthReason) return null;
    return {
      ...(code ? { code } : {}),
      ...(requestId ? { requestId } : {}),
      ...(message ? { message } : {}),
    };
  } catch {
    return null;
  }
}
