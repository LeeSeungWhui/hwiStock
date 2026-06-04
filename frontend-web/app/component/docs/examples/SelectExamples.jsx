/**
 * 파일명: SelectExamples.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Select 컴포넌트 바운드/컨트롤드/상태 시나리오 예제
 */
import { useState } from 'react';
import * as Lib from '@/app/lib';

/**
 * @description EasyListSelectDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const EasyListSelectDemo = () => {
  const [jobOptionList] = useState(() => Lib.EasyList([
    { id: '', label: '직무를 선택하세요', placeholder: true, selected: true },
    { id: 'designer', label: '디자이너' },
    { id: 'developer', label: '개발자' },
    { id: 'pm', label: '프로덕트 매니저' }
  ]));

  const selectedItemObj = jobOptionList.find((jobOptionObj) => jobOptionObj.selected);
  const selectedId = selectedItemObj ? String(selectedItemObj.id) : '';

  return <div className="space-y-2">
      <Lib.Select id="select-easylist" dataList={jobOptionList} valueKey="id" textKey="label" status="success" statusMessage="dataList의 selected 플래그와 동기화됩니다." />
      <dl className="text-xs text-gray-600">
        <dt className="font-semibold">현재 선택된 id</dt>
        <dd>{selectedId}</dd>
      </dl>
    </div>;
};

/**
 * @description CtrlSelectDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const CtrlSelectDemo = () => {
  const [jobOptionList] = useState(() => Lib.EasyList([
    { id: '', label: '직무를 선택하세요', placeholder: true, selected: true },
    { id: 'designer', label: '디자이너' },
    { id: 'developer', label: '개발자' },
    { id: 'pm', label: '프로덕트 매니저' }
  ]));
  const [roleValue, setRoleValue] = useState('developer');

  return <div className="space-y-2">
      <Lib.Select id="select-controlled" dataList={jobOptionList} valueKey="id" textKey="label" value={roleValue} onValueChange={setRoleValue} status="info" statusMessage={`value prop: ${roleValue}`} />
      <div className="text-xs text-gray-600">value = {String(roleValue)}</div>
    </div>;
};

/**
 * @description LoadingSelectDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const LoadingSelectDemo = () => {
  const [loadingOptionList] = useState(() => Lib.EasyList([
    { id: '', label: '불러오는 중', placeholder: true, selected: true }
  ]));

  return <Lib.Select id="select-loading" dataList={loadingOptionList} valueKey="id" textKey="label" status="loading" assistiveText="옵션을 불러오는 중입니다." disabled />;
};

/**
 * @description ErrorSelectDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const ErrorSelectDemo = () => {
  const [jobOptionList] = useState(() => Lib.EasyList([
    { id: '', label: '직무를 선택하세요', placeholder: true, selected: true },
    { id: 'designer', label: '디자이너' },
    { id: 'developer', label: '개발자' },
    { id: 'pm', label: '프로덕트 매니저' }
  ]));

  return <Lib.Select id="select-error" dataList={jobOptionList} valueKey="id" textKey="label" status="error" statusMessage="필수 입력 항목입니다." />;
};

/**
 * @description EmptySelectDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const EmptySelectDemo = () => {
  const [emptyOptionList] = useState(() => Lib.EasyList([]));

  return <Lib.Select id="select-empty" dataList={emptyOptionList} status="empty" assistiveText="선택 가능한 항목이 비어 있습니다." />;
};

export const basicExampleList = [{
  exampleId: 'easyList',
  component: <EasyListSelectDemo />,
  description: 'EasyList 모드 — dataList 내부의 selected 플래그만으로 선택 상태를 관리',
  code: `const jobOptionList = Lib.EasyList([
  { id: '', label: '직무를 선택하세요', placeholder: true, selected: true },
  { id: 'designer', label: '디자이너' },
  { id: 'developer', label: '개발자' },
  { id: 'pm', label: '프로덕트 매니저' },
]);

<Lib.Select
  dataList={jobOptionList}
  valueKey="id"
  textKey="label"
  status="success"
  statusMessage="dataList의 selected 플래그와 동기화됩니다."
/>`
}, {
  exampleId: 'controlled',
  component: <CtrlSelectDemo />,
  description: '컨트롤드 모드 — value/onValueChange로 외부 상태와 동기화하면서도 dataList.selected는 자동 갱신',
  code: `const [roleValue, setRoleValue] = useState('developer');

<Lib.Select
  dataList={jobOptionList}
  valueKey="id"
  textKey="label"
  value={roleValue}
  onValueChange={setRoleValue}
  status="info"
  statusMessage={\`value prop: \${roleValue}\`}
/>`
}];

export const stateExampleList = [{
  exampleId: 'loading',
  component: <LoadingSelectDemo />,
  description: '로딩/비활성화 상태 — status="loading" + assistiveText로 라이브 영역 안내',
  code: `<Lib.Select
  dataList={loadingOptionList}
  valueKey="id"
  textKey="label"
  status="loading"
  assistiveText="옵션을 불러오는 중입니다."
  disabled
/>`
}, {
  exampleId: 'error',
  component: <ErrorSelectDemo />,
  description: '에러 상태 — status="error"와 안내 메시지',
  code: `<Lib.Select
  dataList={jobOptionList}
  valueKey="id"
  textKey="label"
  status="error"
  statusMessage="필수 입력 항목입니다."
/>`
}, {
  exampleId: 'empty',
  component: <EmptySelectDemo />,
  description: '빈 상태 — status="empty" 프리셋으로 항목 부재 안내 및 aria-live=assertive 적용',
  code: `<Lib.Select
  dataList={Lib.EasyList([])}
  status="empty"
  assistiveText="선택 가능한 항목이 비어 있습니다."
/>`
}];
