/**
 * 파일명: Radiobox.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Radiobox UI 컴포넌트 구현
 */
import { useState, useEffect, forwardRef } from 'react';
import { getBoundValue, setBoundValue, buildCtx, fireValueHandlers } from '../../binding';
import radioboxCssModule from './Radiobox.module.css';

/**
 * @description 렌더링 및 상호작용 처리
 * 처리 규칙: 전달된 props와 바인딩 값을 기준으로 UI 상태를 계산하고 변경 이벤트를 상위로 전달한다.
 * @updated 2026-02-27
 */
const Radiobox = forwardRef(({
    label,
    name,
    value,
    onChange,
    onValueChange,
    dataObj,
    dataKey,
    className = "",
    checked: propChecked,
    defaultChecked,
    disabled = false,
    color = "primary",
    ...props
}, ref) => {

    const isControlled = propChecked !== undefined;
    const isDataObjControlled = dataObj && (dataKey || label);

    // name이나 dataKey가 없을 경우 label을 name으로 사용
    const inputName = name || label || dataKey;
    const dataKeyName = dataKey || name || label;

    const [internalChecked, setInternalChecked] = useState(() => {
        if (dataObj && dataKeyName) {
            return getBoundValue(dataObj, dataKeyName) === value;
        }
        return defaultChecked || false;
    });

    /**
     * @description dataObj 바인딩 값이 value와 일치하는지 internalChecked에 동기화
     * 처리 규칙: isDataObjControlled일 때 getBoundValue===value 결과를 반영한다.
     */
    useEffect(() => {
        if (isDataObjControlled) {
            const currentValue = getBoundValue(dataObj, dataKeyName);
            const isNextChecked = currentValue === value;
            setInternalChecked(isNextChecked);
        }
    }, [isDataObjControlled, dataObj, dataKeyName, value]);

    /**
     * @description 라디오 변경 이벤트를 처리하고 dataObj/콜백에 선택값을 반영
     * @param {React.ChangeEvent<HTMLInputElement>} event
     * @returns {void}
     * @updated 2026-02-27
     */
    const handleChange = (event) => {
        event.stopPropagation();
        const isNewChecked = event.target.checked;

        if (!isControlled) {
            setInternalChecked(isNewChecked);
        }

        if (isDataObjControlled && isNewChecked) {
            setBoundValue(dataObj, dataKeyName, value, { source: 'user' });
        }

        const bindingCtx = buildCtx({ dataKey: dataKeyName, dataObj, source: 'user', dirty: true, valid: null });
        if (isNewChecked) {
            event.target.value = value;
        }
        fireValueHandlers({
            onChange,
            onValueChange,
            value: isNewChecked ? value : undefined,
            ctx: bindingCtx,
            event,
        });
    };

    const colorKey = typeof color === "string" ? color.toLowerCase() : "primary";
    const radioColorClassMap = {
        primary: radioboxCssModule.radioPrimary,
        success: radioboxCssModule.radioSuccess,
        warning: radioboxCssModule.radioWarning,
        danger: radioboxCssModule.radioDanger,
        neutral: radioboxCssModule.radioNeutral,
    };
    const radioColorClassName = radioColorClassMap[colorKey] || radioColorClassMap.primary;
    let isChecked = internalChecked;
    if (isControlled) {
        isChecked = Boolean(propChecked);
    } else if (isDataObjControlled) {
        isChecked = getBoundValue(dataObj, dataKeyName) === value;
    }

    return (
        <label className={`${radioboxCssModule.wrapper} ${className}`}>
            <input
                ref={ref}
                type="radio"
                name={inputName}
                value={value}
                checked={isChecked}
                disabled={disabled}
                onChange={handleChange}
                className={`${radioboxCssModule.radio} ${radioColorClassName}`.trim()}
                {...props}
            />
            {label && <span className={radioboxCssModule.label}>{label}</span>}
        </label>
    );
});

Radiobox.displayName = 'Radiobox';

/**
 * @description Radiobox 컴포넌트 진입점 노출
 * 반환값: 기본 라디오 입력 UI를 제공하는 Radiobox 컴포넌트.
 * @returns {React.ComponentType}
 */
export default Radiobox;
