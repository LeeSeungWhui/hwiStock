"use client";

/**
 * 파일명: SwitchExamples.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Switch 컴포넌트 예제
 */
import * as Lib from '@/app/lib';
import { useState } from 'react';

/**
 * @description BoundSwitchDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const BoundSwitchDemo = () => {
  const [switchDataObj] = useState(() => Lib.EasyObj({
    enabled: false
  }));

  return <div className="flex items-center gap-4">
      <Lib.Switch dataObj={switchDataObj} dataKey="enabled" label={`바운드: ${switchDataObj.enabled ? 'ON' : 'OFF'}`} />
      <span className="text-sm text-gray-600">switchDataObj.enabled = {String(switchDataObj.enabled)}</span>
    </div>;
};

/**
 * @description CtrlSwitchDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const CtrlSwitchDemo = () => {
  const [isLocalOn, setIsLocalOn] = useState(false);

  return <div className="flex items-center gap-4">
      <Lib.Switch checked={isLocalOn} onValueChange={nextValue => setIsLocalOn(nextValue)} label={`컨트롤드: ${isLocalOn ? 'ON' : 'OFF'}`} />
      <span className="text-sm text-gray-600">isLocalOn = {String(isLocalOn)}</span>
    </div>;
};

/**
 * @description A11ySwitchDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const A11ySwitchDemo = () => {
  const [switchDataObj] = useState(() => Lib.EasyObj({
    notifications: true
  }));

  return <div className="flex items-center gap-4">
      <Lib.Switch dataObj={switchDataObj} dataKey="notifications" id="notify-switch" label="알림 허용" />
    </div>;
};

/**
 * @description Switch 예제 계약을 정의. 입력/출력 계약을 함께 명시
 * @updated 2026-02-24
 * 처리 규칙: 단건 섹션은 ExampleObj로 노출하고 상태는 demo 컴포넌트 안에만 둔다.
 */
export const boundExampleObj = {
  exampleId: 'bound',
  component: <BoundSwitchDemo />,
  description: 'dataObj + dataKey 로 상태 바인딩',
  code: `const switchDataObj = Lib.EasyObj({ enabled: false });

<Lib.Switch
  dataObj={switchDataObj}
  dataKey="enabled"
  label={\`바운드: \${switchDataObj.enabled ? 'ON' : 'OFF'}\`}
/>`
};

export const controlExampleObj = {
  exampleId: 'controlled',
  component: <CtrlSwitchDemo />,
  description: '컨트롤드 모드 (checked + onValueChange)',
  code: `const [isLocalOn, setIsLocalOn] = useState(false);

<Lib.Switch
  checked={isLocalOn}
  onValueChange={(nextValue) => setIsLocalOn(nextValue)}
  label={\`컨트롤드: \${isLocalOn ? 'ON' : 'OFF'}\`}
/>`
};

export const stateExampleObj = {
  exampleId: 'disabled',
  component: <div className="flex items-center gap-4">
      <Lib.Switch disabled defaultChecked label="비활성화" />
      <Lib.Switch disabled label="비활성화 (OFF)" />
    </div>,
  description: 'disabled / defaultChecked 조합',
  code: `<Lib.Switch disabled defaultChecked label="비활성화" />
<Lib.Switch disabled label="비활성화 (OFF)" />`
};

export const accessExampleObj = {
  exampleId: 'access',
  component: <A11ySwitchDemo />,
  description: '접근성: id/label 로 명확한 레이블 제공',
  code: `<Lib.Switch
  dataObj={switchDataObj}
  dataKey="notifications"
  id="notify-switch"
  label="알림 허용"
/>`
};
