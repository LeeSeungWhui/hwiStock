/**
 * 파일명: EasyList.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 리스트형 반응형 데이터 모델
 */

import { useState, useRef } from 'react';

/**
 * @description 리스트 상태 반영 함수를 다음 틱으로 예약
 * 처리 규칙: 브라우저에서는 requestAnimationFrame id를, 그 외 환경에서는 timeout id를 반환한다.
 * @updated 2026-02-27
 */
const scheduleUpdate = (fn) => {
    if (typeof window !== 'undefined' && typeof window.requestAnimationFrame === 'function') {
        return window.requestAnimationFrame(fn);
    }
    return setTimeout(fn, 0);
};

/**
 * @description 값이 null이 아닌 객체 타입인지 검사
 * 처리 규칙: `typeof === 'object'` 이고 `null`이 아니면 true를 반환한다.
 * @updated 2026-02-27
 */
const isObject = (value) => typeof value === 'object' && value !== null;

/**
 * @description 경로 키가 숫자 인덱스 문자열인지 검사
 * 처리 규칙: 문자열이면서 정규식 `^\\d+$`에 일치하면 true를 반환한다.
 * @updated 2026-02-27
 */
const isNumericKey = (key) => {
    if (typeof key !== 'string') return false;
    return /^\d+$/.test(key);
};

/**
 * @description key 입력을 경로 세그먼트 배열로 정규화. 입력/출력 계약을 함께 명시
 * 처리 규칙: number/string/array/symbol 케이스를 공통 배열 포맷으로 변환한다.
 * @updated 2026-02-27
 */
const toSegments = (key) => {
    if (Array.isArray(key)) return key.map((segment) => (typeof segment === 'number' ? String(segment) : segment));
    if (typeof key === 'number') return [String(key)];
    if (typeof key === 'string') {
        if (key.length === 0) return [];
        return key.split('.').filter((segment) => segment.length > 0);
    }
    if (typeof key === 'symbol') return [key];
    return [String(key)];
};

/**
 * @description 프록시 감싸면 안 되는 내장 객체 여부를 판별
 * @param {unknown} value
 * @returns {boolean}
 */
const isNativeFileLike = (value) => {
    if (!isObject(value)) return false;
    if (Array.isArray(value)) return false;
    if (typeof File !== 'undefined' && value instanceof File) return true;
    if (typeof Blob !== 'undefined' && value instanceof Blob) return true;
    if (typeof FileList !== 'undefined' && value instanceof FileList) return true;
    return false;
};

/**
 * @description 리스트 데이터의 깊은 복사본을 생성. 입력/출력 계약을 함께 명시
 * 처리 규칙: primitive와 파일류 객체는 원본을 유지하고, 배열/일반 객체만 재귀 복사한다.
 * @updated 2026-02-27
 */
const deepCopy = (value) => {
    if (!isObject(value) || isNativeFileLike(value)) return value;
    if (Array.isArray(value)) return value.map((listValue) => deepCopy(listValue));
    const copiedObj = {};
    for (const propertyKey of Object.keys(value)) copiedObj[propertyKey] = deepCopy(value[propertyKey]);
    return copiedObj;
};

/**
 * @description EasyList 프록시 상태 모델을 생성. 입력/출력 계약을 함께 명시
 * 처리 규칙: raw 리스트와 proxy 매핑을 유지하고 변경 시 렌더/구독 이벤트를 트리거한다.
 * @updated 2026-02-27
 */
const useEasyList = (initialData = []) => {
    const [, forceRender] = useState({});
    const rootRef = useRef(Array.isArray(initialData) ? deepCopy(initialData) : []);
    const listenersRef = useRef(new Set());
    const rawToProxyRef = useRef(new WeakMap());
    const proxyToRawRef = useRef(new WeakMap());
    const rootProxyRef = useRef(null);
    const renderJobRef = useRef(null);

    /**
     * @description 변경 플래그를 세우고 렌더 갱신을 예약
     * 처리 규칙: 이미 dirty 상태면 중복 예약하지 않고 다음 틱에 한 번만 forceRender를 실행한다.
     * @updated 2026-02-27
     */
    const markDirty = () => {
        if (renderJobRef.current !== null) return;
        renderJobRef.current = scheduleUpdate(() => {
            renderJobRef.current = null;
            forceRender({});
        });
    };

    /**
     * @description 프록시 값을 raw 객체로 역참조
     * 처리 규칙: proxyToRaw 매핑 또는 `__rawObject`를 우선 사용하고 없으면 원값을 반환한다.
     * @updated 2026-02-27
     */
    const unwrap = (value) => {
        if (!isObject(value)) return value;
        if (proxyToRawRef.current.has(value)) return proxyToRawRef.current.get(value);
        if (value.__rawObject) return value.__rawObject;
        return value;
    };

    /**
     * @description 지정 경로의 현재 값을 조회. 입력/출력 계약을 함께 명시
     * 처리 규칙: 경로 중간 값이 null/undefined면 즉시 undefined를 반환한다.
     * @updated 2026-02-27
     */
    const readAtPath = (pathSegments) => {
        if (!pathSegments.length) return rootRef.current;
        let cursor = rootRef.current;
        for (const segment of pathSegments) {
            if (cursor == null) return undefined;
            const pathKey = typeof segment === 'symbol' ? segment : String(segment);
            cursor = cursor[pathKey];
        }
        return cursor;
    };

    /**
     * @description 경로 진행 중 필요한 중간 컨테이너를 보장
     * 처리 규칙: 다음 키가 숫자 인덱스면 배열, 아니면 객체를 생성한다.
     * @updated 2026-02-27
     */
    const ensureContainer = (cursor, key, nextKey) => {
        if (!isObject(cursor[key])) {
            const shouldBeArray = typeof nextKey === 'string' ? isNumericKey(nextKey) : false;
            cursor[key] = shouldBeArray ? [] : {};
        }
        return cursor[key];
    };

    /**
     * @description 경로 위치에 값을 대입하고 이전 값을 반환. 입력/출력 계약을 함께 명시
     * 처리 규칙: 루트 대입은 rootRef를 교체하고, 하위 경로 대입은 중간 컨테이너를 자동 생성한다.
     * @updated 2026-02-27
     */
    const assignAtPath = (pathSegments, value) => {
        if (!pathSegments.length) {
            const prevValueObj = { prev: rootRef.current };
            rootRef.current = Array.isArray(value) ? value : [];
            return prevValueObj;
        }
        if (!Array.isArray(rootRef.current)) rootRef.current = [];
        let cursor = rootRef.current;
        for (let index = 0; index < pathSegments.length - 1; index += 1) {
            const pathKey = typeof pathSegments[index] === 'symbol' ? pathSegments[index] : String(pathSegments[index]);
            cursor = ensureContainer(
                cursor,
                pathKey,
                typeof pathSegments[index + 1] === 'symbol' ? undefined : String(pathSegments[index + 1]),
            );
        }
        const lastKey =
            typeof pathSegments[pathSegments.length - 1] === 'symbol'
                ? pathSegments[pathSegments.length - 1]
                : String(pathSegments[pathSegments.length - 1]);
        const prevValueObj = { prev: cursor[lastKey] };
        cursor[lastKey] = value;
        return prevValueObj;
    };

    /**
     * @description 경로 위치의 필드를 제거
     * 처리 규칙: 배열 인덱스는 splice로 삭제하고, 일반 객체는 Reflect.deleteProperty로 삭제한다.
     * @updated 2026-02-27
     */
    const removeAtPath = (pathSegments) => {
        if (!pathSegments.length) return { prev: undefined, removed: false };
        let cursor = rootRef.current;
        for (let index = 0; index < pathSegments.length - 1; index += 1) {
            const pathKey = typeof pathSegments[index] === 'symbol' ? pathSegments[index] : String(pathSegments[index]);
            cursor = cursor?.[pathKey];
            if (cursor == null) return { prev: undefined, removed: false };
        }
        const leafKey =
            typeof pathSegments[pathSegments.length - 1] === 'symbol'
                ? pathSegments[pathSegments.length - 1]
                : String(pathSegments[pathSegments.length - 1]);
        if (Array.isArray(cursor)) {
            if (typeof leafKey === 'string') {
                if (isNumericKey(leafKey)) {
                    const index = Number(leafKey);
                    const isIndexOutOfRange =
                        Number.isNaN(index) || index < 0 || index >= cursor.length;
                    if (isIndexOutOfRange) return { prev: undefined, removed: false };
                    return { prev: cursor.splice(index, 1)[0], removed: true };
                }
            }
        }
        if (!Object.prototype.hasOwnProperty.call(cursor ?? {}, leafKey)) {
            return { prev: undefined, removed: false };
        }
        return {
            prev: cursor[leafKey],
            removed: Reflect.deleteProperty(cursor, leafKey),
        };
    };

    /**
     * @description 기준 경로와 key 결합 기반 최종 경로 생성
     * 처리 규칙: key를 세그먼트 배열로 변환한 뒤 basePath 뒤에 이어붙인다.
     * @updated 2026-02-27
     */
    const normalizePath = (basePath, key) => {
        const nextSegments = toSegments(key);
        if (!nextSegments.length) return [...basePath];
        return [...basePath, ...nextSegments];
    };

    /**
     * @description 변경 이벤트용 이전 값을 안전하게 래핑
     * 처리 규칙: 객체/배열은 deepCopy로 스냅샷을 만들고 primitive는 그대로 반환한다.
     * @updated 2026-02-27
     */
    const wrapPrevValue = (rawPrev) => {
        if (!isObject(rawPrev)) return rawPrev;
        return deepCopy(rawPrev);
    };

    /**
     * @description raw 값을 외부 노출용 값으로 래핑
     * 처리 규칙: 프록시 가능 객체면 경로 기반 프록시를 반환하고, primitive/파일류 객체는 원값을 반환한다.
     * @updated 2026-02-27
     */
    const wrapValue = (rawValue, pathSegments) => {
        if (!isObject(rawValue) || isNativeFileLike(rawValue)) return rawValue;
        if (!pathSegments.length) return ensureRootProxy();
        return getOrCreateProxy(rawValue, pathSegments);
    };

    /**
     * @description 구독자에게 리스트 변경 이벤트를 브로드캐스트
     * 처리 규칙: path/pathString/ctx 메타를 포함한 detail 객체를 구성하고 각 리스너를 안전 호출한다.
     * @updated 2026-02-27
     */
    const emitChange = ({ type, path, value, prev, source = 'program' }) => {

        const changeDetailObj = {
            type,
            path,
            pathString: path.filter((segment) => typeof segment !== 'symbol').join('.'),
            value,
            prev,
            ctx: {
                dataKey: path.filter((segment) => typeof segment !== 'symbol').join('.'),
                modelType: 'list',
                dirty: true,
                valid: null,
                source,
            },
        };
        listenersRef.current.forEach((listener) => {
            try {
                listener(changeDetailObj);
            } catch {

            }
        });
    };

    /**
     * @description 경로 값 대입의 단일 진입점을 제공
     * 처리 규칙: root 대입 시 deepCopy/맵 초기화를 수행하고 값이 실제로 바뀐 경우만 dirty/emit을 실행한다.
     * @updated 2026-02-27
     */
    const applySet = (pathSegments, incomingValue, options = {}) => {

        const source = options.source ?? 'program';
        const nextRaw = unwrap(incomingValue);
        const onRoot = pathSegments.length === 0;
        let normalizedValue = nextRaw;
        if (onRoot) {
            normalizedValue = Array.isArray(nextRaw) ? deepCopy(nextRaw) : nextRaw;
        }
        const { prev } = assignAtPath(pathSegments, normalizedValue);
        const prevExport = wrapPrevValue(prev);

        if (onRoot) {
            rawToProxyRef.current = new WeakMap();
            proxyToRawRef.current = new WeakMap();
        }

        if (Object.is(prev, normalizedValue)) {
            return wrapValue(normalizedValue, pathSegments);
        }

        markDirty();

        if (onRoot) ensureRootProxy();

        const latest = readAtPath(pathSegments);
        const wrappedValue = wrapValue(latest, pathSegments);
        emitChange({
            type: 'set',
            path: pathSegments,
            value: wrappedValue,
            prev: prevExport,
            source,
        });
        return wrappedValue;
    };

    /**
     * @description 경로 삭제 작업을 진행
     * 처리 규칙: 삭제 성공 시에만 dirty 처리와 delete 이벤트를 발생시키고 boolean 결과를 반환한다.
     * @updated 2026-02-27
     */
    const applyDelete = (pathSegments, options = {}) => {

        const source = options.source ?? 'program';
        const { prev, removed } = removeAtPath(pathSegments);
        if (!removed) return false;
        markDirty();
        const wrappedPrev = wrapPrevValue(prev);
        emitChange({
            type: 'delete',
            path: pathSegments,
            value: undefined,
            prev: wrappedPrev,
            source,
        });
        return true;
    };

    /**
     * @description 브랜치 값을 대상 리스트/객체로 교체 동기화
     * 처리 규칙: 배열 입력은 전체 교체하고, 객체 입력은 키 기준으로 삭제/대입을 각각 수행한다.
     * @updated 2026-02-27
     */
    const replaceBranch = (basePath, sourceValue, options = {}) => {

        const plain = unwrap(sourceValue);
        if (Array.isArray(plain)) {
            applySet(basePath, deepCopy(plain), options);
            return;
        }
        if (!isObject(plain)) {
            applySet(basePath, plain, options);
            return;
        }
        const nextKeySet = new Set(Object.keys(plain));
        const currentBranchValue = readAtPath(basePath);
        const currentKeyList = isObject(currentBranchValue) ? Object.keys(currentBranchValue) : [];
        currentKeyList.forEach((currentKey) => {
            if (!nextKeySet.has(currentKey)) applyDelete([...basePath, currentKey], options);
        });
        Object.entries(plain).forEach(([plainKey, plainValue]) => {
            applySet([...basePath, plainKey], plainValue, options);
        });
    };

    /**
     * @description 프록시가 바라보는 raw 타깃을 최신 경로 값과 동기화
     * 처리 규칙: 최신 값이 객체면 WeakMap 매핑을 갱신하고, 아니면 매핑을 제거한다.
     * @updated 2026-02-27
     */
    const synchronizeProxyTarget = (target, proxy, basePath) => {
        const latest = readAtPath(basePath);
        if (isObject(latest)) {
            if (latest !== target) {
                rawToProxyRef.current.delete(target);
                rawToProxyRef.current.set(latest, proxy);
                proxyToRawRef.current.set(proxy, latest);
            }
            return latest;
        }
        rawToProxyRef.current.delete(target);
        proxyToRawRef.current.set(proxy, latest);
        return latest;
    };

    /**
     * @description 프록시 핸들러에서 사용할 실 컨테이너를 결정
     * 처리 규칙: 루트 경로는 rootRef를 우선하고, 하위 경로는 synchronizeProxyTarget 결과를 사용한다.
     * @updated 2026-02-27
     */
    const resolveContainer = (target, proxy, basePath) => {
        if (!basePath.length) {
            if (!Array.isArray(rootRef.current)) rootRef.current = [];
            if (rootRef.current !== target) {
                rawToProxyRef.current.delete(target);
                rawToProxyRef.current.set(rootRef.current, proxy);
                proxyToRawRef.current.set(proxy, rootRef.current);
            }
            return rootRef.current;
        }
        return synchronizeProxyTarget(target, proxy, basePath);
    };

    /**
     * @description raw 객체에 대한 프록시를 조회하거나 생성. 입력/출력 계약을 함께 명시
     * 처리 규칙: WeakMap 캐시를 우선 사용하고, proxy handler에서 리스트 조작(push/pop/splice 등)을 EasyList 규약으로 통합한다.
     * @updated 2026-02-27
     */
    const getOrCreateProxy = (rawObj, basePath = []) => {
        if (!isObject(rawObj)) return rawObj;
        const cached = rawToProxyRef.current.get(rawObj);
        if (cached) return cached;
        let proxy;
        const proxyHandlerObj = {
            get(target, prop, receiver) {
                const container = resolveContainer(target, proxy, basePath);
                if (prop === '__isProxy') return true;
                if (prop === '__rawObject') return container;
                if (prop === '__path') return [...basePath];
                if (prop === 'toString') {
                    if (isObject(container)) return () => JSON.stringify(container);
                }
                if (prop === 'toJSON') return () => deepCopy(container);
                if (!isObject(container)) {
                    if (prop === 'valueOf') return () => container;
                    if (prop === 'toString') return () => String(container ?? '');
                    if (prop === Symbol.toPrimitive) {
                        return (hint) => {
                            if (hint === 'number') return Number(container);
                            if (hint === 'string') return String(container ?? '');
                            return container;
                        };
                    }
                }
                if (prop === 'copy') {
                    return (sourceList) => replaceBranch(basePath, sourceList ?? [], { source: 'program' });
                }
                if (prop === 'deepCopy') {
                    return (sourceList) => replaceBranch(basePath, deepCopy(sourceList ?? []), { source: 'program' });
                }
                if (prop === 'get') {
                    return (key, defaultValue) => {
                        const fullPath = normalizePath(basePath, key);
                        const pathValue = readAtPath(fullPath);
                        if (typeof pathValue === 'undefined') return defaultValue;
                        return wrapValue(pathValue, fullPath);
                    };
                }
                if (prop === 'set') {
                    return (key, value, opts) => applySet(normalizePath(basePath, key), value, opts);
                }
                if (prop === 'delete') {
                    return (key, opts) => applyDelete(normalizePath(basePath, key), opts);
                }
                if (prop === 'subscribe') {
                    return (listener) => {
                        if (typeof listener !== 'function') return () => { };
                        listenersRef.current.add(listener);
                        return () => listenersRef.current.delete(listener);
                    };
                }
                if (prop === 'push') {
                    return (...items) => {
                        let start = 0;
                        if (Array.isArray(container)) {
                            start = container.length;
                        } else if (Array.isArray(target)) {
                            start = target.length;
                        }
                        items.forEach((insertItemValue, offset) => {
                            applySet([...basePath, String(start + offset)], insertItemValue, { source: 'program' });
                        });
                        const latest = readAtPath(basePath);
                        return Array.isArray(latest) ? latest.length : start + items.length;
                    };
                }
                if (prop === 'pop') {
                    return () => {
                        const targetList = readAtPath(basePath);
                        if (!Array.isArray(targetList) || !targetList.length) return undefined;
                        const index = targetList.length - 1;
                        const poppedValue = wrapValue(targetList[index], [...basePath, String(index)]);
                        applyDelete([...basePath, String(index)], { source: 'program' });
                        return poppedValue;
                    };
                }
                if (prop === 'splice') {
                    return (start, deleteCount, ...items) => {
                        const targetList = readAtPath(basePath);
                        const normalizedStart = Math.max(0, Math.min(targetList.length, Number(start) || 0));
                        const toDelete = Math.max(0, Number(deleteCount) || 0);
                        const removedItemList = [];
                        for (let index = 0; index < toDelete; index += 1) {
                            const removePathList = [...basePath, String(normalizedStart)];
                            const removedItemValue = readAtPath(removePathList);
                            removedItemList.push(wrapValue(removedItemValue, removePathList));
                            applyDelete(removePathList, { source: 'program' });
                        }
                        items.forEach((insertItemValue, offset) => {
                            const insertPathList = [...basePath, String(normalizedStart + offset)];
                            applySet(insertPathList, insertItemValue, { source: 'program' });
                        });
                        return removedItemList;
                    };
                }
                if (prop === 'forAll') {
                    return (callback) => {
                        if (typeof callback !== 'function') return;
                        const targetList = readAtPath(basePath);
                        if (!Array.isArray(targetList)) return;
                        targetList.forEach((targetItemValue, index) => {
                            callback(wrapValue(targetItemValue, [...basePath, String(index)]), index);
                        });
                    };
                }
                if (typeof prop === 'string') {
                    if (prop.includes('.')) {
                        const fullPath = normalizePath(basePath, prop);
                        const pathValue = readAtPath(fullPath);
                        return wrapValue(pathValue, fullPath);
                    }
                }
                const baseObject = isObject(container) ? container : Object(container ?? {});
                const propertyValue = Reflect.get(baseObject, prop, receiver);
                if (isObject(propertyValue) && !isNativeFileLike(propertyValue)) {
                    const nextContainer = readAtPath(normalizePath(basePath, prop));
                    return getOrCreateProxy(nextContainer ?? propertyValue, [...basePath, typeof prop === 'symbol' ? prop : String(prop)]);
                }
                return propertyValue;
            },
            set(target, prop, value) {
                applySet(normalizePath(basePath, prop), value, { source: 'program' });
                return true;
            },
            deleteProperty(target, prop) {
                applyDelete(normalizePath(basePath, prop), { source: 'program' });
                return true;
            },
            has(target, prop) {
                const container = resolveContainer(target, proxy, basePath);
                if (!isObject(container)) {
                    const boxed = Object(container ?? {});
                    return Reflect.has(boxed, prop);
                }
                return Reflect.has(container, prop);
            },
            ownKeys(target) {
                const container = resolveContainer(target, proxy, basePath);
                if (!isObject(container)) {
                    const boxed = Object(container ?? {});
                    return Reflect.ownKeys(boxed);
                }
                return Reflect.ownKeys(container);
            },
            getOwnPropertyDescriptor(target, prop) {
                const container = resolveContainer(target, proxy, basePath);
                if (!isObject(container)) {
                    const boxed = Object(container ?? {});
                    return Object.getOwnPropertyDescriptor(boxed, prop);
                }
                return Object.getOwnPropertyDescriptor(container, prop);
            },
        };
        proxy = new Proxy(rawObj, proxyHandlerObj);
        rawToProxyRef.current.set(rawObj, proxy);
        proxyToRawRef.current.set(proxy, rawObj);
        if (!basePath.length) rootProxyRef.current = proxy;
        return proxy;
    }

    /**
     * @description 루트 프록시의 유효성을 보장
     * 처리 규칙: rootRef와 캐시 프록시의 raw 매핑이 다르면 새 프록시를 재생성한다.
     * @updated 2026-02-27
     */
    const ensureRootProxy = () => {
        if (!Array.isArray(rootRef.current)) rootRef.current = [];
        if (rootProxyRef.current) {
            const rawRoot = proxyToRawRef.current.get(rootProxyRef.current);
            if (rawRoot === rootRef.current) {
                return rootProxyRef.current;
            }
        }
        return getOrCreateProxy(rootRef.current, []);
    }

    if (!rootProxyRef.current) {
        rootProxyRef.current = getOrCreateProxy(rootRef.current, []);
    }

    return rootProxyRef.current;
}

export default useEasyList;
export { useEasyList };
