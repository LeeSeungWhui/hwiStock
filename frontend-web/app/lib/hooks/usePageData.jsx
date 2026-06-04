"use client";

/**
 * 파일명: usePageData.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: PAGE_CONFIG 기반 페이지 데이터 자동 로딩 훅
 */

import { useCallback, useEffect } from "react";
import EasyObj from "@/app/lib/dataset/EasyObj";
import { apiJSON } from "@/app/lib/runtime/api";
import {
  isSsrMode,
  loadPageDataObj,
  normalizePageConfig,
} from "@/app/lib/runtime/pageData";

const EMPTY_OBJ = {};

/**
 * @description PAGE_CONFIG 기반 자동 로딩 상태 제공
 * 처리 규칙: SSR은 초기값 우선 사용, CSR은 마운트 시 API 자동 호출.
 * @param {Object} params
 * @param {Object} params.pageConfig
 * @param {Object} [params.initialDataObj]
 * @param {Object} [params.initialErrorObj]
 * @param {boolean} [params.auto]
 * @returns {{mode:string, dataObj:Object, errorObj:Object, isLoading:boolean, hasError:boolean, reload:Function}}
 */
export const usePageData = ({
  pageConfig,
  initialDataObj = EMPTY_OBJ,
  initialErrorObj = EMPTY_OBJ,
  auto = true,
}) => {
  const normalizedConfig = normalizePageConfig(pageConfig);
  const ui = EasyObj({
    isLoading: false,
  });
  const dataObj = EasyObj(initialDataObj || EMPTY_OBJ);
  const errorObj = EasyObj(initialErrorObj || EMPTY_OBJ);
  const requestObj = EasyObj({
    sequence: 0,
  });

  /**
   * @description API 엔트리 일괄 로딩 실행
   * 처리 규칙: 가장 마지막 요청(sequence)만 상태에 반영.
   * @returns {Promise<{dataObj:Object, errorObj:Object, hasError:boolean, ignored:boolean}>}
   */
  const load = useCallback(async () => {
    const sequence = Number(requestObj.sequence || 0) + 1;
    requestObj.sequence = sequence;
    ui.isLoading = true;
    const loadResult = await loadPageDataObj({
      pageConfig: normalizedConfig,
      fetcher: apiJSON,
    });
    if (Number(requestObj.sequence || 0) !== sequence) {
      return {
        ...loadResult,
        ignored: true,
      };
    }
    dataObj.copy(loadResult.dataObj || EMPTY_OBJ);
    errorObj.copy(loadResult.errorObj || EMPTY_OBJ);
    ui.isLoading = false;
    return {
      ...loadResult,
      ignored: false,
    };
  }, [normalizedConfig, dataObj, errorObj, requestObj, ui]);

  /**
   * @description 수동 재조회 트리거
   * 처리 규칙: SSR/CSR 모드와 무관하게 동일 로딩 루틴 수행.
   * @returns {Promise<{dataObj:Object, errorObj:Object, hasError:boolean, ignored:boolean}>}
   */
  const reload = async () => {
    try {
      return await load();
    } finally {
      ui.isLoading = false;
    }
  };

  /**
   * @description initialDataObj/initialErrorObj 변경 시 dataObj/errorObj 스냅샷 복사
   * 처리 규칙: pageConfig 초기값이 바뀌면 EasyObj 상태를 동기화한다.
   */
  useEffect(() => {
    dataObj.copy(initialDataObj || EMPTY_OBJ);
    errorObj.copy(initialErrorObj || EMPTY_OBJ);
  }, [initialDataObj, initialErrorObj, dataObj, errorObj]);

  /**
   * @description auto=true일 때 마운트 후 load() 호출 및 ui.isLoading 해제
   * 처리 규칙: unmount 시 isMounted=false로 비동기 완료 반영을 차단한다.
   */
  useEffect(() => {
    if (!auto) return undefined;
    if (isSsrMode(normalizedConfig.MODE)) {
      ui.isLoading = false;
      return undefined;
    }
    let isMounted = true;

    /**
     * @description 자동 로딩 초기 호출 실행
     * 처리 규칙: 마운트 유지 상태에서만 로딩 완료 상태를 반영한다.
     * @returns {Promise<void>}
     */
    const executeAutoLoad = async () => {
      try {
        await load();
      } finally {
        if (!isMounted) return;
        ui.isLoading = false;
      }
    };

    executeAutoLoad();
    return () => {
      isMounted = false;
    };
  }, [auto, pageConfig, load, normalizedConfig.MODE, ui]);

  const hasError = Object.keys(errorObj.toJSON() || {}).length > 0;
  return {
    mode: normalizedConfig.MODE,
    dataObj,
    errorObj,
    isLoading: Boolean(ui.isLoading),
    hasError,
    reload,
  };
};

export default usePageData;
