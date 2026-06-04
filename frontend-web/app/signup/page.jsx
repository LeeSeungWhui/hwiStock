/**
 * 파일명: signup/page.jsx
 * 작성자: LSH
 * 갱신일: 2026-02-22
 * 설명: 회원가입 페이지 엔트리
 */

import SignupView from "./view";
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
 * @description 회원가입 서버 엔트리에서 SignupView를 반환. 입력/출력 계약을 함께 명시
 * @returns {Promise<JSX.Element>}
 */
const SignupPage = async () => {
  const { dataObj: initialDataObj, errorObj: initialErrorObj } = await loadServerPageData({
    pageConfig: PAGE_CONFIG,
  });
  return <SignupView initialDataObj={initialDataObj} initialErrorObj={initialErrorObj} />;
};

export default SignupPage;
