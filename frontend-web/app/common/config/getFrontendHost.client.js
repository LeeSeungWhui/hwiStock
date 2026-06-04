/**
 * 파일명: getFrontendHost.client.js
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 클라이언트 컨텍스트에서 프론트엔드 호스트를 조회
 */

import { getConfigSnapshot } from '@/app/common/store/SharedStore'

/**
 * @description config 스냅샷 기반으로 프론트 호스트를 해석하고 기본값을 반환. 입력/출력 계약을 함께 명시
 * @returns {string}
 */
export const getFrontendHost = () => {
  const frontendConfigObj = getConfigSnapshot()
  const frontendHostValue = frontendConfigObj?.APP?.frontendHost
  if (typeof frontendHostValue === 'string' && frontendHostValue) return frontendHostValue.replace(/\/$/, '')

  if (typeof window !== 'undefined' && window.location?.origin) return window.location.origin
  return 'http://127.0.0.1:5000'
}
