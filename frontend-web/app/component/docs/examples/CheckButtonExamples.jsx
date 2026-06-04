/**
 * 파일명: CheckButtonExamples.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: CheckButton 컴포넌트 예제
 */
import * as Lib from '@/app/lib';
import { useState } from 'react';

/**
 * @description BoundCheckDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const BoundCheckDemo = () => {
  const [checkDataObj] = useState(() => Lib.EasyObj({
    basicCheckButton: false
  }));

  return <Lib.CheckButton dataObj={checkDataObj} dataKey="basicCheckButton">
      기본 체크버튼
    </Lib.CheckButton>;
};

/**
 * @description ColorCheckDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const ColorCheckDemo = () => {
  const [colorDataObj] = useState(() => Lib.EasyObj({
    redButton: false,
    greenButton: false,
    blueButton: false
  }));

  return <div className="space-x-2">
      <Lib.CheckButton color="#FF0000" dataObj={colorDataObj} dataKey="redButton">
        빨간색
      </Lib.CheckButton>
      <Lib.CheckButton color="#4CAF50" dataObj={colorDataObj} dataKey="greenButton">
        초록색
      </Lib.CheckButton>
      <Lib.CheckButton color="#2196F3" dataObj={colorDataObj} dataKey="blueButton">
        파란색
      </Lib.CheckButton>
    </div>;
};

/**
 * @description CtrlCheckDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const CtrlCheckDemo = () => {
  const [isChecked, setIsChecked] = useState(false);

  return <div className="space-y-2">
      <Lib.CheckButton checked={isChecked} onChange={() => setIsChecked(!isChecked)}>
        제어 컴포넌트
      </Lib.CheckButton>
      <div className="text-sm text-gray-600">
        현재 상태: {isChecked ? '활성화' : '비활성화'}
      </div>
    </div>;
};

/**
 * @description CheckButton 예제 계약을 정의. 입력/출력 계약을 함께 명시
 * @updated 2026-02-24
 * 처리 규칙: 상태가 필요한 예제는 demo 컴포넌트 안으로 가두고 계약은 직접 export한다.
 */
export const basicExampleList = [{
  exampleId: 'binding',
  component: <BoundCheckDemo />,
  description: '기본 체크버튼 (dataObj/dataKey 바인딩).',
  code: `<Lib.CheckButton
    dataObj={checkDataObj}
    dataKey="basicCheckButton"
>
    기본 체크버튼
</Lib.CheckButton>`
}, {
  exampleId: 'disabled',
  component: <Lib.CheckButton disabled>
      비활성화 체크버튼
    </Lib.CheckButton>,
  description: '비활성화 상태',
  code: `<Lib.CheckButton disabled>
    비활성화 체크버튼
</Lib.CheckButton>`
}];

export const advancedExampleList = [{
  exampleId: 'colors',
  component: <ColorCheckDemo />,
  description: '다양한 색상',
  code: `<Lib.CheckButton color="#FF0000" dataObj={colorDataObj} dataKey="redButton">
    빨간색
</Lib.CheckButton>
<Lib.CheckButton color="#4CAF50" dataObj={colorDataObj} dataKey="greenButton">
    초록색
</Lib.CheckButton>
<Lib.CheckButton color="#2196F3" dataObj={colorDataObj} dataKey="blueButton">
    파란색
</Lib.CheckButton>`
}, {
  exampleId: 'controlled',
  component: <CtrlCheckDemo />,
  description: '제어 컴포넌트 방식',
  code: `const [isChecked, setIsChecked] = useState(false);

<Lib.CheckButton
    checked={isChecked}
    onChange={() => setIsChecked(!isChecked)}
>
    제어 컴포넌트
</Lib.CheckButton>`
}];
