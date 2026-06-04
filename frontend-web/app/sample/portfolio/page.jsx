/**
 * 파일명: sample/portfolio/page.jsx
 * 작성자: LSH
 * 갱신일: 2026-03-04
 * 설명: 공개 샘플 경로용 포트폴리오 페이지 엔트리
 */

import PortfolioView from "./view";
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
 * @description 공개 샘플 경로에서 포트폴리오 페이지를 렌더링. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const DemoPortfolioPage = async () => {
  const { dataObj: initialDataObj, errorObj: initialErrorObj } = await loadServerPageData({
    pageConfig: PAGE_CONFIG,
  });
  return (
    <PortfolioView
      initialDataObj={initialDataObj}
      initialErrorObj={initialErrorObj}
    />
  );
};

export default DemoPortfolioPage;
