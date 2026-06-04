/**
 * 파일명: openapiClient.js
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: OpenAPI 스키마(/openapi.json) 기반 JS 클라이언트 유틸. 실제 요청은 apiRequest/apiJSON에 위임
 */

import { apiJSON, apiRequest } from "@/app/lib/runtime/api";

let cachedOpenApi = null;
let cachedOpenApiPromise = null;

/**
 * @description `/openapi. json` 스키마를 로드해 openapi-client-axios 인스턴스를 초기화
 * 실패 동작: 스키마가 객체가 아니거나 라이브러리 로딩 실패 시 Error를 던진다.
 * @updated 2026-02-27
 */
const loadOpenApiClient = async () => {
  const openapiSpecObj = await apiJSON(
    "/openapi.json",
    { method: "GET" },
    { authless: true },
  );
  if (!openapiSpecObj || typeof openapiSpecObj !== "object") {
    throw new Error("Invalid OpenAPI schema");
  }

  const openapiModuleObj = await import("openapi-client-axios");
  const OpenAPIClientAxios = openapiModuleObj?.default || openapiModuleObj?.OpenAPIClientAxios;
  if (typeof OpenAPIClientAxios !== "function") {
    throw new Error("openapi-client-axios not available");
  }

  // 요청 실행은 apiRequest/apiJSON에 위임하므로, 여기서는 스키마 파싱/요청 구성만 사용한다.
  const openapiClientObj = new OpenAPIClientAxios({ definition: openapiSpecObj, quick: true });
  openapiClientObj.initSync();
  return openapiClientObj;
}

/**
 * @description OpenAPI 클라이언트를 캐시 기반으로 단일 인스턴스로 반환. 입력/출력 계약을 함께 명시
 * 처리 규칙: 초기 로딩 중에는 Promise 캐시를 공유해 중복 초기화를 방지한다.
 * @updated 2026-02-27
 */
const getOpenApiClient = async () => {
  if (cachedOpenApi) return cachedOpenApi;
  if (!cachedOpenApiPromise) {
    cachedOpenApiPromise = loadOpenApiClient()
      .then((client) => {
        cachedOpenApi = client;
        return client;
      })
      .finally(() => {
        cachedOpenApiPromise = null;
      });
  }
  return cachedOpenApiPromise;
}

/**
 * @description query params 객체를 URLSearchParams 문자열로 직렬화
 * 처리 규칙: null/undefined 키는 제외하고 배열 값은 같은 키로 반복 append 한다.
 * @updated 2026-02-27
 */
const buildQueryString = (queryParamObj) => {
  if (!queryParamObj || typeof queryParamObj !== "object") return "";
  const querySearchParams = new URLSearchParams();
  for (const [paramKey, paramValue] of Object.entries(queryParamObj)) {
    if (!paramKey) continue;
    if (paramValue == null) continue;
    if (Array.isArray(paramValue)) {
      for (const paramItem of paramValue) {
        if (paramItem == null) continue;
        querySearchParams.append(paramKey, String(paramItem));
      }
      continue;
    }
    querySearchParams.append(paramKey, String(paramValue));
  }
  return querySearchParams.toString();
}

/**
 * @description 기존 URL과 query string 병합 기반 최종 요청 URL 생성
 * 반환값: 파라미터가 없으면 원본 URL, 있으면 `?` 또는 `&`가 반영된 URL.
 * @updated 2026-02-27
 */
const mergeUrlAndParams = (requestUrl, queryParamObj) => {
  const baseUrl = typeof requestUrl === "string" ? requestUrl : String(requestUrl || "");
  const queryText = buildQueryString(queryParamObj);
  if (!queryText) return baseUrl;
  return baseUrl.includes("?") ? `${baseUrl}&${queryText}` : `${baseUrl}?${queryText}`;
}

/**
 * 설명: OpenAPI operationId 기반 요청을 구성해 fetch(Request) 경로로 위임
 * 반환값: apiRequest가 반환하는 fetch Response 객체.
 * 갱신일: 2026-03-02
 */
export const openapiRequest = async (
  operationId,
  operationParamObj = null,
  requestBodyObj = null,
  operationConfigObj = {},

) => {
  const openapiClientObj = await getOpenApiClient();
  const operationObj = openapiClientObj.getOperation?.(operationId);
  if (!operationObj) {
    throw new Error(
      `Unknown OpenAPI operationId: ${String(operationId || "")}`,
    );
  }
  const axiosConfig = openapiClientObj.getAxiosConfigForOperation(operationId, [
    operationParamObj,
    requestBodyObj,
    operationConfigObj,
  ]);
  const requestMethod = String(axiosConfig?.method || "GET").toUpperCase();
  const requestUrl = mergeUrlAndParams(axiosConfig?.url, axiosConfig?.params);
  const axiosHeaderObj = axiosConfig?.headers || {};
  const authless = Boolean(axiosConfig?.authless);
  return apiRequest(
    requestUrl,
    { method: requestMethod, headers: axiosHeaderObj, body: axiosConfig?.data },
    { authless },
  );
}

/**
 * 설명: OpenAPI operationId 기반으로 JSON(표준 응답 스키마) 호출을 수행(apiJSON 규약 동일)
 * 반환값: apiJSON 규약의 JSON 객체(success/result/code/message/requestId 등).
 * 갱신일: 2026-03-02
 */
export const openapiJSON = async (
  operationId,
  operationParamObj = null,
  requestBodyObj = null,
  operationConfigObj = {},

) => {
  const openapiClientObj = await getOpenApiClient();
  const operationObj = openapiClientObj.getOperation?.(operationId);
  if (!operationObj) {
    throw new Error(
      `Unknown OpenAPI operationId: ${String(operationId || "")}`,
    );
  }
  const axiosConfig = openapiClientObj.getAxiosConfigForOperation(operationId, [
    operationParamObj,
    requestBodyObj,
    operationConfigObj,
  ]);
  const requestMethod = String(axiosConfig?.method || "GET").toUpperCase();
  const requestUrl = mergeUrlAndParams(axiosConfig?.url, axiosConfig?.params);
  const axiosHeaderObj = axiosConfig?.headers || {};
  const authless = Boolean(axiosConfig?.authless);
  return apiJSON(
    requestUrl,
    { method: requestMethod, headers: axiosHeaderObj, body: axiosConfig?.data },
    { authless },
  );
}
