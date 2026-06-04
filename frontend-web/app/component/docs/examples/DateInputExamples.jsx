/**
 * 파일명: DateInputExamples.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: DateInput 컴포넌트 예제
 */
import { useState } from 'react';
import * as Lib from '@/app/lib';

/**
 * @description BoundDateDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const BoundDateDemo = () => {
  const [dateDataObj] = useState(() => Lib.EasyObj({
    date: ''
  }));

  return <div className="space-y-2">
      <Lib.DateInput dataObj={dateDataObj} dataKey="date" />
      <div className="text-xs text-gray-600">dateDataObj.date = {String(dateDataObj.date)}</div>
    </div>;
};

/**
 * @description DateInput 예제 계약을 정의. 입력/출력 계약을 함께 명시
 * @updated 2026-02-24
 * 처리 규칙: 상태가 필요한 예제는 demo 컴포넌트 안으로 가두고 계약은 직접 export한다.
 */
export const dateExampleList = [{
  exampleId: 'bound',
  component: <BoundDateDemo />,
  description: '기본: 바운드',
  code: `const dateDataObj = Lib.EasyObj({ date: '' });

<Lib.DateInput dataObj={dateDataObj} dataKey="date" />`
}, {
  exampleId: 'range',
  component: <Lib.DateInput defaultValue="2025-01-01" min="2025-01-01" max="2025-12-31" />,
  description: 'min/max + 기본값',
  code: '<Lib.DateInput defaultValue="2025-01-01" min="2025-01-01" max="2025-12-31" />'
}];
