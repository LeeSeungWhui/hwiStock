/**
 * 파일명: ssr.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: SSR 유틸리티 모듈
 */
export const buildSSRHeaders = async (extra = {}) => {


  const headersModuleObj = await import('next/headers')
  const cookieStore = await headersModuleObj.cookies()
  const headersList = await headersModuleObj.headers()
  const cookie = cookieStore.getAll().map((cookieItem) => `${cookieItem.name}=${cookieItem.value}`).join('; ')
  const lang = headersList.get('accept-language') || 'en'
  return {
    'Accept-Language': lang,
    Cookie: cookie,
    ...(extra || {}),
  }
}
