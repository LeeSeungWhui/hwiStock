"use client";

/**
 * 파일명: useSwr.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: apiJSON을 fetcher로 사용하는 SWR 래퍼 훅(선택적)
 */
import useSwrLib from "swr";
import { apiJSON } from "@/app/lib/runtime/api";

/**
 * @description apiJSON 기반 SWR fetcher를 구성. 입력/출력 계약을 함께 명시
 * @param {string|string[]|null} key
 * @param {string} path
 * @param {Object} [options]
 * @returns {any}
 */
export const useSwr = (
  { key, path, method = "GET", body, fetchInit = {}, swr = {} },
) => {
  return useSwrLib(
    key,
    () => apiJSON(path, { method, body, ...fetchInit }),
    { revalidateOnFocus: false, ...swr },
  );
}

export default useSwr;
