/**
 * 파일명: NumberInputExamples.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: NumberInput 컴포넌트 예제
 */
import { useState } from 'react';
import * as Lib from '@/app/lib';

/**
 * @description BoundNumberDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const BoundNumberDemo = () => {
  const [numberDataObj] = useState(() => Lib.EasyObj({
    qty: 1
  }));

  return <div className="space-y-2">
      <Lib.NumberInput dataObj={numberDataObj} dataKey="qty" min={0} step={1} />
      <div className="text-xs text-gray-600">numberDataObj.qty = {String(numberDataObj.qty)}</div>
    </div>;
};

/**
 * @description RangeNumberDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const RangeNumberDemo = () => {
  const [priceDataObj] = useState(() => Lib.EasyObj({
    price: 0
  }));

  return <Lib.NumberInput dataObj={priceDataObj} dataKey="price" min={0} max={100} step={0.5} />;
};

/**
 * @description NumberInput 예제 계약을 정의. 입력/출력 계약을 함께 명시
 * @updated 2026-02-24
 * 처리 규칙: 단건 섹션은 ExampleObj로 노출하고 상태는 demo 컴포넌트 안에만 둔다.
 */
export const basicExampleObj = {
  exampleId: 'bound',
  component: <BoundNumberDemo />,
  description: '기본: 바운드 + step 1',
  code: `const numberDataObj = Lib.EasyObj({ qty: 1 });

<Lib.NumberInput dataObj={numberDataObj} dataKey="qty" min={0} step={1} />`
};

export const rangeExampleObj = {
  exampleId: 'range',
  component: <RangeNumberDemo />,
  description: 'min/max/step 조합',
  code: '<Lib.NumberInput dataObj={priceDataObj} dataKey="price" min={0} max={100} step={0.5} />'
};

export const unboundExampleObj = {
  exampleId: 'unbound',
  component: <Lib.NumberInput defaultValue={10} step={5} />,
  description: '언바운드 + defaultValue',
  code: '<Lib.NumberInput defaultValue={10} step={5} />'
};
