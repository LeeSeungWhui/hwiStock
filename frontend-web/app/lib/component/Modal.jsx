/**
 * 파일명: Modal.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Modal UI 컴포넌트 구현
 */
import { forwardRef, useCallback, useEffect, useRef, useState } from 'react';
import Icon from './Icon';
import React from 'react';
import { COMMON_LANG_KO } from '@/app/common/i18n/lang.ko';

/**
 * @description 를 렌더링. 입력/출력 계약을 함께 명시
 * 처리 규칙: onClose가 있으면 우측 닫기 버튼을 노출하고 draggable이면 헤더에 drag 커서를 적용한다.
 * @updated 2026-02-27
 */
const Header = ({ className = '', children, onClose, draggable = false, ...props }) => {

    return (
        <div
            className={`
                modal-header
                px-6 py-4
                border-b border-gray-200
                ${draggable ? 'cursor-move' : ''}
                ${className}
            `.trim()}
            {...props}
        >
            <div className="flex items-center justify-between">
                <div className="flex-1">
                    {children}
                </div>
                {onClose && (
                    <button
                        type="button"
                        onClick={onClose}
                        aria-label={COMMON_LANG_KO.action.close}
                        className="p-1 ml-4 text-gray-400 hover:text-gray-600 rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                        <Icon icon="ri:RiCloseLine" size="1.5em" />
                    </button>
                )}
            </div>
        </div>
    );
};

/**
 * @description 를 렌더링. 입력/출력 계약을 함께 명시
 * 반환값: 스크롤 가능한 본문 컨테이너 JSX.
 * @updated 2026-02-27
 */
const Body = ({ className = '', children, ...props }) => {

    return (
        <div
            className={`
                px-6 py-4
                overflow-y-auto
                ${className}
            `.trim()}
            {...props}
        >
            {children}
        </div>
    );
};

/**
 * @description 를 렌더링. 입력/출력 계약을 함께 명시
 * 반환값: 액션 버튼 영역을 감싸는 하단 컨테이너 JSX.
 * @updated 2026-02-27
 */
const Footer = ({ className = '', children, ...props }) => {

    return (
        <div
            className={`
                px-6 py-4
                border-t border-gray-200
                ${className}
            `.trim()}
            {...props}
        >
            {children}
        </div>
    );
};

/**
 * @description 렌더링 및 상호작용 처리
 * 처리 규칙: 전달된 props와 바인딩 값을 기준으로 UI 상태를 계산하고 변경 이벤트를 상위로 전달한다.
 * @updated 2026-02-27
 */
const Modal = forwardRef(({
    isOpen = false,
    onClose,
    size = 'md',
    draggable = false,
    closeOnBackdrop = true,
    closeOnEsc = true,
    ariaLabel,
    ariaLabelledBy,
    top,
    left,
    className = '',
    children,
    ...props
}, ref) => {

    const modalRef = useRef(null);
    const lastFocusedRef = useRef(null);
    const dragStartRef = useRef({ startX: 0, startY: 0 });
    const modalFocusTimerRef = useRef(null);
    const [position, setPosition] = useState(null);
    const [isDragging, setIsDragging] = useState(false);

    const modalSizeClassMap = {
        sm: 'max-w-md',
        md: 'max-w-lg',
        lg: 'max-w-2xl',
        xl: 'max-w-4xl',
        full: 'max-w-full mx-4'
    };

    const focusableSelector =
        'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])';

    /**
     * @description isOpen일 때 body 스크롤 잠금·초점 이동·이전 포커스 복원
     * 처리 규칙: cleanup에서 overflow 복구와 modalFocusTimer clearTimeout을 수행한다.
     */
    useEffect(() => {
        if (isOpen) {
            try { lastFocusedRef.current = document.activeElement; } catch {}
            document.body.style.overflow = 'hidden';
            clearTimeout(modalFocusTimerRef.current);
            modalFocusTimerRef.current = setTimeout(() => {
                if (!modalRef.current) return;
                const focusables = Array.from(modalRef.current.querySelectorAll(focusableSelector));
                if (focusables.length) { try { focusables[0].focus(); } catch {} }
            }, 0);
        }
        return () => {
            clearTimeout(modalFocusTimerRef.current);
            modalFocusTimerRef.current = null;
            document.body.style.overflow = '';
            if (lastFocusedRef.current && typeof lastFocusedRef.current.focus === 'function') {
                try { lastFocusedRef.current.focus(); } catch {}
            }
        };
    }, [isOpen]);

    /**
     * @description 모달 닫힘 시 드래그 position·dragging 상태 초기화
     * 처리 규칙: isOpen=false 전환마다 setPosition(null)과 setIsDragging(false)를 호출한다.
     */
    useEffect(() => {
        if (!isOpen) {
            setPosition(null);
            setIsDragging(false);
        }
    }, [isOpen]);

    /**
     * @description 모달의 실제 좌표(top/left) CSS 변수를 DOM에 반영
     * 처리 규칙: 드래그 좌표(position)가 있으면 px 기준으로 우선 적용하고, 없으면 top/left props를 fallback으로 적용한다.
     * @updated 2026-03-04
     */
    useEffect(() => {
        if (!isOpen) return;
        if (!modalRef.current) return;
        if (position) {
            modalRef.current.style.setProperty('--modal-top', `${position.y}px`);
            modalRef.current.style.setProperty('--modal-left', `${position.x}px`);
            return;
        }
        if (top || left) {
            modalRef.current.style.setProperty('--modal-top', String(top || '50%'));
            modalRef.current.style.setProperty('--modal-left', String(left || '50%'));
            return;
        }
        modalRef.current.style.removeProperty('--modal-top');
        modalRef.current.style.removeProperty('--modal-left');
    }, [isOpen, position, top, left]);

    /**
     * @description isOpen일 때 document keydown으로 ESC 닫기 처리
     * 처리 규칙: cleanup에서 keydown 리스너를 제거하고 closeOnEsc일 때만 onClose를 호출한다.
     */
    useEffect(() => {

    /**
     * @description ESC 키 입력으로 모달을 닫고 드래그 위치를 초기화
     * 처리 규칙: closeOnEsc=true 이고 key가 Escape일 때만 동작한다.
     * @updated 2026-02-27
     */
    const handleKeyDown = (keyboardEvent) => {
            if (closeOnEsc && keyboardEvent.key === 'Escape') {
                onClose?.();
                setPosition(null);  // ESC로 닫을 때도 position 초기화
            }
        };

        if (isOpen) {
            document.addEventListener('keydown', handleKeyDown);
            return () => document.removeEventListener('keydown', handleKeyDown);
        }
    }, [isOpen, closeOnEsc, onClose]);

    // 드래그 시작

    /**
     * @description 헤더 영역 마우스 다운에서 드래그 시작 좌표를 기록
     * 처리 규칙: draggable=true 이고 target이 `.modal-header`일 때만 dragging 상태로 전환한다.
     * @updated 2026-02-27
     */
    const handleMouseDown = (event) => {
        if (!draggable) return;
        if (!modalRef.current) return;

        // 헤더 영역에서만 드래그 가능하도록
        const isHeader = event.target.closest('.modal-header');
        if (!isHeader) return;

        const rect = modalRef.current.getBoundingClientRect();
        dragStartRef.current = {
            startX: event.clientX - rect.left,
            startY: event.clientY - rect.top
        };
        setIsDragging(true);

        document.body.style.userSelect = 'none';
        setPosition({ x: rect.left, y: rect.top });
    };

    // 드래그 중

    /**
     * @description 드래그 중인 모달 위치를 마우스 좌표에 맞춰 업데이트
     * 처리 규칙: 화면 경계(0~viewport-size) 안으로 x/y를 clamp 한다.
     * @updated 2026-02-27
     */
    const handleMouseMove = useCallback((event) => {
        if (!isDragging) return;
        if (!modalRef.current) return;

        const newX = event.clientX - dragStartRef.current.startX;
        const newY = event.clientY - dragStartRef.current.startY;

        // 화면 밖으로 나가지 않도록 제한
        const rect = modalRef.current.getBoundingClientRect();
        const maxX = Math.max(0, window.innerWidth - rect.width);
        const maxY = Math.max(0, window.innerHeight - rect.height);

        setPosition({
            x: Math.min(Math.max(0, newX), maxX),
            y: Math.min(Math.max(0, newY), maxY)
        });
    }, [isDragging]);

    // 드래그 종료

    /**
     * @description 드래그 상태를 종료하고 텍스트 선택 잠금을 해제
     * 부작용: body.userSelect=''로 복구하고 dragging 상태를 false로 전환한다.
     * @updated 2026-02-27
     */
    const handleMouseUp = () => {
        document.body.style.userSelect = '';
        setIsDragging(false);
    };

    /**
     * @description 드래그 중 document mousemove/mouseup 리스너 등록
     * 처리 규칙: cleanup에서 mousemove/mouseup 리스너를 제거한다.
     */
    useEffect(() => {
        if (draggable && isDragging) {
            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);
            return () => {
                document.removeEventListener('mousemove', handleMouseMove);
                document.removeEventListener('mouseup', handleMouseUp);
            };
        }
    }, [draggable, isDragging, handleMouseMove]);

    /**
     * @description 백드롭 직접 클릭 시 모달을 닫고 위치 상태를 초기화
     * 처리 규칙: closeOnBackdrop=true 이고 event.target===event.currentTarget 조건에서만 닫는다.
     * @updated 2026-02-27
     */
    const handleBackdropClick = (event) => {
        if (closeOnBackdrop && event.target === event.currentTarget) {
            onClose?.();
            setPosition(null);  // 백드롭 클릭으로 닫을 때도 position 초기화
        }
    };

    /**
     * @description Tab 키가 모달 안에서 순환하도록 포커스 이동을 제어
     * 처리 규칙: 첫/마지막 focusable 요소 경계에서 기본 Tab 이동을 막고 반대쪽 요소로 보낸다.
     * @updated 2026-05-31
     */
    const handleDialogKeyDown = (keyboardEvent) => {
        if (keyboardEvent.key !== 'Tab') return;

        if (!modalRef.current) return;
        const focusables = Array.from(modalRef.current.querySelectorAll(focusableSelector));
        if (!focusables.length) return;

        if (keyboardEvent.shiftKey) {
            if (document.activeElement === focusables[0]) {
                keyboardEvent.preventDefault();
                try { focusables[focusables.length - 1].focus(); } catch {}
            }
            return;
        }

        if (document.activeElement === focusables[focusables.length - 1]) {
            keyboardEvent.preventDefault();
            try { focusables[0].focus(); } catch {}
        }
    };

    if (!isOpen) return null;

    const isCentered = !position && !top && !left;

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-gray-500/70"
            onClick={handleBackdropClick}
        >
            <div
                ref={(el) => {
                    modalRef.current = el;
                    if (typeof ref === 'function') ref(el);
                    else if (ref) ref.current = el;
                }}
                className={`
                    absolute w-full ${modalSizeClassMap[size]}
                    bg-white rounded-lg shadow-xl
                    animate-fade-in-up
                    ${isCentered ? 'top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2' : 'top-[var(--modal-top)] left-[var(--modal-left)]'}
                    ${isDragging ? '!transition-none' : 'transition-all duration-200'}
                    ${className}
                `.trim()}
                role="dialog"
                aria-modal="true"
                aria-label={ariaLabel}
                aria-labelledby={ariaLabelledBy}
                onMouseDown={handleMouseDown}
                onKeyDown={handleDialogKeyDown}
                {...props}
            >
                {React.Children.map(children, child => {
                    if (child?.type === Header) {
                        return React.cloneElement(child, { draggable });
                    }
                    return child;
                })}
            </div>
        </div>
    );
});

Modal.Header = Header;
Modal.Body = Body;
Modal.Footer = Footer;
Modal.displayName = 'Modal';

/**
 * @description 헤더/본문/푸터 슬롯을 제공하는 공통 Modal 컴포넌트를 외부에 노출
 * 반환값: Modal 컴포넌트 export.
 */
export default Modal;
