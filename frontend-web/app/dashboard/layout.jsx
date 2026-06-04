/**
 * 파일명: dashboard/layout.jsx
 * 작성자: LSH
 * 갱신일: 2026-02-26
 * 설명: 대시보드 경로 서버 레이아웃 엔트리
 */

import DashboardLayoutClient from "./DashboardLayoutClient";

/**
 * @description 대시보드 하위 페이지 공통 레이아웃을 렌더링. 입력/출력 계약을 함께 명시
 * @param {{ children: React.ReactNode }} props
 * @returns {JSX.Element}
 */
const DashboardLayout = ({ children }) => {

  return <DashboardLayoutClient>{children}</DashboardLayoutClient>;
};

export default DashboardLayout;
