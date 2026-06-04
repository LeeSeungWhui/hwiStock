/**
 * 파일명: InputExamples.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Input 컴포넌트 예제
 */
import { useState } from 'react';
import * as Lib from '@/app/lib';

/**
 * @description BoundInputDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const BoundInputDemo = ({ dataKey, initialDataObj, ...inputProps }) => {
  const [inputDataObj] = useState(() => Lib.EasyObj(initialDataObj));
  return <Lib.Input dataObj={inputDataObj} dataKey={dataKey} {...inputProps} />;
};

/**
 * @description Input 예제 계약을 정의. 입력/출력 계약을 함께 명시
 * @updated 2026-02-24
 * 처리 규칙: 상태가 필요한 예제는 demo 컴포넌트 안으로 가두고 계약은 직접 export한다.
 */
export const basicExampleList = [{
  exampleId: 'basic',
  component: <BoundInputDemo dataKey="basicInput" initialDataObj={{
    basicInput: ''
  }} placeholder="텍스트 입력하세요" />,
  description: '기본 입력',
  code: `<Lib.Input
    dataObj={inputDataObj}
    dataKey="basicInput"
    placeholder="텍스트 입력하세요"
/>`
}, {
  exampleId: 'email',
  component: <BoundInputDemo dataKey="email" initialDataObj={{
    email: ''
  }} type="email" placeholder="이메일을 입력하세요" />,
  description: '이메일 입력',
  code: `<Lib.Input
    dataObj={inputDataObj}
    dataKey="email"
    type="email"
    placeholder="이메일을 입력하세요"
/>`
}];

export const maskExampleList = [{
  exampleId: 'phoneMask',
  component: <BoundInputDemo dataKey="phone" initialDataObj={{
    phone: ''
  }} mask="###-####-####" placeholder="전화번호: 010-1234-5678" />,
  description: '전화번호 마스킹',
  code: `<Lib.Input
    dataObj={inputDataObj}
    dataKey="phone"
    mask="###-####-####"
    placeholder="전화번호: 010-1234-5678"
/>`
}, {
  exampleId: 'businessMask',
  component: <BoundInputDemo dataKey="businessNo" initialDataObj={{
    businessNo: ''
  }} mask="###-##-#####" placeholder="사업자번호 123-45-67890" />,
  description: '사업자번호 마스킹',
  code: `<Lib.Input
    dataObj={inputDataObj}
    dataKey="businessNo"
    mask="###-##-#####"
    placeholder="사업자번호 123-45-67890"
/>`
}];

export const filterExampleList = [{
  exampleId: 'numberLimit',
  component: <BoundInputDemo dataKey="amount" initialDataObj={{
    amount: ''
  }} type="number" maxDigits={10} maxDecimals={2} placeholder="숫자 입력 (최대 10자리, 소수점2자리)" />,
  description: '숫자 입력 (자리수 제한)',
  code: `<Lib.Input
    dataObj={inputDataObj}
    dataKey="amount"
    type="number"
    maxDigits={10}
    maxDecimals={2}
    placeholder="숫자 입력 (최대 10자리, 소수점2자리)"
/>`
}, {
  exampleId: 'alphaNum',
  component: <BoundInputDemo dataKey="code" initialDataObj={{
    code: ''
  }} filter="A-Za-z0-9" placeholder="영문/숫자 입력" />,
  description: '영문/숫자 필터',
  code: `<Lib.Input
    dataObj={inputDataObj}
    dataKey="code"
    filter="A-Za-z0-9"
    placeholder="영문/숫자 입력"
/>`
}, {
  exampleId: 'korean',
  component: <BoundInputDemo dataKey="koreanName" initialDataObj={{
    koreanName: ''
  }} filter="가-힣" placeholder="한글 입력" />,
  description: '한글 필터',
  code: `<Lib.Input
    dataObj={inputDataObj}
    dataKey="koreanName"
    filter="가-힣"
    placeholder="한글 입력"
/>`
}];

export const advancedExampleList = [{
  exampleId: 'error',
  component: <BoundInputDemo dataKey="email" initialDataObj={{
    email: ''
  }} error="이메일 형식이 올바르지 않습니다" placeholder="에러 상태 표시" />,
  description: '에러 상태',
  code: `<Lib.Input
    dataObj={inputDataObj}
    dataKey="email"
    error="이메일 형식이 올바르지 않습니다"
    placeholder="에러 상태 표시"
/>`
}, {
  exampleId: 'price',
  component: <BoundInputDemo dataKey="price" initialDataObj={{
    price: ''
  }} type="number" maxDigits={10} className="text-right" placeholder="금액 입력" suffix="원" />,
  description: '금액 입력 (우측 정렬, 접미사 표시)',
  code: `<Lib.Input
    dataObj={inputDataObj}
    dataKey="price"
    type="number"
    maxDigits={10}
    className="text-right"
    placeholder="금액 입력"
    suffix="원"
/>`
}, {
  exampleId: 'search',
  component: <BoundInputDemo dataKey="searchKeyword" initialDataObj={{
    searchKeyword: ''
  }} prefix={<Lib.Icon icon="ri:RiSearchLine" className="w-5 h-5 text-gray-400" />} placeholder="검색어를 입력하세요" />,
  description: '아이콘이 있는 검색 입력',
  code: `<Lib.Input
    dataObj={inputDataObj}
    dataKey="searchKeyword"
    prefix={<Lib.Icon icon="ri:RiSearchLine" className="w-5 h-5 text-gray-400" />}
    placeholder="검색어를 입력하세요"
/>`
}, {
  exampleId: 'password',
  component: <BoundInputDemo dataKey="password" initialDataObj={{
    password: ''
  }} type="password" placeholder="비밀번호 입력" togglePassword />,
  description: '비밀번호 토글 기능',
  code: `<Lib.Input
    dataObj={inputDataObj}
    dataKey="password"
    type="password"
    placeholder="비밀번호 입력"
    togglePassword
/>`
}];
