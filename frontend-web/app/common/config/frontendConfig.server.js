/**
 * 파일명: frontendConfig.server.js
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 프론트엔드 config.ini 로더
 */

import { safeJsonParse } from "@/app/lib/runtime/json";

let cachedConfig = null

/**
 * 설명: config.ini 파일을 읽어 JSON 객체로 변환. 입력/출력 계약 명시
 * 우선순위: config.ini > config_prod.ini > config_dev.ini (env 변수 미사용)
 */
export const loadFrontendConfig = async () => {
  if (typeof window !== 'undefined') {
    return cachedConfig ?? {}
  }
  if (cachedConfig) return cachedConfig

  const { existsSync, readFileSync } = await import('node:fs')
  const { join } = await import('node:path')

  const projectRootPath = process.cwd()

  // 환경 변수 의존 제거. 운영/개발 선택은 배포 환경에서 config.ini 계열 파일로 결정한다.
  // 존재 순서: config.ini > config_prod.ini > config_dev.ini
  const candidates = [
    join(projectRootPath, 'config.ini'),
    join(projectRootPath, 'config_prod.ini'),
    join(projectRootPath, 'config_qa.ini'),
    join(projectRootPath, 'config_dev.ini'),
  ]

  for (const candidatePath of candidates) {
    try {
      if (existsSync(candidatePath)) {
        const iniText = readFileSync(candidatePath, 'utf-8')
        cachedConfig = parseIni(iniText)
        return cachedConfig
      }
    } catch {
      continue
    }
  }
  cachedConfig = {}
  return cachedConfig
}

/**
 * 설명: INI 문자열을 객체로 변환. 입력/출력 계약 명시
 * 섹션([SECTION])은 객체 키, 섹션 밖 키는 최상위 매핑
 */
export const parseIni = (iniText) => {
  const iniConfigObj = {}
  let currentSection = iniConfigObj
  const iniLineList = iniText.split(/\r?\n/)
  for (const rawLine of iniLineList) {
    const line = rawLine.trim()
    const isIgnorableLine = !line || line.startsWith('#') || line.startsWith(';')
    if (isIgnorableLine) continue
    if (line.startsWith('[')) {
      if (line.endsWith(']')) {
        const sectionName = line.slice(1, -1).trim()
        if (!sectionName) continue
        if (!iniConfigObj[sectionName]) iniConfigObj[sectionName] = {}
        currentSection = iniConfigObj[sectionName]
        continue
      }
    }
    const equalsIndex = line.indexOf('=')
    if (equalsIndex === -1) continue
    const configKey = line.slice(0, equalsIndex).trim()
    const valueRaw = line.slice(equalsIndex + 1).trim()
    if (!configKey) continue
    currentSection[configKey] = coerceValue(valueRaw)
  }
  return iniConfigObj
}

/**
 * 설명: INI 값 문자열을 타입에 맞게 변환. 입력/출력 계약 명시
 * true/false, 숫자, JSON 객체/배열 포맷 자동 변환, 실패 시 문자열 유지
 */
const coerceValue = (valueRaw) => {
  if (valueRaw === '') return ''

  const isSingleQuoted = valueRaw.startsWith("'") ? valueRaw.endsWith("'") : false
  const isDoubleQuoted = valueRaw.startsWith('"') ? valueRaw.endsWith('"') : false
  if (isSingleQuoted || isDoubleQuoted) {
    const unquotedValue = valueRaw.slice(1, -1)
    return coerceValue(unquotedValue)
  }
  const lowerCaseValue = valueRaw.toLowerCase()
  if (lowerCaseValue === 'true') return true
  if (lowerCaseValue === 'false') return false
  const numericValue = Number(valueRaw)
  if (!Number.isNaN(numericValue) && valueRaw.trim() !== '') return numericValue
  try {
    const startsWithObject = valueRaw.startsWith('{')
    const startsWithArray = valueRaw.startsWith('[')
    const looksLikeJson =
      (startsWithObject ? valueRaw.endsWith('}') : false) ||
      (startsWithArray ? valueRaw.endsWith(']') : false)
    if (looksLikeJson) {
      const notParsed = Symbol('notParsed')
      const parsedValue = safeJsonParse(valueRaw, notParsed)
      if (parsedValue !== notParsed) return parsedValue
    }
  } catch {
    return valueRaw
  }
  return valueRaw
}
