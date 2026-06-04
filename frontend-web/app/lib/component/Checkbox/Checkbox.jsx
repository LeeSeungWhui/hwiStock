/**
 * 파일명: Checkbox.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Checkbox UI 컴포넌트 구현
 */
import { useState, useEffect, forwardRef } from 'react';
import checkboxCssModule from './Checkbox.module.css';
import { getBoundValue, setBoundValue, buildCtx, fireValueHandlers } from '../../binding';

/**
 * @description 렌더링 및 상호작용 처리
 * 처리 규칙: 전달된 props와 바인딩 값을 기준으로 UI 상태를 계산하고 변경 이벤트를 상위로 전달한다.
 * @updated 2026-02-27
 */
const Checkbox = forwardRef(({
    label,
    name,
    onChange,
    onValueChange,
    dataObj,
    dataKey,
    className = "",
    checked: propChecked,
    disabled = false,
    color = "primary",
    ...props
}, ref) => {

    const isControlled = propChecked !== undefined;
    const isDataObjControlled = dataObj && (dataKey || label);

    // name이나 dataKey가 없을 경우 label을 사용
    const inputName = name || label || dataKey;
    const dataKeyName = dataKey || label;

    const [internalChecked, setInternalChecked] = useState(() => {
        if (dataObj && dataKeyName) {
            return [true, 'Y', 'y', '1', 1].includes(getBoundValue(dataObj, dataKeyName));
        }
        return false;
    });

    /**
     * @description dataObj 바인딩 checked 값을 internalChecked에 동기화
     * 처리 규칙: isDataObjControlled일 때 getBoundValue 결과를 boolean으로 변환한다.
     */
    useEffect(() => {
        if (isDataObjControlled) {
            const boundValue = getBoundValue(dataObj, dataKeyName);
            const isNextChecked = [true, 'Y', 'y', '1', 1].includes(boundValue);
            setInternalChecked(isNextChecked);
        }
    }, [isDataObjControlled, dataObj, dataKeyName]);

    /**
     * @description 체크박스 변경값을 내부 상태와 dataObj에 반영하고 이벤트를 전파
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

        if (isDataObjControlled) {
            setBoundValue(dataObj, dataKeyName, isNewChecked);
        }

        const bindingCtx = buildCtx({ dataKey: dataKeyName, dataObj, source: 'user', dirty: true, valid: null });
        fireValueHandlers({ onChange, onValueChange, value: isNewChecked, ctx: bindingCtx, event });
    };

    const colorKey = typeof color === "string" ? color.toLowerCase() : "primary";
    const colorClassMap = {
        primary: checkboxCssModule.checkboxPrimary,
        success: checkboxCssModule.checkboxSuccess,
        warning: checkboxCssModule.checkboxWarning,
        danger: checkboxCssModule.checkboxDanger,
        neutral: checkboxCssModule.checkboxNeutral,
    };
    const colorClassName = colorClassMap[colorKey] || checkboxCssModule.checkboxPrimary;
    let isChecked = internalChecked;
    if (isControlled) {
        isChecked = Boolean(propChecked);
    } else if (isDataObjControlled) {
        isChecked = [true, 'Y', 'y', '1', 1].includes(getBoundValue(dataObj, dataKeyName));
    }

    return (
        <label className={`${checkboxCssModule.wrapper} ${className}`}>
            <input
                ref={ref}
                type="checkbox"
                name={inputName}
                checked={isChecked}
                disabled={disabled}
                onChange={handleChange}
                className={`${checkboxCssModule.checkbox} ${colorClassName}`.trim()}
                role="checkbox"
                aria-checked={isChecked}
                aria-disabled={disabled}
                {...props}
            />
            {label && <span className={checkboxCssModule.label}>{label}</span>}
        </label>
    );
});

Checkbox.displayName = 'Checkbox';

/**
 * @description Checkbox 컴포넌트 진입점 노출
 * 반환값: 체크 상태 입력을 처리하는 Checkbox 컴포넌트.
 * @returns {React.ComponentType}
 */
export default Checkbox;
