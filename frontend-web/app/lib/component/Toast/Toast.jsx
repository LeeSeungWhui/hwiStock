/**
 * 파일명: Toast.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Toast UI 컴포넌트 구현
 */
import { forwardRef } from 'react';
import Icon from '../Icon';
import toastCssModule from './Toast.module.css';
import { COMMON_LANG_KO } from '@/app/common/i18n/lang.ko';

/**
 * @description 렌더링 및 상호작용 처리
 * 처리 규칙: 전달된 props와 바인딩 값을 기준으로 UI 상태를 계산하고 변경 이벤트를 상위로 전달한다.
 * @updated 2026-02-27
 */
const Toast = forwardRef(({
    message,
    type = 'info',
    position = 'bottom-center',
    isExiting = false,
    onClose,
    className = '',
    ...props
}, ref) => {

    const toastTypeMetaObj = {
        info: {
            icon: 'ri:RiInformationLine',
            iconColor: 'text-blue-500',
            bgColor: 'bg-blue-50',
            borderColor: 'border-blue-200'
        },
        success: {
            icon: 'ri:RiCheckboxCircleLine',
            iconColor: 'text-green-500',
            bgColor: 'bg-green-50',
            borderColor: 'border-green-200'
        },
        warning: {
            icon: 'ri:RiErrorWarningLine',
            iconColor: 'text-yellow-500',
            bgColor: 'bg-yellow-50',
            borderColor: 'border-yellow-200'
        },
        error: {
            icon: 'ri:RiCloseCircleLine',
            iconColor: 'text-red-500',
            bgColor: 'bg-red-50',
            borderColor: 'border-red-200'
        }
    };

    const toastPlaceClassMap = {
        'top-left': 'top-4 left-4',
        'top-center': 'top-4 left-1/2 -translate-x-1/2',
        'top-right': 'top-4 right-4',
        'bottom-left': 'bottom-4 left-4',
        'bottom-center': 'bottom-4 left-1/2 -translate-x-1/2',
        'bottom-right': 'bottom-4 right-4'
    };

    // 위치에 따른 슬라이드 방향 결정
    const isTopPosition = position.startsWith('top-');
    const slideInAnimation = isTopPosition ? toastCssModule.slideDown : toastCssModule.slideUp;
    const slideOutAnimation = isTopPosition ? toastCssModule.slideUpExit : toastCssModule.slideDownExit;

    return (
        <div
            ref={ref}
            className={`
                fixed z-50
                ${toastPlaceClassMap[position] || toastPlaceClassMap['bottom-center']}
                flex items-center
                w-[calc(100vw-32px)] max-w-md
                px-4 py-3
                rounded-lg shadow-lg
                border ${(toastTypeMetaObj[type] || toastTypeMetaObj.info).borderColor}
                ${(toastTypeMetaObj[type] || toastTypeMetaObj.info).bgColor}
                backdrop-blur-sm
                ${isExiting ? slideOutAnimation : slideInAnimation}
                ${className}
            `.trim()}
            role="alert"
            {...props}
        >
            <Icon
                icon={(toastTypeMetaObj[type] || toastTypeMetaObj.info).icon}
                size="1.25em"
                className={`mr-3 ${(toastTypeMetaObj[type] || toastTypeMetaObj.info).iconColor} flex-shrink-0`}
            />
            <div className="flex-1 text-sm text-gray-600">
                {message}
            </div>
            {onClose && (
                <button
                    type="button"
                    onClick={onClose}
                    aria-label={COMMON_LANG_KO.action.close}
                    className="ml-3 text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 rounded-full p-1"
                >
                    <Icon icon="ri:RiCloseLine" size="1.25em" />
                </button>
            )}
        </div>
    );
});

Toast.displayName = 'Toast';

/**
 * @description Toast 컴포넌트 진입점 노출
 * 반환값: 상태별 알림 메시지 표시를 제공하는 Toast 컴포넌트.
 * @returns {React.ComponentType}
 */
export default Toast;
