/**
 * 파일명: TimeInputExamples.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: TimeInput 컴포넌트 예제
 */
import { useState } from 'react';
import * as Lib from '@/app/lib';

/**
 * @description BoundTimeDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const BoundTimeDemo = () => {
  const [timeDataObj] = useState(() => Lib.EasyObj({
    time: ''
  }));

  return <div className="space-y-2">
      <Lib.TimeInput dataObj={timeDataObj} dataKey="time" />
      <div className="text-xs text-gray-600">timeDataObj.time = {String(timeDataObj.time)}</div>
    </div>;
};

/**
 * @description TimeInput 예제 계약을 정의. 입력/출력 계약을 함께 명시
 * @updated 2026-02-24
 * 처리 규칙: 상태가 필요한 예제는 demo 컴포넌트 안으로 가두고 계약은 직접 export한다.
 */
export const timeExampleList = [{
  exampleId: 'bound',
  component: <BoundTimeDemo />,
  description: '기본: 바운드',
  code: `const timeDataObj = Lib.EasyObj({ time: '' });

<Lib.TimeInput dataObj={timeDataObj} dataKey="time" />`
}, {
  exampleId: 'step',
  component: <Lib.TimeInput defaultValue="09:30" step={60} />,
  description: '기본값 + 분 단위(step)',
  code: '<Lib.TimeInput defaultValue="09:30" step={60} />'
}];
