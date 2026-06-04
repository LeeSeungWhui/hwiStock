/**
 * 파일명: EasyObj.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 객체형 반응형 데이터 모델
 */

import { useState, useRef } from 'react';

/**
 * @description 상태 반영 함수를 다음 틱으로 예약
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
 * @description 일반 객체(plain object) 여부를 판별
 * 처리 규칙: 프로토타입이 `Object.prototype` 또는 `null`인 경우만 true를 반환한다.
 * @updated 2026-02-27
 */
const isPlainObject = (value) => {
    if (!isObject(value)) return false;
    const proto = Object.getPrototypeOf(value);
    return proto === Object.prototype || proto === null;
};

/**
 * @description 프록시 래핑 가능한 데이터 타입인지 확인
 * 처리 규칙: 배열 또는 plain object인 경우만 true를 반환한다.
 * @updated 2026-02-27
 */
const isProxyableObject = (value) => Array.isArray(value) || isPlainObject(value);

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
 * @description 프록시 대상 객체/배열을 깊은 복사
 * 처리 규칙: primitive와 비-프록시 객체는 원본을 유지하고, 배열/plain object만 재귀 복사한다.
 * @updated 2026-02-27
 */
const deepCopy = (value) => {
    if (!isObject(value)) return value;
    if (!isProxyableObject(value)) return value;
    if (Array.isArray(value)) return value.map((listValue) => deepCopy(listValue));
    const copiedObj = {};
    for (const propertyKey of Object.keys(value)) copiedObj[propertyKey] = deepCopy(value[propertyKey]);
    return copiedObj;
};

/**
 * @description EasyObj 프록시 상태 모델을 생성. 입력/출력 계약을 함께 명시
 * 처리 규칙: 내부 raw 데이터와 proxy 매핑을 유지하고 변경 시 렌더/구독 이벤트를 트리거한다.
 * @updated 2026-02-27
 */
const useEasyObj = (initialData = {}) => {

    const [, forceRender] = useState({});
    const rootRef = useRef(isObject(initialData) ? deepCopy(initialData) : {});
    const listenersRef = useRef(new Set());
    const rawToProxyRef = useRef(new WeakMap());
    const proxyToRawRef = useRef(new WeakMap());
    const rootProxyRef = useRef(null);
    const renderJobRef = useRef(null);

    /**
     * @description 변경 플래그를 세우고 렌더 갱신을 예약
     * 처리 규칙: 이미 dirty 상태면 중복 예약하지 않고, 다음 틱에 한 번만 forceRender를 실행한다.
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
     * 처리 규칙: proxyToRaw 매핑 또는 `__rawObject`를 우선 사용하고, 없으면 원값을 반환한다.
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
            rootRef.current = isObject(value) ? value : {};
            return prevValueObj;
        }
        if (!isObject(rootRef.current)) rootRef.current = {};
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
     * 처리 규칙: 키가 없으면 removed=false를 반환하고, 존재하면 이전값과 삭제 결과를 함께 반환한다.
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
        if (!isProxyableObject(rawPrev)) return rawPrev;
        return deepCopy(rawPrev);
    };

    /**
     * @description raw 값을 외부 노출용 값으로 래핑
     * 처리 규칙: 프록시 가능 객체면 경로 기반 프록시를 반환하고, primitive/비-프록시 객체는 원값을 반환한다.
     * @updated 2026-02-27
     */
    const wrapValue = (rawValue, pathSegments) => {
        if (!isObject(rawValue)) return rawValue;
        if (!isProxyableObject(rawValue)) return rawValue;
        if (!pathSegments.length) return ensureRootProxy();
        return getOrCreateProxy(rawValue, pathSegments);
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
     * @description 프록시 핸들러가 사용할 실 컨테이너를 결정
     * 처리 규칙: 루트 경로는 rootRef를 우선하고, 하위 경로는 synchronizeProxyTarget 결과를 사용한다.
     * @updated 2026-02-27
     */
    const resolveContainer = (target, proxy, basePath) => {
        if (!basePath.length) {
            if (!isObject(rootRef.current)) rootRef.current = {};
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
     * @description 구독자에게 변경 이벤트를 브로드캐스트
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
                modelType: 'obj',
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
     * 처리 규칙: root 대입 시 deepCopy/맵 초기화를 수행하고, 값이 실제로 바뀐 경우만 dirty/emit을 실행한다.
     * @updated 2026-02-27
     */
    const applySet = (pathSegments, incomingValue, options = {}) => {

        const source = options.source ?? 'program';
        const nextRaw = unwrap(incomingValue);
        const onRoot = pathSegments.length === 0;
        let normalizedValue = nextRaw;
        if (onRoot) {
            if (isObject(nextRaw)) {
                normalizedValue = deepCopy(nextRaw);
            }
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
     * @description 객체 브랜치를 대상 값으로 교체 동기화
     * 처리 규칙: 누락 키는 삭제하고, 입력 plain object의 key/value를 applySet으로 반영한다.
     * @updated 2026-02-27
     */
    const replaceBranch = (basePath, sourceValue, options = {}) => {

        const plain = unwrap(sourceValue);
        if (!isPlainObject(plain)) {
            applySet(basePath, deepCopy(plain), options);
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
     * @description raw 객체에 대한 프록시를 조회하거나 생성. 입력/출력 계약을 함께 명시
     * 처리 규칙: WeakMap 캐시를 우선 사용하고, proxy handler에서 get/set/delete/copy 구문을 EasyObj 규약으로 통합한다.
     * @updated 2026-02-27
     */
    const getOrCreateProxy = (rawObj, basePath = []) => {
        if (!isProxyableObject(rawObj)) return rawObj;
        const cached = rawToProxyRef.current.get(rawObj);
        if (cached) return cached;
        let proxy;
        const proxyHandlerObj = {
            get(target, prop) {
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
                    return (sourceObj) => replaceBranch(basePath, sourceObj ?? {}, { source: 'program' });
                }
                if (prop === 'deepCopy') {
                    return (sourceObj) => replaceBranch(basePath, deepCopy(sourceObj ?? {}), { source: 'program' });
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
                        if (typeof listener !== 'function') return () => {};
                        listenersRef.current.add(listener);
                        return () => listenersRef.current.delete(listener);
                    };
                }
                if (prop === 'forAll') {

                    // 모든 1단계 필드를 순회하며 콜백을 적용한다.
                    // 콜백은 (value, key, obj) 인자를 받고, 반환값이 undefined가 아니면 해당 키에 대입한다.
                    return (fn) => {
                        if (typeof fn !== 'function') return wrapValue(container, basePath);
                        const propertyKeyList = isObject(container) ? Object.keys(container) : [];
                        for (let propertyIndex = 0; propertyIndex < propertyKeyList.length; propertyIndex += 1) {
                            const propertyKey = propertyKeyList[propertyIndex];
                            const nextValue = fn(container[propertyKey], propertyKey, container);
                            if (typeof nextValue !== 'undefined') {
                                applySet(normalizePath(basePath, propertyKey), nextValue, { source: 'program' });
                            }
                        }
                        return wrapValue(container, basePath);
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

                // Native branded objects(File/Blob 등)는 자기 자신을 receiver로 써야 getter가 안전하다.
                const propertyValue = Reflect.get(baseObject, prop, baseObject);
                if (isProxyableObject(propertyValue)) {
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
        if (!isObject(rootRef.current)) rootRef.current = {};
        if (rootProxyRef.current) {
            const cachedRawRoot = proxyToRawRef.current.get(rootProxyRef.current);
            if (cachedRawRoot === rootRef.current) {
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

export default useEasyObj;
export { useEasyObj };
