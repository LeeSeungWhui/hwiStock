/**
 * 파일명: component/page.jsx
 * 작성자: LSH
 * 갱신일: 2026-02-24
 * 설명: 컴포넌트 문서 페이지 엔트리(서버 컴포넌트)
 */
import ComponentsView from "./view";
import { PAGE_CONFIG } from "./initData";
import { loadServerPageData } from "@/app/lib/runtime/pageData";

/**
 * @description 컴포넌트 문서 화면의 초기 데이터 로딩 후 클라이언트 뷰 전달
 * @returns {Promise<JSX.Element>}
 */
const ComponentsPage = async () => {
  const { dataObj, errorObj } = await loadServerPageData({
    pageConfig: PAGE_CONFIG,
  });
  return (
    <ComponentsView
      initialDataObj={dataObj}
      initialErrorObj={errorObj}
    />
  );
};

export default ComponentsPage
