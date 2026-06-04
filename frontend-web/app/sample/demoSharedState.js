"use client";

/**
 * 파일명: sample/demoSharedState.js
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 공개 샘플 페이지 간 공유 상태(세션 메모리) 유틸
 */

import { useEffect } from "react";
import { getSharedSnapshot, useSharedData } from "@/app/common/store/SharedStore";
import { deepCloneValue } from "@/app/lib/runtime/json";

/**
 * @description 샘플 상태 값을 안전하게 깊은 복사
 * @returns {any}
 * @updated 2026-02-27
 */
const cloneValue = (value) => {
  if (value == null) return value;
  return deepCloneValue(value, value);
};

/**
 * @description 샘플 공용 상태를 읽고 쓰는 훅을 반환. 입력/출력 계약을 함께 명시
 * @param {{ stateKey: string, initialValue: any }} params
 * @returns {{ value: any, setValue: (nextValueOrUpdater: any) => void, resetValue: () => void, isInitialized: boolean }}
 */
export const useDemoSharedState = ({ stateKey, initialValue }) => {

  const { shared, setShared } = useSharedData();

  /**
   * @description shared[stateKey]가 없을 때 initialValue를 1회 주입
   * 처리 규칙: sharedValue가 undefined일 때만 cloneValue(initialValue)를 저장한다.
   */
  useEffect(() => {

    /**
     * @description 공유 상태 미존재 시 초기값 1회 채움
     * 처리 규칙: sharedValue가 undefined일 때만 cloneValue(initialValue)를 저장.
     * @updated 2026-02-23
     */
    if (shared?.[stateKey] !== undefined) return;
    setShared({ [stateKey]: cloneValue(initialValue) });
  }, [initialValue, setShared, shared, stateKey]);

  /**
   * @description 최신 공유 상태를 기준으로 다음 상태를 계산해 저장
   * 처리 규칙: 스토어 스냅샷에서 현재값을 읽어 updater 함수/직접값 입력을 분기한다.
   * @updated 2026-04-08
   */
  const setValue = (nextValueOrUpdater) => {
    const latestShared = getSharedSnapshot();
    const currentValue =
      latestShared[stateKey] === undefined
        ? cloneValue(initialValue)
        : latestShared[stateKey];
    const nextValue =
      typeof nextValueOrUpdater === "function"
        ? nextValueOrUpdater(currentValue)
        : nextValueOrUpdater;
    setShared({ [stateKey]: cloneValue(nextValue) });
  };

  /**
   * @description 공유 상태 초기값 복원
   * 처리 규칙: stateKey 슬롯을 cloneValue(initialValue)로 덮어쓰기.
   * @updated 2026-02-23
   */
  const resetValue = () => {
    setShared({ [stateKey]: cloneValue(initialValue) });
  };

  return {
    value: shared?.[stateKey] === undefined ? initialValue : shared?.[stateKey],
    setValue,
    resetValue,
    isInitialized: shared?.[stateKey] !== undefined,
  };
};
