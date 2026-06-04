/**
 * 파일명: app/page.jsx
 * 작성자: LSH
 * 갱신일: 2026-06-05
 * 설명: 루트 페이지 서버 엔트리
 */

import { redirect } from "next/navigation";

export const dynamic = "force-dynamic";
export const revalidate = 0;
export const runtime = "nodejs";

/**
 * @description 루트는 템플릿 랜딩 대신 /dashboard로 위임한다.
 * @note 인증 분기는 middleware.js에서 단일 처리한다.
 */
const HomePage = async () => {
  redirect("/dashboard");
};

export default HomePage;
