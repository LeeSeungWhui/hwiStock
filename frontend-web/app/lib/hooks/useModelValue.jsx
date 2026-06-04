/**
 * 파일명: useModelValue.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: EasyObj/EasyList 경로 값을 React 외부 스토어 형태로 구독하는 훅
 */

import { useCallback, useRef, useSyncExternalStore } from "react";
import { getBoundValue, setBoundValue } from "@/app/lib/binding";

/**
 * @description path 입력을 점 표기 문자열 배열로 정규화
 * 처리 규칙: number/string/array/null 입력을 공통 세그먼트 배열로 변환한다.
 * @param {string|string[]|number|null|undefined} path
 * @returns {string[]}
 */
const normalizePath = (path) => {
  if (Array.isArray(path)) {
    return path.map((segment) => String(segment));
  }
  if (typeof path === "number") {
    return [String(path)];
  }
  if (typeof path === "string") {
    return path
      .split(".")
      .map((segment) => segment.trim())
      .filter((segment) => segment.length > 0);
  }
  return [];
};

/**
 * @description 변경 경로와 구독 경로가 같은지 또는 상하위 관계인지 판별
 * 처리 규칙: 루트 변경/루트 구독은 항상 true로 간주하고, 그 외에는 prefix 일치 여부를 비교한다.
 * @param {Array<string|number>|undefined} changedPath
 * @param {string[]} targetPath
 * @returns {boolean}
 */
const pathMatches = (changedPath, targetPath) => {
  if (!targetPath.length) return true;
  if (!Array.isArray(changedPath)) return false;
  const normalizedChangedPath = changedPath.map((segment) => String(segment));
  if (!normalizedChangedPath.length) return true;
  const compareLength = Math.min(normalizedChangedPath.length, targetPath.length);
  for (let index = 0; index < compareLength; index += 1) {
    if (normalizedChangedPath[index] !== targetPath[index]) return false;
  }
  return true;
};

/**
 * @description 모델 경로 값 읽기를 공통화
 * 처리 규칙: model.get이 있으면 우선 사용하고, 없으면 binding dotted path 조회로 fallback한다.
 * @param {object} model
 * @param {string[]} pathSegments
 * @param {unknown} defaultValue
 * @returns {unknown}
 */
const readModelValue = (model, pathSegments, defaultValue) => {
  if (!model) return defaultValue;
  const normalizedPath = pathSegments.join(".");
  let modelValue;
  if (typeof model.get === "function") {
    modelValue = model.get(pathSegments);
  } else {
    modelValue = getBoundValue(model, normalizedPath);
  }
  return typeof modelValue === "undefined" ? defaultValue : modelValue;
};

/**
 * @description EasyObj/EasyList 경로 값을 구독하고 setter를 제공
 * 처리 규칙: 경로 관련 변경만 구독하고, setter는 model.set/delete 또는 binding helper로 반영한다.
 * @param {object} params
 * @param {object} params.model
 * @param {string|string[]|number|null|undefined} params.path
 * @param {unknown} [params.defaultValue]
 * @param {string} [params.source]
 * @returns {[unknown, Function]}
 */
const useModelValue = ({
  model,
  path,
  defaultValue,
  source = "user",
}) => {
  const versionRef = useRef(0);
  const snapshotRef = useRef({
    version: -1,
    value: undefined,
    snapshot: { version: -1, value: undefined },
  });

  /**
   * @description 현재 경로 스냅샷을 생성하거나 재사용
   * 처리 규칙: 같은 version/value 조합이면 캐시한 snapshot 객체를 재사용한다.
   * @returns {{version:number, value:unknown}}
   */
  const getSnapshot = useCallback(() => {
    const pathSegments = normalizePath(path);
    const modelValue = readModelValue(model, pathSegments, defaultValue);
    if (snapshotRef.current.version === versionRef.current) {
      if (Object.is(snapshotRef.current.value, modelValue)) {
        return snapshotRef.current.snapshot;
      }
    }
    const nextSnapshotObj = {
      version: versionRef.current,
      value: modelValue,
    };
    snapshotRef.current = {
      version: versionRef.current,
      value: modelValue,
      snapshot: nextSnapshotObj,
    };
    return nextSnapshotObj;
  }, [defaultValue, model, path]);

  /**
   * @description 모델 subscribe를 useSyncExternalStore 규약으로 연결
   * 처리 규칙: 관련 경로 변경일 때만 version을 증가시키고 notify를 호출한다.
   * @param {Function} notify
   * @returns {Function}
   */
  const subscribe = useCallback((notify) => {
    const pathSegments = normalizePath(path);
    if (!model || typeof model.subscribe !== "function") {
      return () => {};
    }
    const unsubscribe = model.subscribe((detail) => {
      if (!pathMatches(detail?.path, pathSegments)) return;
      versionRef.current += 1;
      notify();
    });
    return () => unsubscribe?.();
  }, [model, path]);

  const snapshot = useSyncExternalStore(subscribe, getSnapshot, getSnapshot);

  /**
   * @description 구독 경로 값에 다음 값을 반영
   * 처리 규칙: updater 함수도 허용하고, undefined는 delete 경로로 처리한다.
   * @param {unknown|Function} nextValue
   * @returns {void}
   */
  const setValue = useCallback((nextValue) => {
    const pathSegments = normalizePath(path);
    if (!model) return;
    const resolvedValue = typeof nextValue === "function"
      ? nextValue(readModelValue(model, pathSegments, defaultValue))
      : nextValue;
    if (typeof resolvedValue === "undefined") {
      if (typeof model.delete === "function") {
        model.delete(pathSegments, { source });
        return;
      }
      if (pathSegments.length) {
        const parentPath = pathSegments.slice(0, -1).join(".");
        const parentValue = parentPath
          ? getBoundValue(model, parentPath)
          : model;
        if (parentValue && typeof parentValue === "object") {
          Reflect.deleteProperty(
            parentValue,
            pathSegments[pathSegments.length - 1],
          );
        }
      }
      return;
    }
    if (typeof model.set === "function") {
      model.set(pathSegments, resolvedValue, { source });
      return;
    }
    setBoundValue(model, pathSegments.join("."), resolvedValue, { source });
  }, [defaultValue, model, path, source]);

  return [snapshot.value, setValue];
};

export default useModelValue;
export { useModelValue };
