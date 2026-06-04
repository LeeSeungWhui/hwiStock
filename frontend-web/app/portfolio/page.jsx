/**
 * 파일명: portfolio/page.jsx
 * 작성자: LSH
 * 갱신일: 2026-03-04
 * 설명: 레거시 공개 경로(/portfolio) 포트폴리오 페이지 엔트리
 */

import PortfolioView from "./view";
import { PAGE_CONFIG } from "./initData";
import { loadServerPageData } from "@/app/lib/runtime/pageData";
import LANG_KO from "./lang.ko";

export const metadata = {
  title: LANG_KO.page.metadataTitle,
  description: LANG_KO.page.metadataDescription,
};

/**
 * @description 레거시 공개 경로에서 포트폴리오 콘텐츠를 재사용 뷰로 전달
 * @returns {JSX.Element}
 */
const PortfolioPage = async () => {
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

export default PortfolioPage;
