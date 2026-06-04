/**
 * 파일명: NumberInput.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: NumberInput UI 컴포넌트 구현
 */

import { forwardRef, useEffect, useRef, useState } from 'react';
import Icon from './Icon';
import { getBoundValue, setBoundValue, buildCtx, fireValueHandlers } from '../binding';

/**
 * @description 렌더링 및 상호작용 처리
 * 처리 규칙: 전달된 props와 바인딩 값을 기준으로 UI 상태를 계산하고 변경 이벤트를 상위로 전달한다.
 * @updated 2026-02-27
 */
const NumberInput = forwardRef(({
  dataObj,
  dataKey,
  value: propValue,
  defaultValue = '',
  onChange,
  onValueChange,
  min,
  max,
  step = 1,
  className = '',
  disabled = false,
  readOnly = false,
  placeholder,
  id,
  ...props
}, ref) => {

  const isPropControlled = propValue !== undefined;
  const isDataBound = Boolean(dataObj && dataKey);

  const [innerValue, setInnerValue] = useState(defaultValue);

  /**
   * @description 입력값을 정규화해 상태/바인딩/핸들러로 확정 반영
   * 부작용: innerValue, dataObj[dataKey], onChange/onValueChange 이벤트 값이 함께 갱신된다.
   * @updated 2026-02-27
   */
  const commitNumberValue = (rawInputValue, event) => {
    let parsedNumber = '';
    const hasRawNumberInput =
      rawInputValue !== '' && rawInputValue !== null && typeof rawInputValue !== 'undefined';
    if (hasRawNumberInput) {
      const rawNumber = Number(rawInputValue);
      if (Number.isFinite(rawNumber)) {
        parsedNumber = rawNumber;
      }
    }
    let nextValue = parsedNumber;
    const isBelowMin = nextValue !== '' && min !== undefined && nextValue < min;
    if (isBelowMin) nextValue = min;
    const isAboveMax = nextValue !== '' && max !== undefined && nextValue > max;
    if (isAboveMax) nextValue = max;
    if (!isPropControlled && !isDataBound) setInnerValue(nextValue);
    if (isDataBound) setBoundValue(dataObj, dataKey, nextValue);
    const bindingCtx = buildCtx({ dataKey, dataObj, source: 'user', dirty: true, valid: null });
    const nextEvent = event ? { ...event, target: { ...event.target, value: nextValue } } : { target: { value: nextValue } };
    fireValueHandlers({ onChange, onValueChange, value: nextValue, ctx: bindingCtx, event: nextEvent });
  };

  /**
   * @description stepDelta 증감값으로 숫자 값을 변경
   * 처리 규칙: disabled/readOnly면 중단하고, 그 외에는 min/max 보정 후 commit을 호출한다.
   * @updated 2026-02-27
   */
  const changeByStep = (stepDelta) => {
    if (disabled || readOnly) return;
    let currentValue = innerValue ?? '';
    if (isPropControlled) {
      currentValue = propValue ?? '';
    } else if (isDataBound) {
      currentValue = getBoundValue(dataObj, dataKey) ?? '';
    }
    const baseNumber = currentValue === '' ? 0 : Number(currentValue) || 0;
    let nextValue = baseNumber + stepDelta;
    if (min !== undefined && nextValue < min) nextValue = min;
    if (max !== undefined && nextValue > max) nextValue = max;
    commitNumberValue(nextValue);
  };

  const holdIntervalRef = useRef(null);
  const holdTimerRef = useRef(null);
  const [hasHeldStarted, setHasHeldStarted] = useState(false);

  /**
   * @description 증감 버튼 long-press 반복 입력을 시작
   * 처리 규칙: 300ms 지연 후 120ms 간격 반복 호출로 연속 증감을 수행한다.
   * @updated 2026-02-27
   */
  const startHold = (stepDelta) => {
    clearInterval(holdIntervalRef.current);
    clearTimeout(holdTimerRef.current);
    setHasHeldStarted(false);
    holdTimerRef.current = setTimeout(() => {
      setHasHeldStarted(true);
      changeByStep(stepDelta);
      holdIntervalRef.current = setInterval(() => changeByStep(stepDelta), 120);
    }, 300);
  };

  /**
   * @description press 관련 타이머와 반복 인터벌 정리
   * 부작용: holdIntervalRef/holdTimerRef를 null로 초기화한다.
   * @updated 2026-02-27
   */
  const stopHold = () => {
    clearInterval(holdIntervalRef.current);
    clearTimeout(holdTimerRef.current);
    holdIntervalRef.current = null;
    holdTimerRef.current = null;
  };

  /**
   * @description 컴포넌트 해제 시 long-press 타이머를 정리
   * 처리 규칙: pending timeout/interval이 unmount 뒤 상태를 갱신하지 못하게 차단한다.
   */
  useEffect(() => () => {
    clearInterval(holdIntervalRef.current);
    clearTimeout(holdTimerRef.current);
  }, []);

  let currentNumberValue = innerValue ?? '';
  if (isPropControlled) {
    currentNumberValue = propValue ?? '';
  } else if (isDataBound) {
    currentNumberValue = getBoundValue(dataObj, dataKey) ?? '';
  }

  const baseClassName = 'block w-full h-10 px-3 text-sm rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-0 bg-white border';
  const stateClassName = 'border-gray-300 focus:ring-blue-500 focus:border-blue-500';

  const inputId = id || (dataKey ? `num_${String(dataKey).replace(/[^a-zA-Z0-9_]+/g, '_')}` : undefined);

  return (
    <div className={`inline-flex items-center gap-2 w-full ${className}`.trim()} {...props}>
      <button
        type="button"
        className="h-10 w-10 flex items-center justify-center rounded-full border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-50"
        onMouseDown={() => startHold(-step)}
        onMouseUp={stopHold}
        onMouseLeave={stopHold}
        onClick={(event) => { if (hasHeldStarted) { event.preventDefault(); setHasHeldStarted(false); return; } changeByStep(-step); }}
        disabled={disabled || readOnly}
        aria-label="decrement"
      >
        <Icon icon="md:MdRemove" className="w-5 h-5" />
      </button>

      <input
        ref={ref}
        id={inputId}
        type="text"
        inputMode="decimal"
        pattern="[0-9.-]*"
        placeholder={placeholder}
        value={currentNumberValue}
        onChange={(event) => {
          const nextInputValue = event.target.value;
          if (nextInputValue === '' || /^-?\d*(?:\.\d*)?$/.test(nextInputValue)) {
            if (!isPropControlled && !isDataBound) setInnerValue(nextInputValue);
          }
        }}
        onKeyDown={(event) => {
          if (event.key === 'ArrowUp') { event.preventDefault(); changeByStep(+step); }
          if (event.key === 'ArrowDown') { event.preventDefault(); changeByStep(-step); }
          if (event.key === 'PageUp') { event.preventDefault(); changeByStep(+step * 10); }
          if (event.key === 'PageDown') { event.preventDefault(); changeByStep(-step * 10); }
        }}
        onBlur={(event) => commitNumberValue(event.target.value, event)}
        className={`${baseClassName} ${stateClassName} flex-1`.trim()}
        disabled={disabled}
        readOnly={readOnly}
        role="spinbutton"
        aria-valuemin={min}
        aria-valuemax={max}
        aria-valuenow={
          currentNumberValue === '' ? undefined : Number(currentNumberValue)
        }
      />

      <button
        type="button"
        className="h-10 w-10 flex items-center justify-center rounded-full border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-50"
        onMouseDown={() => startHold(+step)}
        onMouseUp={stopHold}
        onMouseLeave={stopHold}
        onClick={(event) => { if (hasHeldStarted) { event.preventDefault(); setHasHeldStarted(false); return; } changeByStep(+step); }}
        disabled={disabled || readOnly}
        aria-label="increment"
      >
        <Icon icon="md:MdAdd" className="w-5 h-5" />
      </button>
    </div>
  );
});

NumberInput.displayName = 'NumberInput';

/**
 * @description 숫자 입력/step 증감/바인딩 동기화 기능을 가진 NumberInput 컴포넌트를 외부에 노출
 * 반환값: NumberInput 컴포넌트 export.
 */
export default NumberInput;
