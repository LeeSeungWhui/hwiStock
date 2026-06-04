/**
 * 파일명: Drawer.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Drawer UI 컴포넌트 구현
 */
import { forwardRef, useEffect } from 'react';
import Icon from './Icon';

const drawerSideMapObj = {
  right: {
    base: 'inset-y-0 right-0 w-80 max-w-full rounded-l-2xl',
    transform: { open: 'translate-x-0', closed: 'translate-x-full' }
  },
  left: {
    base: 'inset-y-0 left-0 w-80 max-w-full rounded-r-2xl',
    transform: { open: 'translate-x-0', closed: '-translate-x-full' }
  },
  top: {
    base: 'inset-x-0 top-0 h-72 max-h-full rounded-b-2xl',
    transform: { open: 'translate-y-0', closed: '-translate-y-full' }
  },
  bottom: {
    base: 'inset-x-0 bottom-0 h-72 max-h-full rounded-t-2xl',
    transform: { open: 'translate-y-0', closed: 'translate-y-full' }
  }
};
const resizeClassMapObj = {
  horizontal: 'resize-x overflow-auto',
  vertical: 'resize-y overflow-auto',
};

/**
 * @description 렌더링 및 열림 상태 전환 처리
 * 처리 규칙: 열림 상태에 따라 위치/사이즈/접힘 버튼 UI를 계산하고 외부 닫기 이벤트를 전파.
 * @updated 2026-02-27
 */
const Drawer = forwardRef(function Drawer(
  {
    isOpen = false,
    onClose,
    side = 'right',
    size = '',
    closeOnBackdrop = true,
    closeOnEsc = true,
    resizable = false,
    collapseButton = false,
    className = '',
    children,
    ...props
  },

  ref
) {

  const sideConfigObj = drawerSideMapObj[side] || drawerSideMapObj.right;

  /**
   * @description isOpen일 때 document keydown으로 Escape 닫기 처리
   * 처리 규칙: cleanup에서 keydown 리스너를 제거하고 closeOnEsc일 때 onClose를 호출한다.
   */
  useEffect(() => {
    if (!isOpen) return undefined;

    /**
     * @description Esc 입력을 감지해 closeOnEsc 옵션이 켜진 경우 패널을 닫힘 상태로 전환
     * @param {KeyboardEvent} keyboardEvent
     * @returns {void}
     * @updated 2026-02-27
     */
    const handleDocKeyDown = (keyboardEvent) => {
      if (closeOnEsc && keyboardEvent.key === 'Escape') onClose?.();
    };

    document.addEventListener('keydown', handleDocKeyDown);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', handleDocKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [isOpen, closeOnEsc, onClose]);



  const sizeClassName = typeof size === 'string' ? size.trim() : '';
  const resizeAxisKey = side === 'top' || side === 'bottom' ? 'vertical' : 'horizontal';
  const resizeClassName = resizable ? resizeClassMapObj[resizeAxisKey] : '';
  const transformClassName = isOpen ? sideConfigObj.transform.open : sideConfigObj.transform.closed;


  const cornerBoostClassName = collapseButton ? {
    bottom: 'rounded-t-2xl',
    left: 'rounded-r-2xl',
    right: 'rounded-l-2xl',
    top: 'rounded-b-2xl',
  }[side] : '';


  const handlePositionMapObj = {
    right: 'absolute left-1 top-1/2 -translate-y-1/2',
    left: 'absolute right-1 top-1/2 -translate-y-1/2',
    top: 'absolute bottom-1 left-1/2 -translate-x-1/2',
    bottom: 'absolute top-1 left-1/2 -translate-x-1/2'
  };

  const handleShapeMapObj = {
    right: 'h-16 w-7 rounded-r-lg border-l',
    left: 'h-16 w-7 rounded-l-lg border-r',
    top: 'w-16 h-7 rounded-b-lg border-t',
    bottom: 'w-16 h-7 rounded-t-lg border-b'
  };
  const handleBaseClassName = 'bg-gray-100/90 hover:bg-gray-200 text-gray-500 border-gray-200 shadow-sm flex items-center justify-center focus:outline-none focus:ring-2 focus:ring-blue-500/30';
  const arrowRotateClassMap = { right: '', left: 'rotate-180', top: '-rotate-90', bottom: 'rotate-90' };

  const contentPadClassName = collapseButton ? {
    bottom: 'pt-10',
    left: 'pr-10',
    right: 'pl-10',
    top: 'pb-10',
  }[side] : '';

  /**
   * @description forwardRef가 함수형/객체형인 경우를 모두 지원해 패널 DOM 참조를 전달
   * @param {HTMLElement | null} el
   * @returns {void}
   * @updated 2026-02-27
   */
  const assignRef = (el) => {
    if (typeof ref === 'function') ref(el);
    else if (ref) ref.current = el;
  };

  const drawerPropsObj = { ...(props || {}) };
  delete drawerPropsObj.style;

  return (
    <div
      className={`fixed inset-0 z-50 transition-opacity duration-300 ease-in-out ${isOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}`}
      aria-hidden={!isOpen}
    >

      {/* 배경 레이어 */}
      <div
        className={`absolute inset-0 bg-black/40 transition-opacity duration-300 ease-in-out ${isOpen ? 'opacity-100' : 'opacity-0'}`}
        onClick={() => { if (closeOnBackdrop) onClose?.(); }}
        aria-hidden="true"
      />

      {/* 패널 */}
      <div
        ref={assignRef}
        className={`absolute bg-white shadow-xl transform-gpu will-change-transform transition-transform duration-300 ease-in-out ${sideConfigObj.base} ${cornerBoostClassName} ${transformClassName} ${sizeClassName} ${resizeClassName} ${className}`.trim()}
        {...drawerPropsObj}
      >
        <div className={contentPadClassName}>
          {children}
        </div>

        {collapseButton && (
          <button
            type="button"
            aria-label="collapse"
            className={`${handleBaseClassName} ${handleShapeMapObj[side]} ${handlePositionMapObj[side]} z-10`}
            onClick={() => onClose?.()}
          >

            <Icon icon="hi:HiChevronRight" className={arrowRotateClassMap[side]} size="12px" />
          </button>
        )}
      </div>
    </div>
  );
});

Drawer.displayName = 'Drawer';

/**
 * @description Drawer 컴포넌트 진입점 노출
 * 반환값: 측면 패널 열림/닫힘 동작을 제공하는 Drawer 컴포넌트.
 * @returns {React.ComponentType}
 */
export default Drawer;
