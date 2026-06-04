/**
 * 파일명: CheckboxExamples.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Checkbox 컴포넌트 예제
 */
import * as Lib from '@/app/lib';
import { useState } from 'react';

/**
 * @description BoundCheckboxDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const BoundCheckboxDemo = () => {
  const [checkboxDataObj] = useState(() => Lib.EasyObj({
    basicCheckbox: false
  }));

  return <Lib.Checkbox label="기본 체크박스" dataObj={checkboxDataObj} dataKey="basicCheckbox" />;
};

/**
 * @description ColorCheckboxDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const ColorCheckboxDemo = () => {
  const [checkboxDataObj] = useState(() => Lib.EasyObj({
    primary: false,
    red: false,
    green: false
  }));

  return <div className="space-y-2">
      <Lib.Checkbox label="기본 색상 (Primary)" dataObj={checkboxDataObj} dataKey="primary" color="primary" />
      <Lib.Checkbox label="커스텀 빨간색" dataObj={checkboxDataObj} dataKey="red" color="#FF0000" />
      <Lib.Checkbox label="커스텀 초록색" dataObj={checkboxDataObj} dataKey="green" color="rgb(34, 197, 94)" />
    </div>;
};

/**
 * @description CtrlCheckboxDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const CtrlCheckboxDemo = () => {
  const [isChecked, setIsChecked] = useState(false);

  return <div className="space-y-2">
      <Lib.Checkbox label="제어 컴포넌트" checked={isChecked} onChange={event => setIsChecked(event.target.checked)} />
      <div className="text-sm text-gray-600">
        현재 상태: {isChecked ? '체크됨' : '체크 해제됨'}
      </div>
    </div>;
};

/**
 * @description TermsCheckboxDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const TermsCheckboxDemo = () => {
  const [termsDataObj] = useState(() => Lib.EasyObj({
    termsAgreed: false,
    privacyAgreed: false,
    marketingAgreed: false
  }));

  return <div className="space-y-2">
      <h4 className="text-sm font-medium text-gray-700">약관 동의</h4>
      <Lib.Checkbox name="terms" label="[필수] 서비스 이용약관 동의" dataObj={termsDataObj} dataKey="termsAgreed" />
      <Lib.Checkbox name="privacy" label="[필수] 개인정보 처리방침 동의" dataObj={termsDataObj} dataKey="privacyAgreed" />
      <Lib.Checkbox name="marketing" label="[선택] 마케팅 정보 수신 동의" dataObj={termsDataObj} dataKey="marketingAgreed" />
    </div>;
};

/**
 * @description Checkbox 예제 계약을 정의. 입력/출력 계약을 함께 명시
 * @updated 2026-02-24
 * 처리 규칙: 상태가 필요한 예제는 demo 컴포넌트 안으로 가두고 계약은 직접 export한다.
 */
export const basicExampleList = [{
  exampleId: 'binding',
  component: <BoundCheckboxDemo />,
  description: '기본 체크박스 (dataObj/dataKey 바인딩).',
  code: `<Lib.Checkbox
    label="기본 체크박스"
    dataObj={checkboxDataObj}
    dataKey="basicCheckbox"
/>`
}, {
  exampleId: 'disabled',
  component: <Lib.Checkbox label="비활성화 체크박스" disabled />,
  description: '비활성화 상태',
  code: `<Lib.Checkbox
    label="비활성화 체크박스"
    disabled
/>`
}];

export const advancedExampleList = [{
  exampleId: 'colors',
  component: <ColorCheckboxDemo />,
  description: '다양한 색상',
  code: `<Lib.Checkbox
    label="기본 색상 (Primary)"
    dataObj={checkboxDataObj}
    dataKey="primary"
    color="primary"
/>
<Lib.Checkbox
    label="커스텀 빨간색"
    dataObj={checkboxDataObj}
    dataKey="red"
    color="#FF0000"
/>`
}, {
  exampleId: 'controlled',
  component: <CtrlCheckboxDemo />,
  description: '제어 컴포넌트 방식',
  code: `const [isChecked, setIsChecked] = useState(false);

<Lib.Checkbox
    label="제어 컴포넌트"
    checked={isChecked}
    onChange={(event) => setIsChecked(event.target.checked)}
/>`
}, {
  exampleId: 'terms',
  component: <TermsCheckboxDemo />,
  description: '실제 사용 예시 (약관 동의)',
  code: `<Lib.Checkbox
    name="terms"
    label="[필수] 서비스 이용약관 동의"
    dataObj={termsDataObj}
    dataKey="termsAgreed"
/>`
}];
