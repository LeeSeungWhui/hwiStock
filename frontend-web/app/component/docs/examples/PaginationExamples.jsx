/**
 * 파일명: PaginationExamples.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Pagination 컴포넌트 사용 예제 모음
 */
import * as Lib from '@/app/lib';
import { useState } from 'react';

/**
 * @description BasicPageDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const BasicPageDemo = () => {
  const [pageNo, setPageNo] = useState(2);

  return <div className="flex flex-col gap-2 items-start">
      <Lib.Pagination page={pageNo} pageCount={12} onChange={setPageNo} />
      <div className="text-sm text-gray-600">현재 페이지: {pageNo} / 12</div>
    </div>;
};

/**
 * @description LimitPageDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const LimitPageDemo = () => {
  const [pageNo, setPageNo] = useState(5);

  return <div className="flex flex-col gap-2 items-start">
      <Lib.Pagination page={pageNo} pageCount={50} maxButtons={5} onChange={setPageNo} />
      <div className="text-sm text-gray-600">현재 페이지: {pageNo} / 50</div>
    </div>;
};

/**
 * @description Pagination 예제 계약을 정의. 입력/출력 계약을 함께 명시
 * @updated 2026-02-24
 * 처리 규칙: 단건 섹션은 ExampleObj로 노출하고 상태는 demo 컴포넌트 안에만 둔다.
 */
export const basicExampleObj = {
  exampleId: 'basic',
  component: <BasicPageDemo />,
  description: '기본 제어형 페이지네이션 (page/onChange)',
  code: `const [pageNo, setPageNo] = useState(2);

<Lib.Pagination page={pageNo} pageCount={12} onChange={setPageNo} />`
};

export const limitExampleObj = {
  exampleId: 'limit',
  component: <LimitPageDemo />,
  description: '버튼 수 제한(maxButtons=5) 대용량 페이지',
  code: `const [pageNo, setPageNo] = useState(5);

<Lib.Pagination page={pageNo} pageCount={50} maxButtons={5} onChange={setPageNo} />`
};
