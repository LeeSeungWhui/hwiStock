/**
 * 파일명: frontendConfig.test.jsx
 * 작성자: LSH
 * 갱신일: 2025-09-13
 * 설명: 프론트엔드 config 파서 테스트
 */

import { describe, expect, it } from 'vitest'
import { parseIni } from '@/app/common/config/frontendConfig.server'

/**
 * 설명: parseIni가 다양한 타입을 처리하는지 검증한다.
 * 갱신일: 2025-09-13
 */
function buildSampleIni() {
  return `# comment\n[APP]\napi_base_url = http://localhost:5000/api\nretry = 3\n\n[FEATURE_FLAGS]\nenable_mock = true\noptions = {"a":1}\n`;
}

describe('parseIni', () => {
  it('섹션과 값을 객체로 변환한다', () => {
    const ini = buildSampleIni()
    const parsed = parseIni(ini)
    expect(parsed.APP.api_base_url).toBe('http://localhost:5000/api')
    expect(parsed.APP.retry).toBe(3)
    expect(parsed.FEATURE_FLAGS.enable_mock).toBe(true)
    expect(parsed.FEATURE_FLAGS.options).toEqual({ a: 1 })
  })
})
