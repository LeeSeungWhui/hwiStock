/**
 * 파일명: RadioboxExamples.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Radiobox 컴포넌트 예제
 */
import * as Lib from '@/app/lib';
import { useState } from 'react';

/**
 * @description BoundRadioboxDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const BoundRadioboxDemo = () => {
  const [radioDataObj] = useState(() => Lib.EasyObj({
    selectedJob: ''
  }));

  return <div className="space-y-2">
      <Lib.Radiobox name="job" label="개발자" value="developer" dataObj={radioDataObj} dataKey="selectedJob" />
      <Lib.Radiobox name="job" label="디자이너" value="designer" dataObj={radioDataObj} dataKey="selectedJob" />
    </div>;
};

/**
 * @description PaymentRadioboxDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const PaymentRadioboxDemo = () => {
  const [radioDataObj] = useState(() => Lib.EasyObj({
    paymentMethod: ''
  }));

  return <div className="space-y-2">
      <h4 className="text-sm font-medium text-gray-700">결제 수단 선택</h4>
      <Lib.Radiobox name="payment" label="신용카드" value="card" dataObj={radioDataObj} dataKey="paymentMethod" color="#FF6B6B" />
      <Lib.Radiobox name="payment" label="계좌이체" value="bank" dataObj={radioDataObj} dataKey="paymentMethod" color="#4D96FF" />
      <Lib.Radiobox name="payment" label="휴대폰 결제" value="mobile" dataObj={radioDataObj} dataKey="paymentMethod" color="#6BCB77" />
    </div>;
};

/**
 * @description CtrlRadioboxDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const CtrlRadioboxDemo = () => {
  const [optionValue, setOptionValue] = useState('');

  return <div className="space-y-2">
      <Lib.Radiobox name="controlled" label="옵션 1" value="option1" checked={optionValue === 'option1'} onChange={event => setOptionValue(event.target.value)} />
      <Lib.Radiobox name="controlled" label="옵션 2" value="option2" checked={optionValue === 'option2'} onChange={event => setOptionValue(event.target.value)} />
      <div className="text-sm text-gray-600">
        선택된 값: {optionValue || '없음'}
      </div>
    </div>;
};

/**
 * @description Radiobox 예제 계약을 정의. 입력/출력 계약을 함께 명시
 * @updated 2026-02-24
 * 처리 규칙: 상태가 필요한 예제는 demo 컴포넌트 안으로 가두고 계약은 직접 export한다.
 */
export const basicExampleList = [{
  exampleId: 'binding',
  component: <BoundRadioboxDemo />,
  description: '기본 라디오박스 (dataObj/dataKey 바인딩).',
  code: `<Lib.Radiobox
    name="job"
    label="개발자"
    value="developer"
    dataObj={radioDataObj}
    dataKey="selectedJob"
/>`
}, {
  exampleId: 'disabled',
  component: <div className="space-y-2">
      <Lib.Radiobox name="disabled" label="비활성화 1" value="disabled1" disabled />
      <Lib.Radiobox name="disabled" label="비활성화 2" value="disabled2" disabled checked />
    </div>,
  description: '비활성화 상태',
  code: `<Lib.Radiobox
    name="disabled"
    label="비활성화 1"
    value="disabled1"
    disabled
/>`
}];

export const advancedExampleList = [{
  exampleId: 'payment',
  component: <PaymentRadioboxDemo />,
  description: '커스텀 색상',
  code: `<Lib.Radiobox
    name="payment"
    label="신용카드"
    value="card"
    dataObj={radioDataObj}
    dataKey="paymentMethod"
    color="#FF6B6B"
/>`
}, {
  exampleId: 'controlled',
  component: <CtrlRadioboxDemo />,
  description: '제어 컴포넌트 방식',
  code: `const [optionValue, setOptionValue] = useState('');

<Lib.Radiobox
    name="controlled"
    label="옵션 1"
    value="option1"
    checked={optionValue === 'option1'}
    onChange={(event) => setOptionValue(event.target.value)}
/>`
}];
