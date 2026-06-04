/**
 * 파일명: dashboard/settings/page.jsx
 * 작성자: LSH
 * 갱신일: 2026-02-23
 * 설명: hwiStock 운영 정책 페이지 엔트리(서버 컴포넌트)
 */

import SettingsView from "./view";
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
 * @description 운영 정책 초기 데이터 로딩 후 클라이언트 뷰에 전달
 * @returns {Promise<JSX.Element>}
 */
const SettingsPage = async () => {
  const { dataObj, errorObj } = await loadServerPageData({
    pageConfig: PAGE_CONFIG,
  });
  return <SettingsView initialDataObj={dataObj} initialErrorObj={errorObj} />;
};

export default SettingsPage;
