'use client'

/**
 * 파일명: AppShell.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 앱 공통 셸 컴포넌트
 */

import { useEffect, useRef } from 'react'
import { usePathname } from "next/navigation";
import { useGlobalUi } from './common/store/SharedStore'
import Loading from '@/app/lib/component/Loading'
import Alert from '@/app/lib/component/Alert'
import Confirm from '@/app/lib/component/Confirm'
import Toast from '@/app/lib/component/Toast/Toast'
import PublicGnb from "@/app/common/layout/PublicGnb";
import PublicFooter from "@/app/common/layout/PublicFooter";

/**
 * @description 로딩/알림/확인/토스트 오버레이와 퍼블릭 셸 분기를 관리하는 AppShell 컴포넌트를 렌더링. 입력/출력 계약을 함께 명시
 * 처리 규칙: 퍼블릭 경로는 Header/Footer를 감싸고, 그 외 경로는 children만 그대로 노출한다.
 */
const AppShell = ({ children }) => {

  const pathname = usePathname();
  const pathText = String(pathname || "");
  const {
    isLoading,
    alert, hideAlert,
    confirm, hideConfirm,
    toast, hideToast,
  } = useGlobalUi()
  const isPublicShell =
    pathText === "/" || pathText.startsWith("/sample/portfolio");
  const shellClassName = pathText.startsWith("/sample/portfolio")
    ? "mx-auto w-full max-w-6xl px-4 py-10 sm:px-6 lg:px-8"
    : "mx-auto w-full max-w-6xl px-4 py-8 sm:px-6 lg:px-8";
  const focusTimerRef = useRef(null);

  /**
   * @description 공통 셸 해제 시 pending focus 복귀 타이머를 정리
   * 처리 규칙: alert/confirm 종료 직후 예약된 focus 콜백이 unmount 뒤 실행되지 않게 차단한다.
   */
  useEffect(() => () => clearTimeout(focusTimerRef.current), [])

  /**
   * @description Alert 닫기 클릭 시 콜백 실행과 포커스 복귀를 함께 처리
   * 처리 규칙: onClick 실행 여부와 관계없이 hideAlert 후 onFocus를 비동기 복귀시킨다.
   */
  const handleAlertClick = () => {
    try {
      if (typeof alert?.onClick === 'function') {
        alert.onClick()
      }
    } finally {
      hideAlert()

      clearTimeout(focusTimerRef.current)
      focusTimerRef.current = setTimeout(() => {
        if (typeof alert?.onFocus === 'function') {
          alert.onFocus()
        }
      }, 0)
    }
  }

  /**
   * @description toast.show가 true일 때 duration 경과 후 hideToast 자동 호출
   * 처리 규칙: cleanup에서 toastTimer clearTimeout을 수행한다.
   */
  useEffect(() => {
    if (toast?.show && (toast.duration ?? 3000) !== Infinity) {
      const toastTimer = setTimeout(() => hideToast(), toast.duration ?? 3000)
      return () => clearTimeout(toastTimer)
    }
  }, [toast?.show, toast?.duration, hideToast])

  /**
   * @description Confirm 종료 결과를 반영하고 포커스를 원복
   * 처리 규칙: hideConfirm에 사용자의 선택값을 전달한 뒤 onFocus를 비동기 호출한다.
   */
  const handleConfirmClose = (isConfirmed) => {
    hideConfirm(isConfirmed)
    clearTimeout(focusTimerRef.current)
    focusTimerRef.current = setTimeout(() => {
      if (typeof confirm?.onFocus === 'function') {
        confirm.onFocus()
      }
    }, 0)
  }

  return (
    <>
      {isLoading && <Loading />}
      {isPublicShell ? (
        <div className="min-h-screen bg-gray-50 text-gray-900">
          <PublicGnb />
          <main className={shellClassName}>{children}</main>
          <PublicFooter />
        </div>
      ) : (
        children
      )}
      {alert?.show && (
        <Alert title={alert.title} text={alert.message} type={alert.type} onClick={handleAlertClick} />
      )}
      {confirm?.show && (
        <Confirm
          title={confirm.title}
          text={confirm.message}
          type={confirm.type}
          onConfirm={() => handleConfirmClose(true)}
          onCancel={() => handleConfirmClose(false)}
          confirmText={confirm.confirmText}
          cancelText={confirm.cancelText}
        />
      )}
      {toast?.show && (
        <Toast message={toast.message} type={toast.type} position={toast.position} isExiting={false} onClose={hideToast} />
      )}
    </>
  )
}

export default AppShell
