/**
 * 파일명: getBackendHost.server.js
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 백엔드 호스트 주소를 로드/캐시
 */

import { loadFrontendConfig } from './frontendConfig.server'

let cachedBackendHost = null

const DEFAULT_BACKEND = 'http://127.0.0.1:5001'

/**
 * @description getBackendHost 구성 데이터를 반환. 입력/출력 계약을 함께 명시
 * @updated 2026-02-24
 * 처리 규칙: 입력값과 상태를 검증해 UI/데이터 흐름을 안전하게 유지한다.
 */
export const getBackendHost = async () => {
  if (cachedBackendHost) return cachedBackendHost
  try {
    const frontendConfigObj = await loadFrontendConfig()
    const backendHostValue = frontendConfigObj?.API?.base
      ?? frontendConfigObj?.APP?.backendHost
      ?? frontendConfigObj?.APP?.api_base_url
      ?? frontendConfigObj?.APP?.serverHost
    cachedBackendHost = typeof backendHostValue === 'string' && backendHostValue ? backendHostValue : DEFAULT_BACKEND
  } catch {
    cachedBackendHost = DEFAULT_BACKEND
  }
  return cachedBackendHost
}
