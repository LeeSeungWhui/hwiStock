/**
 * 파일명: CheckButton.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: CheckButton UI 컴포넌트 구현
 */
import React, { useState, useEffect } from 'react';
import { getBoundValue, setBoundValue, buildCtx, fireValueHandlers } from '../binding';

/**
 * @description 렌더링 및 상호작용 처리
 * 처리 규칙: 전달된 props와 바인딩 값을 기준으로 UI 상태를 계산하고 변경 이벤트를 상위로 전달한다.
 * @updated 2026-02-27
 */
const CheckButton = React.forwardRef(({
    children,
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
    const isDataObjControlled = dataObj && (dataKey || name);

    const inputName = name || dataKey || (typeof children === 'string' ? children : undefined);
    const dataKeyName = dataKey || name || (typeof children === 'string' ? children : undefined);

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

    let isChecked = internalChecked;
    if (isControlled) {
        isChecked = Boolean(propChecked);
    } else if (isDataObjControlled) {
        isChecked = [true, 'Y', 'y', '1', 1].includes(getBoundValue(dataObj, dataKeyName));
    }
    const baseClassName = "inline-flex items-center justify-center px-4 py-2 text-sm font-medium rounded-md transition-all duration-200 border";
    const disabledClassName = disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer";
    const colorKey = typeof color === "string" ? color.toLowerCase() : "primary";
    const colorClassMapObj = {
        primary: {
            checked: "bg-blue-500 text-white hover:bg-blue-600 border-blue-500",
            unchecked: "bg-white border-gray-300 text-gray-700 hover:bg-gray-50 hover:border-blue-500",
        },
        success: {
            checked: "bg-emerald-500 text-white hover:bg-emerald-600 border-emerald-500",
            unchecked: "bg-white border-gray-300 text-gray-700 hover:bg-emerald-50 hover:border-emerald-500",
        },
        warning: {
            checked: "bg-amber-500 text-white hover:bg-amber-600 border-amber-500",
            unchecked: "bg-white border-gray-300 text-gray-700 hover:bg-amber-50 hover:border-amber-500",
        },
        danger: {
            checked: "bg-rose-500 text-white hover:bg-rose-600 border-rose-500",
            unchecked: "bg-white border-gray-300 text-gray-700 hover:bg-rose-50 hover:border-rose-500",
        },
        neutral: {
            checked: "bg-gray-600 text-white hover:bg-gray-700 border-gray-600",
            unchecked: "bg-white border-gray-300 text-gray-700 hover:bg-gray-50 hover:border-gray-500",
        },
    };
    const colorClassObj = colorClassMapObj[colorKey] || colorClassMapObj.primary;
    const colorClassName = isChecked ? colorClassObj.checked : colorClassObj.unchecked;

    /**
     * @description 버튼 클릭 값을 토글하고 bound 데이터/콜백으로 변경 이벤트를 전파
     * @param {React.MouseEvent<HTMLButtonElement>} event
     * @returns {void}
     * @updated 2026-02-27
     */
    const handleChange = (event) => {
        event.stopPropagation();
        const isNewChecked = !isChecked; // 토글

        if (!isControlled) {
            setInternalChecked(isNewChecked);
        }

        if (isDataObjControlled) {
            setBoundValue(dataObj, dataKeyName, isNewChecked, { source: 'user' });
        }

        const bindingCtx = buildCtx({ dataKey: dataKeyName, dataObj, source: 'user', dirty: true, valid: null });
        event.target.value = isNewChecked;
        fireValueHandlers({
            onChange,
            onValueChange,
            value: isNewChecked,
            ctx: bindingCtx,
            event,
        });
    };

    return (
        <button
            ref={ref}
            type="button"
            name={inputName}
            onClick={handleChange}
            disabled={disabled}
            aria-pressed={isChecked}
            className={`
                ${baseClassName}
                ${colorClassName}
                ${disabledClassName}
                ${className}
            `.trim()}
            {...props}
        >
            {children}
        </button>
    );
});

CheckButton.displayName = 'CheckButton';

/**
 * @description CheckButton 컴포넌트 진입점 노출
 * 반환값: 체크 토글 UI를 제공하는 CheckButton 컴포넌트.
 * @returns {React.ComponentType}
 */
export default CheckButton;
