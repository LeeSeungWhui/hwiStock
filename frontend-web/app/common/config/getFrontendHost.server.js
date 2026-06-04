/**
 * 파일명: getFrontendHost.server.js
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 프론트엔드 호스트 주소를 로드/캐시
 */

import { loadFrontendConfig } from './frontendConfig.server'

let cachedFrontendHost = null

const DEFAULT_FRONTEND = 'http://127.0.0.1:5000'

/**
 * @description getFrontendHost 구성 데이터를 반환. 입력/출력 계약을 함께 명시
 * @updated 2026-02-24
 * 처리 규칙: 입력값과 상태를 검증해 UI/데이터 흐름을 안전하게 유지한다.
 */
export const getFrontendHost = async () => {
  if (cachedFrontendHost) return cachedFrontendHost
  try {
    const frontendConfigObj = await loadFrontendConfig()
    const frontendHostValue = frontendConfigObj?.APP?.frontendHost
    cachedFrontendHost = typeof frontendHostValue === 'string' && frontendHostValue ? frontendHostValue.replace(/\/$/, '') : DEFAULT_FRONTEND
  } catch {
    cachedFrontendHost = DEFAULT_FRONTEND
  }
  return cachedFrontendHost
}
