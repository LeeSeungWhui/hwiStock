/**
 * 파일명: forgot-password/page.jsx
 * 작성자: LSH
 * 갱신일: 2026-02-22
 * 설명: 비밀번호 찾기 페이지 엔트리
 */

import ForgotPasswordView from "./view";
import { PAGE_CONFIG } from "./initData";
import { loadServerPageData } from "@/app/lib/runtime/pageData";
import LANG_KO from "./lang.ko";

export const dynamic = "force-dynamic";
export const revalidate = 0;
export const metadata = {
  title: LANG_KO.page.metadataTitle,
  robots: {
    index: false,
    follow: false,
  },
};

/**
 * @description 비밀번호 찾기 서버 엔트리에서 화면 컴포넌트를 반환. 입력/출력 계약을 함께 명시
 * @returns {Promise<JSX.Element>}
 */
const ForgotPasswordPage = async () => {
  const { dataObj: initialDataObj, errorObj: initialErrorObj } = await loadServerPageData({
    pageConfig: PAGE_CONFIG,
  });
  return (
    <ForgotPasswordView
      initialDataObj={initialDataObj}
      initialErrorObj={initialErrorObj}
    />
  );
};

export default ForgotPasswordPage;
