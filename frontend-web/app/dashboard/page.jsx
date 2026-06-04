/**
 * 파일명: dashboard/page.jsx
 * 작성자: LSH
 * 갱신일: 2026-02-28
 * 설명: 대시보드 페이지 엔트리(서버 컴포넌트)
 */

import DashboardView from "./view";
import { PAGE_CONFIG } from "./initData";
import { loadServerPageData } from "@/app/lib/runtime/pageData";
import LANG_KO from "./lang.ko";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";
export const revalidate = 0;
export const fetchCache = "only-no-store";
export const metadata = {
  title: LANG_KO.page.metadataTitle,
  robots: {
    index: false,
    follow: false,
  },
};

/**
 * @description 대시보드 SSR 초기 데이터를 로드하고 뷰 컴포넌트에 전달
 * 처리 규칙: stats/list 응답은 카드/테이블 초기 렌더링 모델로 정규화해 전달한다.
 * @returns {Promise<JSX.Element>}
 */
const DashboardPage = async () => {
  const { dataObj: initialDataObj, errorObj: initialErrorObj } = await loadServerPageData({
    pageConfig: PAGE_CONFIG,
  });
  return (
    <DashboardView
      initialDataObj={initialDataObj}
      initialErrorObj={initialErrorObj}
    />
  );
};

export default DashboardPage;
