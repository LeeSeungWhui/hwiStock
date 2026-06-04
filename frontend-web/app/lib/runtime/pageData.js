/**
 * 파일명: pageData.js
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: PAGE_CONFIG(MODE/INIT_API/API) 기반 페이지 초기 데이터 자동 로딩 유틸
 */

import { apiJSON } from "@/app/lib/runtime/api";

const SSR_MODE = "SSR";
const CSR_MODE = "CSR";

/**
 * @description 값이 plain object인지 판별
 * 처리 규칙: `null` 제외 object 타입이며 배열이 아니면 true 반환.
 * @param {unknown} value
 * @returns {boolean}
 */
const isPlainObject = (value) => (
  Boolean(value)
  && typeof value === "object"
  && !Array.isArray(value)
);

/**
 * @description 페이지 MODE 문자열 정규화
 * 처리 규칙: 대문자 `SSR`만 SSR로 인정하고 나머지는 CSR로 보정.
 * @param {string} mode
 * @returns {"SSR"|"CSR"}
 */
const normalizeMode = (mode) => {
  const normalizedMode = String(mode || "").toUpperCase();
  return normalizedMode === SSR_MODE ? SSR_MODE : CSR_MODE;
};

/**
 * @description PAGE_CONFIG의 API 맵 정규화
 * 처리 규칙: `INIT_API`/`API` 필드를 각각 object 맵으로 정규화한다.
 * @param {Object} pageConfig
 * @param {"INIT_API"|"API"} configKey
 * @returns {Object}
 */
const normalizeApiMap = (pageConfig, configKey) => {
  const apiMap = pageConfig?.[configKey] ?? {};
  if (!isPlainObject(apiMap)) return {};
  return { ...apiMap };
};

/**
 * @description API 엔드포인트 스펙 정규화
 * 처리 규칙: string은 GET 경로로 해석하고 object는 path/method/body/options 병합.
 * @param {string|Object} endpoint
 * @returns {Object|null}
  */
const normalizeEndpointSpec = (endpoint) => {
  if (typeof endpoint === "string") {
    const endpointPath = String(endpoint || "").trim();
    if (!endpointPath) return null;
    return {
      path: endpointPath,
      method: "GET",
      body: undefined,
      fetchInit: {},
      options: {},
    };
  }
  if (!isPlainObject(endpoint)) return null;
  let initConfig = {};
  if (isPlainObject(endpoint.init)) {
    initConfig = endpoint.init;
  } else if (isPlainObject(endpoint.fetchInit)) {
    initConfig = endpoint.fetchInit;
  }
  const endpointPath = String(endpoint.path ?? "").trim();
  if (!endpointPath) return null;
  const endpointMethod = String(
    endpoint.method ?? initConfig.method ?? "GET",
  ).toUpperCase();
  const hasBody = Object.prototype.hasOwnProperty.call(endpoint, "body")
    || Object.prototype.hasOwnProperty.call(initConfig, "body");
  const endpointBody = Object.prototype.hasOwnProperty.call(endpoint, "body")
    ? endpoint.body
    : initConfig.body;
  const restInitObj = { ...initConfig };
  delete restInitObj.method;
  delete restInitObj.body;
  delete restInitObj.authless;
  delete restInitObj.path;
  const endpointOptionsObj = {};
  const authless = Object.prototype.hasOwnProperty.call(endpoint, "authless")
    ? endpoint.authless
    : initConfig.authless;
  if (typeof authless === "boolean") endpointOptionsObj.authless = authless;
  return {
    path: endpointPath,
    method: endpointMethod,
    body: hasBody ? endpointBody : undefined,
    fetchInit: { ...restInitObj },
    options: endpointOptionsObj,
  };
};

/**
 * @description PAGE_CONFIG 기본 구조 정규화
 * 처리 규칙: MODE/INIT_API/API만 남긴 최소 구조로 변환해 반환.
 * @param {Object} pageConfig
 * @returns {{MODE:"SSR"|"CSR", INIT_API:Object, API:Object}}
 */
export const normalizePageConfig = (pageConfig = {}) => ({
  MODE: normalizeMode(pageConfig?.MODE),
  INIT_API: normalizeApiMap(pageConfig, "INIT_API"),
  API: normalizeApiMap(pageConfig, "API"),
});

/**
 * @description MODE가 SSR인지 판별
 * @param {string} mode
 * @returns {boolean}
 */
export const isSsrMode = (mode) => normalizeMode(mode) === SSR_MODE;

/**
 * @description PAGE_CONFIG에서 API 엔트리 목록 추출
 * 처리 규칙: 유효 path가 있는 엔트리만 `[apiKey, spec]` 배열로 반환.
 * @param {Object} pageConfig
 * @param {"INIT_API"|"API"} [configKey]
 * @returns {Array<[string, Object]>}
 */
export const listPageApiEntries = (pageConfig = {}, configKey = "INIT_API") => {
  const normalizedConfig = normalizePageConfig(pageConfig);
  const apiEntryList = [];
  Object.entries(normalizedConfig[configKey] || {}).forEach(([apiKey, endpointSpec]) => {
    const normalizedSpec = normalizeEndpointSpec(endpointSpec);
    if (!normalizedSpec) return;
    apiEntryList.push([apiKey, normalizedSpec]);
  });
  return apiEntryList;
};

/**
 * @description PAGE_CONFIG 초기 자동 로딩 엔트리 일괄 조회
 * 처리 규칙: Promise.allSettled로 INIT_API 전체 호출 후 dataObj/errorObj 분리 반환.
 * @param {Object} params
 * @param {Object} params.pageConfig
 * @param {Function} [params.fetcher]
 * @returns {Promise<{dataObj:Object, errorObj:Object, hasError:boolean}>}
 */
export const loadPageDataObj = async ({
  pageConfig,
  fetcher = apiJSON,
}) => {
  const apiEntryList = listPageApiEntries(pageConfig, "INIT_API");
  if (!apiEntryList.length) {
    return {
      dataObj: {},
      errorObj: {},
      hasError: false,
    };
  }
  const settledResultList = await Promise.allSettled(
    apiEntryList.map(([, endpointSpec]) => {
      const requestInitObj = {
        ...endpointSpec.fetchInit,
        method: endpointSpec.method,
      };
      if (typeof endpointSpec.body !== "undefined") {
        requestInitObj.body = endpointSpec.body;
      }
      if (Object.keys(endpointSpec.options || {}).length > 0) {
        return fetcher(endpointSpec.path, requestInitObj, endpointSpec.options);
      }
      return fetcher(endpointSpec.path, requestInitObj);
    }),
  );
  const dataObj = {};
  const errorObj = {};
  settledResultList.forEach((settledResult, index) => {
    const [apiKey] = apiEntryList[index];
    if (settledResult.status === "fulfilled") {
      dataObj[apiKey] = settledResult.value;
      return;
    }
    errorObj[apiKey] = {
      message: settledResult.reason?.message || "INIT_FETCH_FAILED",
      code: settledResult.reason?.code,
      requestId: settledResult.reason?.requestId,
      statusCode: settledResult.reason?.statusCode,
    };
  });
  return {
    dataObj,
    errorObj,
    hasError: Object.keys(errorObj).length > 0,
  };
};

/**
 * @description SSR 모드 전용 서버 초기 데이터 로딩
 * 처리 규칙: SSR이 아니면 빈 맵 반환, SSR이면 INIT_API 맵만 일괄 조회.
 * @param {Object} params
 * @param {Object} params.pageConfig
 * @param {Function} [params.fetcher]
 * @returns {Promise<{mode:"SSR"|"CSR", dataObj:Object, errorObj:Object, hasError:boolean}>}
 */
export const loadServerPageData = async ({
  pageConfig,
  fetcher = apiJSON,
}) => {
  const normalizedConfig = normalizePageConfig(pageConfig);
  if (!isSsrMode(normalizedConfig.MODE)) {
    return {
      mode: normalizedConfig.MODE,
      dataObj: {},
      errorObj: {},
      hasError: false,
    };
  }
  const loadResult = await loadPageDataObj({
    pageConfig: normalizedConfig,
    fetcher,
  });
  return {
    mode: normalizedConfig.MODE,
    ...loadResult,
  };
};
