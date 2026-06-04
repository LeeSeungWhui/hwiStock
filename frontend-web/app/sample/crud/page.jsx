/**
 * 파일명: sample/crud/page.jsx
 * 작성자: LSH
 * 갱신일: 2026-03-04
 * 설명: 공개 CRUD 샘플 페이지 엔트리
 */

import CrudDemoView from "./view";
import { PAGE_CONFIG } from "./initData";
import { loadServerPageData } from "@/app/lib/runtime/pageData";
import LANG_KO from "./lang.ko";

export const metadata = {
  title: LANG_KO.page.metadataTitle,
  description: LANG_KO.page.metadataDescription,
};
export const dynamic = "force-dynamic";
export const runtime = "nodejs";
export const revalidate = 0;

/**
 * @description 공개 CRUD 샘플 페이지를 렌더링. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const CrudDemoPage = async () => {
  const { dataObj: initialDataObj, errorObj: initialErrorObj } = await loadServerPageData({
    pageConfig: PAGE_CONFIG,
  });
  return (
    <CrudDemoView
      initialDataObj={initialDataObj}
      initialErrorObj={initialErrorObj}
    />
  );
};

export default CrudDemoPage;
