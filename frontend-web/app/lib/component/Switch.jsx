/**
 * 파일명: Switch.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Switch UI 컴포넌트 구현
 */
import { useState, forwardRef, useEffect } from 'react';
import { getBoundValue, setBoundValue, buildCtx, fireValueHandlers } from '../binding';

const CHECKED_TRUE_LIST = [true, 'Y', 'y', '1', 1];

/**
 * @description 렌더링 및 상호작용 처리
 * 처리 규칙: 전달된 props와 바인딩 값을 기준으로 UI 상태를 계산하고 변경 이벤트를 상위로 전달한다.
 * @updated 2026-02-27
 */
const Switch = forwardRef(({
  label,
  name,
  onChange,
  onValueChange,
  dataObj,
  dataKey,
  className = '',
  checked: propChecked,
  defaultChecked = false,
  disabled = false,
  id,
  ...props
}, ref) => {

  const isControlled = propChecked !== undefined;
  const isDataBound = Boolean(dataObj && dataKey);

  const inputName = name || dataKey;

  const [internalChecked, setInternalChecked] = useState(() => {
    if (isDataBound) return CHECKED_TRUE_LIST.includes(getBoundValue(dataObj, dataKey));
    return Boolean(defaultChecked);
  });

  /**
   * @description dataObj 바인딩 checked 값을 internalChecked에 동기화
   * 처리 규칙: isDataBound일 때 getBoundValue 결과를 CHECKED_TRUE_LIST로 판정한다.
   */
  useEffect(() => {
    if (isDataBound) {
      setInternalChecked(CHECKED_TRUE_LIST.includes(getBoundValue(dataObj, dataKey)));
    }
  }, [isDataBound, dataObj, dataKey]);

  /**
   * @description 스위치 토글 이벤트를 상태/바인딩/핸들러 규약으로 동기화
   * 부작용: internalChecked, dataObj[dataKey], onChange/onValueChange 호출 값이 함께 갱신된다.
   * @updated 2026-02-27
   */
  const handleChange = (event) => {
    event.stopPropagation();
    const isNewChecked = event.target.checked;

    if (!isControlled) setInternalChecked(isNewChecked);
    if (isDataBound) {
      setBoundValue(dataObj, dataKey, isNewChecked);
    }

    const bindingCtx = buildCtx({ dataKey, dataObj, source: 'user', dirty: true, valid: null });
    fireValueHandlers({ onChange, onValueChange, value: isNewChecked, ctx: bindingCtx, event });
  };

  let isChecked = internalChecked;
  if (isControlled) {
    isChecked = Boolean(propChecked);
  } else if (isDataBound) {
    isChecked = CHECKED_TRUE_LIST.includes(getBoundValue(dataObj, dataKey));
  }
  const switchId = id || (dataKey ? `sw_${String(dataKey).replace(/[^a-zA-Z0-9_]+/g, '_')}` : undefined);

  return (
    <label className={`inline-flex items-center gap-2 ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'} ${className}`.trim()}>
      <input
        ref={ref}
        id={switchId}
        type="checkbox"
        name={inputName}
        className="sr-only"
        checked={Boolean(isChecked)}
        onChange={handleChange}
        disabled={disabled}
        role="switch"
        aria-checked={Boolean(isChecked)}
        aria-disabled={disabled}
        {...props}
      />
      <span
        aria-hidden="true"
        className={`relative inline-flex h-6 w-10 items-center rounded-full transition-colors duration-200 ${isChecked ? 'bg-blue-600' : 'bg-gray-300'}`}
      >
        <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform duration-200 ${isChecked ? 'translate-x-5' : 'translate-x-1'}`}></span>
      </span>
      {label && (
        <span className="select-none text-sm text-gray-800">{label}</span>
      )}
    </label>
  );
});

Switch.displayName = 'Switch';

/**
 * @description on/off 토글과 바인딩 연동을 지원하는 Switch 컴포넌트를 외부에 노출
 * 반환값: Switch 컴포넌트 export.
 */
export default Switch;
