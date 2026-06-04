"use client";

/**
 * 파일명: TextareaExamples.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Textarea 컴포넌트 예제
 */
import * as Lib from '@/app/lib';
import { useState } from 'react';

/**
 * @description BoundTextareaDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const BoundTextareaDemo = () => {
  const [textDataObj] = useState(() => Lib.EasyObj({
    memo: '초기 메모'
  }));

  return <div>
      <div className="mb-2 text-sm text-gray-600">바운드 모드</div>
      <Lib.Textarea dataObj={textDataObj} dataKey="memo" rows={4} placeholder="메모를 입력하세요" />
      <div className="mt-1 text-xs text-gray-500">textDataObj.memo = {textDataObj.memo}</div>
    </div>;
};

/**
 * @description CtrlTextareaDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const CtrlTextareaDemo = () => {
  const [textValue, setTextValue] = useState('로컬 상태');

  return <div>
      <div className="mb-2 text-sm text-gray-600">컨트롤드 모드</div>
      <Lib.Textarea value={textValue} onValueChange={setTextValue} rows={3} />
      <div className="mt-1 text-xs text-gray-500">value = {textValue}</div>
    </div>;
};

/**
 * @description ErrorTextareaDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const ErrorTextareaDemo = () => {
  const [textDataObj] = useState(() => Lib.EasyObj({
    memo: '초기 메모'
  }));

  return <div>
      <div className="mb-2 text-sm text-gray-600">검증/에러 상태</div>
      <Lib.Textarea dataObj={textDataObj} dataKey="memo" rows={4} error={textDataObj.memo.length < 10} placeholder="10자 이상 입력" />
      <div className="mt-1 text-xs text-red-600">{textDataObj.memo.length < 10 ? '10자 이상 입력해주세요' : '정상'}</div>
    </div>;
};

/**
 * @description Textarea 예제 계약을 정의. 입력/출력 계약을 함께 명시
 * @updated 2026-02-24
 * 처리 규칙: 단건 섹션은 ExampleObj로 노출하고 상태는 demo 컴포넌트 안에만 둔다.
 */
export const boundExampleObj = {
  exampleId: 'bound',
  component: <BoundTextareaDemo />,
  description: 'dataObj + dataKey 로 상태 바인딩',
  code: `const textDataObj = Lib.EasyObj({ memo: '' });

<Lib.Textarea
  dataObj={textDataObj}
  dataKey="memo"
  rows={4}
  placeholder="메모를 입력하세요"
/>`
};

export const controlExampleObj = {
  exampleId: 'controlled',
  component: <CtrlTextareaDemo />,
  description: '컨트롤드 모드 (value + onValueChange)',
  code: `const [textValue, setTextValue] = useState('');

<Lib.Textarea
  value={textValue}
  onValueChange={setTextValue}
  rows={3}
/>`
};

export const errorExampleObj = {
  exampleId: 'error',
  component: <ErrorTextareaDemo />,
  description: 'error prop 과 aria-invalid 활용',
  code: `<Lib.Textarea
  dataObj={textDataObj}
  dataKey="memo"
  rows={4}
  error={textDataObj.memo.length < 10}
  placeholder="10자 이상 입력"
/>
<div className="mt-1 text-xs text-red-600">{textDataObj.memo.length < 10 ? '10자 이상 입력해주세요' : '정상'}</div>`
};

export const readonlyExampleObj = {
  exampleId: 'readonly',
  component: <div className="flex flex-col gap-3">
      <Lib.Textarea placeholder="읽기 전용" value="내용 편집 불가" readOnly />
      <Lib.Textarea placeholder="비활성화" disabled />
    </div>,
  description: 'readOnly / disabled 상태',
  code: `<Lib.Textarea placeholder="읽기 전용" value="내용 편집 불가" readOnly />
<Lib.Textarea placeholder="비활성화" disabled />`
};
