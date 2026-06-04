/**
 * 파일명: Textarea.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Textarea UI 컴포넌트 구현
 */
import { useState, forwardRef, useEffect } from 'react';
import { getBoundValue, setBoundValue, buildCtx, fireValueHandlers } from '../binding';

/**
 * @description 렌더링 및 상호작용 처리
 * 처리 규칙: 전달된 props와 바인딩 값을 기준으로 UI 상태를 계산하고 변경 이벤트를 상위로 전달한다.
 * @updated 2026-02-27
 */
const Textarea = forwardRef(({
  dataObj,
  dataKey,
  value: propValue,
  defaultValue = '',
  onChange,
  onValueChange,
  rows = 4,
  className = '',
  error,
  disabled = false,
  readOnly = false,
  placeholder,
  ...props
}, ref) => {

  const isPropControlled = propValue !== undefined;
  const isDataBound = Boolean(dataObj && dataKey);

  const [innerValue, setInnerValue] = useState(defaultValue);
  const [draftValue, setDraftValue] = useState(undefined);
  const [isComposing, setIsComposing] = useState(false);

  /**
   * @description prop/data/inner 값과 draftValue 일치 시 조합 임시 표시 상태 해제
   * 처리 규칙: externalValue===draftValue이면 setDraftValue(undefined)를 호출한다.
   */
  useEffect(() => {
    let externalValue = innerValue ?? '';
    if (isPropControlled) {
      externalValue = propValue ?? '';
    } else if (isDataBound) {
      externalValue = getBoundValue(dataObj, dataKey) ?? '';
    }
    if (draftValue !== undefined && draftValue === externalValue) {
      setDraftValue(undefined);
    }
  }, [dataObj, dataKey, draftValue, innerValue, isDataBound, isPropControlled, propValue]);

  /**
   * @description 입력값을 저장소(dataObj 또는 내부 state)에 반영하고 상위 폼 동기화를 유지
   * @param {string} rawTextareaValue
   * @param {React.SyntheticEvent | undefined} event
   * @returns {void}
   * @updated 2026-02-27
   */
  const commitTextareaValue = (rawTextareaValue, event) => {
    if (isDataBound) setBoundValue(dataObj, dataKey, rawTextareaValue);
    if (!isPropControlled && !isDataBound) setInnerValue(rawTextareaValue);
    const bindingCtx = buildCtx({ dataKey, dataObj, source: 'user', dirty: true, valid: null });
    const nextEvent = event ? { ...event, target: { ...event.target, value: rawTextareaValue } } : { target: { value: rawTextareaValue } };
    fireValueHandlers({ onChange, onValueChange, value: rawTextareaValue, ctx: bindingCtx, event: nextEvent });
  };

  const baseClassName = 'block w-full px-3 py-2 text-sm rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-0 bg-white';
  const stateClassName = error ? 'border border-red-300 focus:ring-red-500 focus:border-red-500' : 'border border-gray-300 focus:ring-blue-500 focus:border-blue-500';

  let externalValue = innerValue ?? '';
  if (isPropControlled) {
    externalValue = propValue ?? '';
  } else if (isDataBound) {
    externalValue = getBoundValue(dataObj, dataKey) ?? '';
  }
  const textareaValue = draftValue ?? externalValue;

  return (
    <textarea
      ref={ref}
      className={`${baseClassName} ${stateClassName} ${className}`.trim()}
      rows={rows}
      value={textareaValue}
      onChange={(event) => {
        const isTextComposing = event.nativeEvent?.isComposing || isComposing;
        const rawTextareaValue = event.target.value;
        setDraftValue(rawTextareaValue);
        if (!isTextComposing) {
          commitTextareaValue(rawTextareaValue, event);
        }
      }}
      onCompositionStart={() => { setIsComposing(true); }}
      onCompositionEnd={(event) => { setIsComposing(false); commitTextareaValue(event.target.value, event); }}
      onBlur={(event) => { commitTextareaValue(event.target.value, event); }}
      disabled={disabled}
      readOnly={readOnly}
      placeholder={placeholder}
      aria-invalid={Boolean(error)}
      {...props}
    />
  );
});

Textarea.displayName = 'Textarea';

/**
 * @description Textarea 컴포넌트 진입점 노출
 * 반환값: 다중 줄 텍스트 입력을 처리하는 Textarea 컴포넌트.
 * @returns {React.ComponentType}
 */
export default Textarea;
