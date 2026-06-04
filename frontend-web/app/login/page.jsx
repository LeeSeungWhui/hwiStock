/**
 * 파일명: page.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 로그인 페이지 컴포넌트
 */
import Client from './view'
import { loadServerPageData } from '@/app/lib/runtime/pageData'
import { PAGE_CONFIG } from './initData'
import SharedHydrator from '@/app/common/store/SharedHydrator'
import { cookies } from 'next/headers'
import { AUTH_REASON_COOKIE, NX_COOKIE, parseAuthReason, decodeUriComponentValue, sanitizeInternalPath } from '@/app/lib/runtime/authRedirect'
import LANG_KO from './lang.ko'

export const dynamic = 'force-dynamic'
export const revalidate = 0
export const runtime = 'nodejs'

export const metadata = {
  title: LANG_KO.page.metadataTitle,
  robots: {
    index: false,
    follow: false,
  },
}

/**
 * @description PAGE_CONFIG/쿠키 기반 초기값을 읽어 로그인 클라이언트 뷰에 전달
 * @returns {Promise<JSX.Element>}
 */
const Page = async () => {
  const { dataObj: initialDataObj, errorObj: initialErrorObj } = await loadServerPageData({
    pageConfig: PAGE_CONFIG,
  })
  const sessionData = initialDataObj.session || null

  // 미들웨어가 저장한 httpOnly 쿠키(next-hint)를 읽어 복귀 경로에 사용한다(URL에는 노출되지 않음).
  const cookieStore = await cookies()
  const rawNext = cookieStore.get(NX_COOKIE)?.value || null
  const rawAuthReason = cookieStore.get(AUTH_REASON_COOKIE)?.value || null
  const nextHint = sanitizeInternalPath(decodeUriComponentValue(rawNext), null)
  const authReason = parseAuthReason(rawAuthReason)
  initialDataObj.__pageMeta = { nextHint, authReason }
  const userJson = sessionData && sessionData.result && sessionData.result.username
    ? { userId: sessionData.result.username, name: sessionData.result.username }
    : null
  return (
    <>
      <SharedHydrator userJson={userJson} />
      <Client
        initialDataObj={initialDataObj}
        initialErrorObj={initialErrorObj}
      />
    </>
  )
}

export default Page
