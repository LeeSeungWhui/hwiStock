/**
 * 파일명: Button.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Button UI 컴포넌트 구현
 */
import { forwardRef, useId } from 'react';
import Icon from './Icon';
import { COMMON_COMPONENT_LANG_KO } from '@/app/common/i18n/lang.ko';

/**
 * @description 렌더링 및 상호작용 처리
 * 처리 규칙: 전달된 props와 바인딩 값을 기준으로 UI 상태를 계산하고 변경 이벤트를 상위로 전달한다.
 * @updated 2026-02-27
 */
const Button = forwardRef(({
    children,
    type = 'button',
    className = '',
    variant = 'primary',
    size = 'md',
    icon,
    iconPosition = 'left',
    disabled = false,
    loading = false,
    status,
    'aria-describedby': ariaDescribedByProp,
    ...props
}, ref) => {

    const baseClassName = "inline-flex items-center justify-center font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors";

    const buttonVariantMapObj = {
        primary: "bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500",

        secondary: "border border-blue-600 text-blue-600 bg-white hover:bg-blue-50 focus:ring-blue-500",
        outline: "border border-gray-300 text-gray-700 bg-white hover:bg-gray-50 focus:ring-blue-500",
        danger: "bg-red-600 text-white hover:bg-red-700 focus:ring-red-500",
        success: "bg-green-600 text-white hover:bg-green-700 focus:ring-green-500",
        warning: "bg-yellow-600 text-white hover:bg-yellow-700 focus:ring-yellow-500",
        ghost: "text-gray-600 bg-transparent hover:bg-gray-100 focus:ring-gray-500",
        link: "text-blue-600 bg-transparent hover:text-blue-700 underline-offset-2 hover:underline focus:ring-blue-500",
        dark: "bg-gray-900 text-white hover:bg-black focus:ring-gray-900",
    };

    const buttonSizeClassMap = {
        sm: "px-3 py-1.5 text-sm",
        md: "px-4 py-2 text-sm",
        lg: "px-5 py-2.5 text-base",
    };

    const buttonClassName = `
        ${baseClassName}
        ${buttonVariantMapObj[variant]}
        ${buttonSizeClassMap[size]}
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        ${className}
    `.trim();

    const iconSize = {
        sm: '1em',
        md: '1.1em',
        lg: '1.2em'
    }[size];

    const iconSpacing = {
        sm: 'mr-1.5',
        md: 'mr-2',
        lg: 'mr-2.5'
    }[size];

    const isBusy = loading || status === 'loading';
    const busyStatusId = useId();
    const buttonAriaDescribedBy = [
        ariaDescribedByProp,
        isBusy ? busyStatusId : null,
    ].filter(Boolean).join(' ') || undefined;
    let leadingIconNode = null;
    if (isBusy) {
        leadingIconNode = (
            <Icon icon="ri:RiLoader4Line" className="animate-spin mr-2" size={iconSize} />
        );
    } else if (icon && iconPosition === 'left') {
        leadingIconNode = (
            <Icon icon={icon} className={iconSpacing} size={iconSize} />
        );
    }
    return (
        <>
            <button
                ref={ref}
                type={type}
                disabled={disabled || isBusy}
                className={buttonClassName}
                aria-busy={isBusy ? 'true' : undefined}
                aria-describedby={buttonAriaDescribedBy}
                {...props}
            >
                {leadingIconNode}
                {children}
                {!isBusy && icon && iconPosition === 'right' && (
                    <Icon icon={icon} className={`ml-${iconSpacing.slice(3)}`} size={iconSize} />
                )}
            </button>
            {isBusy ? (
                <span id={busyStatusId} className="sr-only" role="status" aria-live="polite">
                    {COMMON_COMPONENT_LANG_KO.loading.processingText}
                </span>
            ) : null}
        </>
    );
});

Button.displayName = 'Button';

export default Button;
