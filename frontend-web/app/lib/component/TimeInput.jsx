/**
 * 파일명: TimeInput.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: TimeInput UI 컴포넌트 구현
 */

import { forwardRef, useEffect, useRef, useState } from 'react';
import { getBoundValue, setBoundValue, buildCtx, fireValueHandlers } from '../binding';
import Icon from './Icon';
import { COMMON_COMPONENT_LANG_KO } from '@/app/common/i18n/lang.ko';

/**
 * @description 렌더링 및 상호작용 처리
 * 처리 규칙: 전달된 props와 바인딩 값을 기준으로 UI 상태를 계산하고 변경 이벤트를 상위로 전달한다.
 * @updated 2026-02-27
 */
const TimeInput = forwardRef(({
  dataObj,
  dataKey,
  value: propValue,
  defaultValue = '',
  onChange,
  onValueChange,
  min,
  max,
  step,
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
  const [timeText, setTimeText] = useState(() => (propValue ?? (isDataBound ? getBoundValue(dataObj, dataKey) : innerValue) ?? ''));
  const [isOpen, setIsOpen] = useState(false);

  /**
   * @description prop/data/inner 값 변경을 timeText 표시 문자열에 동기화
   * 처리 규칙: isPropControlled·isDataBound 우선순위로 setTimeText를 갱신한다.
   */
  useEffect(() => {
    if (isPropControlled) {
      setTimeText(propValue ?? '');
      return;
    }
    if (isDataBound) {
      setTimeText(getBoundValue(dataObj, dataKey) ?? '');
      return;
    }
    setTimeText(innerValue ?? '');
  }, [propValue, dataObj, dataKey, innerValue, isDataBound, isPropControlled]);

  /**
   * @description 확정된 시간 문자열을 상태/바인딩/이벤트 핸들러에 반영
   * 부작용: timeText, innerValue, dataObj[dataKey], onChange/onValueChange 호출 값이 갱신된다.
   * @updated 2026-02-27
   */
  const commitTimeValue = (rawTimeValue, event) => {
    setTimeText(rawTimeValue);
    if (!isPropControlled && !isDataBound) setInnerValue(rawTimeValue);
    if (isDataBound) setBoundValue(dataObj, dataKey, rawTimeValue);
    const bindingCtx = buildCtx({ dataKey, dataObj, source: 'user', dirty: true, valid: null });
    const nextEvent = event ? { ...event, target: { ...event.target, value: rawTimeValue } } : { target: { value: rawTimeValue } };
    fireValueHandlers({ onChange, onValueChange, value: rawTimeValue, ctx: bindingCtx, event: nextEvent });
  };

  let currentTimeValue = innerValue ?? '';
  if (isPropControlled) {
    currentTimeValue = propValue ?? '';
  } else if (isDataBound) {
    currentTimeValue = getBoundValue(dataObj, dataKey) ?? '';
  }
  const baseClassName = 'block w-full pr-10 pl-3 py-2 text-sm rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-0 bg-white border';
  const inputStateClassName = 'border-gray-300 focus:ring-blue-500 focus:border-blue-500';
  const inputId = id || (dataKey ? `time_${String(dataKey).replace(/[^a-zA-Z0-9_]+/g, '_')}` : undefined);
  const rootRef = useRef(null);

  const minuteInterval = Math.max(1, step ?? 30);
  const timeOptionList = [];
  for (let secondCursor = 0; secondCursor < 24 * 60 * 60; secondCursor += minuteInterval * 60) {
    const hourValue = Math.floor(secondCursor / 3600);
    const minuteValue = Math.floor((secondCursor % 3600) / 60);
    timeOptionList.push(`${String(hourValue).padStart(2, '0')}:${String(minuteValue).padStart(2, '0')}`);
  }

  /**
   * @description isOpen일 때 document mousedown으로 시간 패널 닫기 처리
   * 처리 규칙: cleanup에서 outside-click 리스너를 제거한다.
   */
  useEffect(() => {
    if (!isOpen) return;

    /**
     * @description 컴포넌트 외부 클릭 시 시간 옵션 패널 닫기
     * 처리 규칙: rootRef 외부 mousedown 이벤트에서만 open=false를 반영한다.
     * @updated 2026-02-27
     */
    const handleDocMouseDown = (event) => { if (rootRef.current && !rootRef.current.contains(event.target)) setIsOpen(false); };

    /**
     * @description Escape 키 입력으로 시간 옵션 패널 닫기
     * 처리 규칙: key 값이 Escape일 때만 close 동작을 적용한다.
     * @updated 2026-02-27
     */
    const handleDocKeyDown = (keyboardEvent) => { if (keyboardEvent.key === 'Escape') setIsOpen(false); };

    document.addEventListener('mousedown', handleDocMouseDown);
    document.addEventListener('keydown', handleDocKeyDown);
    return () => { document.removeEventListener('mousedown', handleDocMouseDown); document.removeEventListener('keydown', handleDocKeyDown); };
  }, [isOpen]);

  return (
    <div className={`relative ${className}`.trim()} ref={rootRef}>
      <input
        ref={ref}
        id={inputId}
        type="text"
        className={`${baseClassName} ${inputStateClassName}`.trim()}
        value={timeText}
        min={min}
        max={max}
        step={step}
        placeholder={placeholder}
        onChange={(event) => setTimeText(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === 'Enter') {
            const typedTimeValue = event.currentTarget.value;
            if (/^\d{2}:\d{2}$/.test(typedTimeValue)) commitTimeValue(typedTimeValue, event);
            else setTimeText(currentTimeValue);
            setIsOpen(false);
          }
        }}
        onBlur={(event) => {
          const typedTimeValue = event.target.value;
          if (/^\d{2}:\d{2}$/.test(typedTimeValue)) commitTimeValue(typedTimeValue, event);
          else setTimeText(currentTimeValue);
        }}
        disabled={disabled}
        readOnly={readOnly}
        aria-invalid={false}
        aria-haspopup="dialog"
        {...props}
      />
      <button
        type="button"
        className="absolute inset-y-0 right-2 my-auto h-6 w-6 rounded hover:bg-gray-100 text-gray-500 flex items-center justify-center"
        onClick={() => setIsOpen((wasOpen) => !wasOpen)}
        tabIndex={-1}
        aria-label={COMMON_COMPONENT_LANG_KO.timeInput.openPickerAriaLabel}
        disabled={disabled || readOnly}
      >
        <Icon icon="md:MdAccessTime" className="w-5 h-5" />
      </button>
      {isOpen && (
        <div className="absolute z-10 mt-1 w-40 max-h-64 overflow-auto rounded-md border border-gray-200 bg-white shadow-lg p-1" role="listbox" id={inputId ? `${inputId}_list` : undefined}>
          {timeOptionList.map((timeOption) => (
            <div
              key={timeOption}
              role="option"
              aria-selected={timeOption === currentTimeValue}
              className={`px-2 py-1 text-sm rounded cursor-pointer hover:bg-blue-50 ${timeOption === currentTimeValue ? 'bg-blue-100' : ''}`}
              onClick={() => {
                commitTimeValue(timeOption);
                setIsOpen(false);
              }}
            >
              {timeOption}
            </div>
          ))}
        </div>
      )}
    </div>
  );
});

TimeInput.displayName = 'TimeInput';

/**
 * @description 수동 입력과 옵션 선택을 지원하는 TimeInput 컴포넌트를 외부에 노출
 * 반환값: TimeInput 컴포넌트 export.
 */
export default TimeInput;
