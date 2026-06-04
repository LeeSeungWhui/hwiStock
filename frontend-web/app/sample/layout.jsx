/**
 * 파일명: sample/layout.jsx
 * 작성자: LSH
 * 갱신일: 2026-02-23
 * 설명: 공개 샘플 공통 레이아웃 엔트리
 */

import DemoLayoutClient from "./DemoLayoutClient";

/**
 * @description 공개 샘플 하위 페이지 공통 레이아웃을 렌더링. 입력/출력 계약을 함께 명시
 * @param {{ children: React.ReactNode }} props
 * @returns {JSX.Element}
 */
const DemoLayout = ({ children }) => {

  return <DemoLayoutClient>{children}</DemoLayoutClient>;
};

export default DemoLayout;
