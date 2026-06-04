/**
 * 파일명: binding.js
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 바인딩 유틸 함수
 */

// 바인딩 유틸 함수 선언 구간

/**
 * @description 바인딩 객체에서 key 경로 값 조회
 * 처리 규칙: dataObj.get 우선 사용, 없으면 `a.b.c` dotted path를 순회한다.
 * @updated 2026-02-24
 */
export const getBoundValue = (dataObj, dataKey) => {
  if (!dataObj || !dataKey) return undefined;

  if (typeof dataObj.get === 'function') return dataObj.get(dataKey);

  const pathSegmentList = String(dataKey).split('.');
  let currentValue = dataObj;
  for (const pathSegment of pathSegmentList) {
    if (currentValue == null) return undefined;
    currentValue = currentValue[pathSegment];
  }
  return currentValue;
}

/**
 * @description 바인딩 객체의 key 경로 값을 설정. 입력/출력 계약을 함께 명시
 * 부작용: 경로 중간 노드가 없으면 객체를 생성하고 마지막 키에 값을 대입한다.
 * @updated 2026-02-24
 */
export const setBoundValue = (dataObj, dataKey, value, options = {}) => {

  if (!dataObj || !dataKey) return;
  const meta = typeof options === 'object' && options !== null ? options : {};
  if (typeof dataObj.set === 'function') return dataObj.set(dataKey, value, { source: meta.source ?? 'user' });
  const pathSegmentList = String(dataKey).split('.');
  let currentObj = dataObj;
  for (const pathSegment of pathSegmentList.slice(0, -1)) {
    if (currentObj[pathSegment] == null || typeof currentObj[pathSegment] !== 'object') {
      currentObj[pathSegment] = {};
    }
    currentObj = currentObj[pathSegment];
  }
  currentObj[pathSegmentList[pathSegmentList.length - 1]] = value;
  return value;
}

/**
 * @description 값 변경 컨텍스트를 구성. 입력/출력 계약을 함께 명시
 * 반환값: `{ dataKey, modelType, dirty, valid, source }` 형태의 공통 ctx 객체.
 * @updated 2026-02-24
 */
export const buildCtx = ({ dataKey, dataObj, source = 'user', valid = null, dirty = true }) => {

  const modelSource = dataObj && dataObj.__rawObject ? dataObj.__rawObject : dataObj;
  let modelType = null;
  if (Array.isArray(modelSource)) {
    modelType = 'list';
  } else if (modelSource && typeof modelSource === 'object') {
    modelType = 'obj';
  }
  return { dataKey, modelType, dirty: Boolean(dirty), valid, source };
}

/**
 * @description onChange/onValueChange 핸들러에 공통 이벤트 규약을 전달
 * 처리 규칙: event.detail에 value/ctx를 주입하고 onChange(event) → onValueChange(value, ctx) 순으로 호출한다.
 * @updated 2026-02-24
 */
export const fireValueHandlers = ({ onChange, onValueChange, value: handlerValue, ctx: bindingCtx, event }) => {


  if (event) {
    try {
      if (!Object.prototype.hasOwnProperty.call(event, 'detail') || event.detail == null) {
        Object.defineProperty(event, 'detail', { value: { value: handlerValue, ctx: bindingCtx }, configurable: true, writable: true });
      } else if (typeof event.detail === 'object') {
        event.detail.value = handlerValue;
        event.detail.ctx = bindingCtx;
      }
    } catch {
      try {
        event.detail = { value: handlerValue, ctx: bindingCtx };
      } catch {
        if (bindingCtx && typeof bindingCtx === 'object') {
          bindingCtx.eventDetailSynced = false;
        }
      }
    }
  }
  if (typeof onChange === 'function' && event) onChange(event);
  if (typeof onValueChange === 'function') onValueChange(handlerValue, bindingCtx);
}
