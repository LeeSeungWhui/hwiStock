/**
 * 파일명: api.js
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: SSR/CSR 공통 API 호출 유틸 (isomorphic)
 */

import {
  parseJsonPayload,
  normalizeNestedJsonFields,
} from "@/app/lib/runtime/jsonPayload";
import {
  AUTH_REASON_MAXLEN,
  AUTH_REASON_QUERY_PARAM,
  NEXT_QUERY_PARAM,
  base64UrlEncodeUtf8,
  extractUnauthorizedReason,
} from "@/app/lib/runtime/authRedirect";

const BFF_PREFIX = "/api/bff";
const EMPTY_BODY_STATUS = new Set([204, 205, 304]);
const LOGIN_PATH = "/login";

/**
 * @description PAGE_CONFIG 엔드포인트 object 여부를 판별
 * 처리 규칙: plain object이면서 path 키가 있으면 PAGE_CONFIG 엔트리로 간주한다.
 * @updated 2026-03-12
 */
const isEndpointLike = (value) => {
  if (!isPlainObject(value)) return false;
  return Object.prototype.hasOwnProperty.call(value, "path");
};

/**
 * @description 테스트 실행 환경 여부를 확인
 * 처리 규칙: `VITEST` 또는 `NODE_ENV=test` 플래그를 우선 읽고 예외 발생 시 false를 반환한다.
 * @updated 2026-02-27
 */
const isTestEnv = () => {
  try {
    return Boolean(process?.env?.VITEST || process?.env?.NODE_ENV === "test");
  } catch {
    return false;
  }
};

/**
 * @description 입력 경로가 절대 URL인지 판별
 * 처리 규칙: 문자열이면서 `http://` 또는 `https://` 프리픽스를 가지면 true를 반환한다.
 * @updated 2026-02-27
 */
const isAbsoluteUrl = (input) => {
  if (typeof input !== "string") return false;
  return /^https?:\/\//i.test(input);
};

/**
 * @description 애플리케이션 경로를 BFF 프록시 경로로 정규화. 입력/출력 계약을 함께 명시
 * 처리 규칙: 이미 `/api/bff`로 시작하면 유지하고, 아니면 prefix를 붙여 반환한다.
 * @updated 2026-02-27
 */
const toBffPath = (path) => {
  const normalizedPath = String(path || "");
  if (normalizedPath.startsWith(BFF_PREFIX)) return normalizedPath;
  return `${BFF_PREFIX}${normalizedPath.startsWith("/") ? normalizedPath : `/${normalizedPath}`}`;
};

/**
 * @description Request body로 직접 전달 가능한 타입인지 검사
 * 처리 규칙: string/FormData/Blob/ArrayBuffer 타입을 body-like 값으로 인정한다.
 * @updated 2026-02-27
 */
const isBodyLike = (value) => {
  return (
    typeof value === "string" ||
    (typeof FormData !== "undefined" && value instanceof FormData) ||
    (typeof Blob !== "undefined" && value instanceof Blob) ||
    (typeof ArrayBuffer !== "undefined" && value instanceof ArrayBuffer)
  );
};

/**
 * @description body 값이 FormData인지 판별
 * 처리 규칙: 브라우저 환경에서 `instanceof FormData`일 때만 true를 반환한다.
 * @updated 2026-02-27
 */
const isFormBody = (value) => {
  return typeof FormData !== "undefined" && value instanceof FormData;
};

/**
 * @description body 값이 바이너리 타입인지 판별
 * 처리 규칙: `Blob` 또는 `ArrayBuffer` 인스턴스면 true를 반환한다.
 * @updated 2026-02-27
 */
const isBinaryBody = (value) => {
  return (
    (typeof Blob !== "undefined" && value instanceof Blob) ||
    (typeof ArrayBuffer !== "undefined" && value instanceof ArrayBuffer)
  );
};

/**
 * @description 요청 body 입력을 전송 가능한 값으로 직렬화
 * 처리 규칙: body-like 값은 그대로 사용하고, 일반 객체는 JSON 문자열로 변환한다.
 * @updated 2026-02-27
 */
const serializeBody = (input) => {
  if (input == null) return undefined;
  if (isBodyLike(input)) return input;


  try {
    return typeof input === "string" ? input : JSON.stringify(input);
  } catch {

    try {

      return JSON.stringify(JSON.parse(JSON.stringify(input)));
    } catch {
      return JSON.stringify({});
    }
  }
};

/**
 * @description api 호출 인자 오버로딩 패턴을 단일 포맷으로 정규화. 입력/출력 계약을 함께 명시
 * 처리 규칙: `(path, init|body, mode|options)` 입력을 `{ path, init, options }` 형태로 통일한다.
 * @updated 2026-02-27
 */
const normalizeArgs = (path, initOrBody, modeOrOptions) => {

  /**
   * @description 값이 RequestInit 유사 객체인지 판별
   * 처리 규칙: body-like 값은 제외하고, method/headers/body/authless 키 보유 여부로 판별한다.
   * @updated 2026-02-27
   */
  const isInitLike = (value) => {
    if (!value || typeof value !== "object") return false;
    if (isBodyLike(value)) return false;
    const valueKeyList = Object.keys(value);
    return (
      "method" in value ||
      "headers" in value ||
      "body" in value ||
      "authless" in value ||
      valueKeyList.length === 0
    );
  };

  const endpointPath = isEndpointLike(path)
    ? String(path.path || "")
    : String(path || "");
  let endpointInitObj = {};
  if (isEndpointLike(path)) {
    if (isPlainObject(path.init)) {
      endpointInitObj = { ...path.init };
    } else if (isPlainObject(path.fetchInit)) {
      endpointInitObj = { ...path.fetchInit };
    }
  }
  let requestInitObj = { ...endpointInitObj };
  let requestOptionsObj = {};

  /**
   * @description 모드 문자열을 요청 options 객체에 반영
   * 처리 규칙: 현재는 `authless` 모드만 해석해 `requestOptionsObj.authless=true`로 설정한다.
   * @updated 2026-02-27
   */
  const applyMode = (mode) => {
    if (!mode) return;
    if (mode === "authless") requestOptionsObj.authless = true;
  };

  if (isEndpointLike(path)) {
    if (Object.prototype.hasOwnProperty.call(path, "method")) {
      requestInitObj.method = path.method;
    }
    if (Object.prototype.hasOwnProperty.call(path, "body")) {
      requestInitObj.body = path.body;
    }
    if (typeof path.authless === "boolean") {
      requestOptionsObj.authless = path.authless;
    }
  }

  if (typeof initOrBody === "string") applyMode(initOrBody);
  else if (isInitLike(initOrBody)) requestInitObj = { ...requestInitObj, ...initOrBody };
  else if (typeof initOrBody !== "undefined") {
    requestInitObj = { ...requestInitObj, method: requestInitObj.method || "POST", body: initOrBody };
  }

  if (typeof modeOrOptions === "string") applyMode(modeOrOptions);
  else if (modeOrOptions && typeof modeOrOptions === "object") {
    const { authless, ...remainingInitObj } = modeOrOptions;
    if (typeof authless === "boolean") requestOptionsObj.authless = authless;
    if (Object.keys(remainingInitObj).length) requestInitObj = { ...requestInitObj, ...remainingInitObj };
  }

  if (typeof requestInitObj.authless === "boolean") {
    requestOptionsObj.authless = requestInitObj.authless;
    delete requestInitObj.authless;
  }

  return { path: endpointPath, init: requestInitObj, options: requestOptionsObj };
};

/**
 * @description 헤더 집합에 대상 헤더가 존재하는지 검사
 * 처리 규칙: `Headers` 인스턴스와 plain object 양쪽을 지원하며 키 비교는 소문자로 수행한다.
 * @updated 2026-02-27
 */
const hasHeader = (headers, name) => {
  if (!headers) return false;
  const headerNameLower = String(name || "").toLowerCase();
  if (!headerNameLower) return false;
  if (headers instanceof Headers) {
    return headers.has(headerNameLower);
  }
  return Object.keys(headers).some((headerKey) => String(headerKey).toLowerCase() === headerNameLower);
};

/**
 * 응답 본문을 안전하게 텍스트로 변환
 * @param {Response} response fetch Response 객체
 * @returns {Promise<string>} 본문 텍스트
 * @description Response 본문 안전 텍스트 조회
 * 처리 규칙: 빈 본문 상태코드(204/205/304)는 즉시 빈 문자열을 반환하고 읽기 실패도 빈 문자열로 수렴한다.
 * @updated 2026-02-27
 */
const readResponseText = async (response) => {
  if (!response || typeof response.text !== "function") return "";
  if (EMPTY_BODY_STATUS.has(response.status)) return "";
  try {
    return await response.text();
  } catch {
    return "";
  }
};

/**
 * 백엔드 JSON 문자열을 보정/정규화
 * @param {Response} response fetch Response
 * @returns {Promise<object|null>} 파싱 결과
 * @description 응답 JSON 문자열을 파싱하고 중첩 JSON 문자열 필드를 정규화. 입력/출력 계약을 함께 명시
 * 처리 규칙: 파싱 실패 시 원문 텍스트를 노출하지 않는 SyntaxError를 던진다.
 * @updated 2026-02-27
 */
const parseJsonResponseBody = async (response) => {
  const rawText = await readResponseText(response);
  if (!rawText) return null;
  const parsed = parseJsonPayload(rawText, { context: "apiJSON" });
  if (!parsed) {
    const syntaxError = new SyntaxError("Invalid JSON response");
    syntaxError.name = "ApiParseError";
    syntaxError.statusCode = response?.status;
    throw syntaxError;
  }
  return normalizeNestedJsonFields(parsed);
};

/**
 * @description 값이 배열이 아닌 일반 객체인지 판별
 * 처리 규칙: null/array를 제외한 object 타입만 true를 반환한다.
 * @updated 2026-02-27
 */
const isPlainObject = (value) => {
  if (!value || typeof value !== "object") return false;
  if (Array.isArray(value)) return false;
  return true;
};

/**
 * @description API 실패 응답을 표준 ApiError 객체로 변환. 입력/출력 계약을 함께 명시
 * 처리 규칙: body의 message/code/requestId를 우선 사용하고, 없으면 상태코드 기반 기본 메시지를 구성한다.
 * @updated 2026-02-27
 */
const createApiError = (path, response, body) => {
  const message =
    (isPlainObject(body) && typeof body.message === "string" && body.message) ||
    `API request failed (${response?.status || "unknown"})`;

  const apiErrorObj = new Error(message);
  apiErrorObj.name = "ApiError";
  apiErrorObj.statusCode = response?.status;
  apiErrorObj.code = isPlainObject(body) ? body.code : undefined;
  apiErrorObj.requestId = isPlainObject(body) ? body.requestId : undefined;
  apiErrorObj.path = typeof path === "string" ? path : String(path || "");
  return apiErrorObj;
};

/**
 * @description SSR/CSR 공통 규약으로 Request 기반 API 응답(Response)을 반환. 입력/출력 계약을 함께 명시
 * @param {string} path
 * @param {Object} [initOrBody]
 * @param {string|Object} [modeOrOptions]
 * @returns {Promise<Response>}
 */
export const apiRequest = async (path, initOrBody = {}, modeOrOptions) => {

  const { path: requestPath, init: requestInitObj, options: requestOptionsObj } = normalizeArgs(path, initOrBody, modeOrOptions);
  const requestMethod = (requestInitObj.method || "GET").toUpperCase();
  const headersIn = requestInitObj.headers || {};
  const absoluteUrl = isAbsoluteUrl(requestPath);
  const authless = Boolean(requestOptionsObj?.authless);

  /**
   * @description SSR에서 사용할 프론트엔드 origin을 결정
   * 처리 규칙: 환경변수 값을 우선 사용하고 없으면 `http://127.0.0.1:<PORT>` 기본값을 반환한다.
   * @updated 2026-02-27
   */
  const resolveFrontendOrigin = () => {
    const envOrigin =
      process.env.APP_FRONTEND_ORIGIN ||
      process.env.FRONTEND_ORIGIN ||
      process.env.NEXT_PUBLIC_SITE_URL ||
      process.env.VERCEL_URL;
    if (envOrigin) {
      return envOrigin.startsWith("http") ? envOrigin : `https://${envOrigin}`;
    }
    const port = process.env.PORT || 5000;
    return `http://127.0.0.1:${port}`;
  };

  if (typeof window === "undefined") {
    const { buildSSRHeaders } = await import("@/app/lib/runtime/ssr");
    const baseHeaderObj = { ...headersIn };
    if (
      requestMethod !== "GET" &&
      requestMethod !== "HEAD" &&
      !hasHeader(baseHeaderObj, "content-type")
    ) {
      if (!(isFormBody(requestInitObj.body) || isBinaryBody(requestInitObj.body))) {
        baseHeaderObj["Content-Type"] = "application/json";
      }
    }
    const ssrHeaders = await buildSSRHeaders(baseHeaderObj);
    const serializedBodyText = serializeBody(requestInitObj.body);
    const ssrFetchInitObj = {
      method: requestMethod,
      credentials: "include",
      headers: ssrHeaders,
      cache: "no-store",
    };
    if (
      requestMethod !== "GET" &&
      requestMethod !== "HEAD" &&
      typeof serializedBodyText !== "undefined"
    ) {
      ssrFetchInitObj.body = serializedBodyText;
    }
    const targetUrl = absoluteUrl
      ? requestPath
      : new URL(toBffPath(requestPath), resolveFrontendOrigin());

    return fetch(targetUrl, ssrFetchInitObj);
  }


  const targetUrl = absoluteUrl ? requestPath : toBffPath(requestPath);
  const clientHeaderObj = { ...headersIn };

  if (!hasHeader(clientHeaderObj, "accept-language"))
    clientHeaderObj["Accept-Language"] = navigator.language || "en";
  if (
    requestMethod !== "GET" &&
    requestMethod !== "HEAD" &&
    !hasHeader(clientHeaderObj, "content-type")
  ) {
    if (!(isFormBody(requestInitObj.body) || isBinaryBody(requestInitObj.body))) {
      clientHeaderObj["Content-Type"] = "application/json";
    }
  }

  const clientFetchInitObj = {
    method: requestMethod,
    credentials: "include",
    headers: clientHeaderObj,
  };
  if (requestMethod !== "GET" && requestMethod !== "HEAD") {
    clientFetchInitObj.body = serializeBody(requestInitObj.body) ?? "{}";
  }

  const apiResponse = await fetch(targetUrl, clientFetchInitObj);
  if (apiResponse.status !== 401) return apiResponse;

  const { pathname, search } = window.location;
  const isOnLogin = pathname.startsWith(LOGIN_PATH);
  const nextPath = pathname + (search || "");
  const reason = await extractUnauthorizedReason(apiResponse);
  const reasonEncoded = reason
    ? base64UrlEncodeUtf8(JSON.stringify(reason))
    : null;
  const reasonQuery =
    reasonEncoded && reasonEncoded.length <= AUTH_REASON_MAXLEN
      ? `&${AUTH_REASON_QUERY_PARAM}=${encodeURIComponent(reasonEncoded)}`
      : "";
  const redirectTo = `${LOGIN_PATH}?${NEXT_QUERY_PARAM}=${encodeURIComponent(nextPath)}${reasonQuery}`;
  if (!authless && !isOnLogin) {
    if (!isTestEnv()) {
      try {
        window.location.assign(redirectTo);
      } catch {

        // navigation 실패는 무시(테스트/특수 환경)
      }
    }
    const unauthorizedErrorObj = new Error("UNAUTHORIZED");
    unauthorizedErrorObj.name = "UnauthorizedError";
    unauthorizedErrorObj.redirectTo = redirectTo;
    throw unauthorizedErrorObj;
  }
  return apiResponse;
};

/**
 * @description API 응답을 JSON으로 파싱하고 실패 응답을 ApiError로 전환
 * 처리 규칙: HTTP 비정상(`!ok`) 또는 body.status=false 모두 예외로 승격한다.
 * @param {string} path
 * @param {Object} [initOrBody]
 * @param {string|Object} [modeOrOptions]
 * @returns {Promise<any>}
 */
export const apiJSON = async (path, initOrBody = {}, modeOrOptions) => {
  const normalizedArgs = normalizeArgs(path, initOrBody, modeOrOptions);
  const apiResponse = await apiRequest(path, initOrBody, modeOrOptions);
  const responseBodyObj = await parseJsonResponseBody(apiResponse);
  if (!apiResponse?.ok) {
    throw createApiError(normalizedArgs.path, apiResponse, responseBodyObj);
  }
  if (isPlainObject(responseBodyObj) && responseBodyObj.status === false) {
    throw createApiError(normalizedArgs.path, apiResponse, responseBodyObj);
  }
  return responseBodyObj;
};

/**
 * @description JSON API 래퍼를 제공
 * 처리 규칙: init에 method를 강제로 `GET`으로 주입해 `apiJSON`으로 위임한다.
 * @returns {Promise<any>} JSON 응답 페이로드
 */
export const apiGet = (path, requestInitObj = {}) => {

  return apiJSON(path, { ...requestInitObj, method: "GET" });
};

/**
 * @description JSON API 래퍼를 제공
 * 처리 규칙: 전달 body를 포함해 method=`POST`로 고정한 뒤 `apiJSON`으로 위임한다.
 * @returns {Promise<any>} JSON 응답 페이로드
 */
export const apiPost = (path, body, requestInitObj = {}) => {

  return apiJSON(path, { ...requestInitObj, method: "POST", body });
};

/**
 * @description JSON API 래퍼를 제공
 * 처리 규칙: 전달 body를 포함해 method=`PUT`으로 고정한 뒤 `apiJSON`으로 위임한다.
 * @returns {Promise<any>} JSON 응답 페이로드
 */
export const apiPut = (path, body, requestInitObj = {}) => {

  return apiJSON(path, { ...requestInitObj, method: "PUT", body });
};

/**
 * @description JSON API 래퍼를 제공
 * 처리 규칙: 전달 body를 포함해 method=`PATCH`로 고정한 뒤 `apiJSON`으로 위임한다.
 * @returns {Promise<any>} JSON 응답 페이로드
 */
export const apiPatch = (path, body, requestInitObj = {}) => {

  return apiJSON(path, { ...requestInitObj, method: "PATCH", body });
};

/**
 * @description JSON API 래퍼를 제공
 * 처리 규칙: 전달 body를 포함해 method=`DELETE`로 고정한 뒤 `apiJSON`으로 위임한다.
 * @returns {Promise<any>} JSON 응답 페이로드
 */
export const apiDelete = (path, body, requestInitObj = {}) => {

  return apiJSON(path, { ...requestInitObj, method: "DELETE", body });
};
