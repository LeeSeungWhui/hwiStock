/**
 * 파일명: dashboard/tasks/page.jsx
 * 작성자: LSH
 * 갱신일: 2026-02-28
 * 설명: hwiStock 감시 로그 페이지 엔트리(서버 컴포넌트)
 */

import TasksView from "./view";
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
 * @description 감시 로그 SSR 초기 데이터를 로드해 클라이언트 뷰로 전달
 * @returns {Promise<JSX.Element>}
 */
const TasksPage = async () => {
  const { dataObj: initialDataObj, errorObj: initialErrorObj } = await loadServerPageData({
    pageConfig: PAGE_CONFIG,
  });
  return (
    <TasksView
      initialDataObj={initialDataObj}
      initialErrorObj={initialErrorObj}
    />
  );
};

export default TasksPage;
