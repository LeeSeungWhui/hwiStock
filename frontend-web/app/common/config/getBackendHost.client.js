/**
 * 파일명: getBackendHost.client.js
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 클라이언트 컨텍스트에서 백엔드 호스트를 조회
 */

import { getConfigSnapshot } from '@/app/common/store/SharedStore'

/**
 * @description config 스냅샷에서 백엔드 호스트를 우선순위로 해석
 * @returns {string}
 */
export const getBackendHost = () => {
  const frontendConfigObj = getConfigSnapshot()
  const backendHostValue = frontendConfigObj?.API?.base
    ?? frontendConfigObj?.APP?.backendHost
    ?? frontendConfigObj?.APP?.api_base_url
    ?? frontendConfigObj?.APP?.serverHost
  return typeof backendHostValue === 'string' && backendHostValue ? backendHostValue : 'http://127.0.0.1:5001'
}
