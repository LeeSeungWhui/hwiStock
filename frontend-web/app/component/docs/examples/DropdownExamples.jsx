/**
 * 파일명: DropdownExamples.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Dropdown 컴포넌트 사용 예제 모음 (EasyList 기반, 내부 선택 상태 관리)
 */
import { useState } from 'react';
import * as Lib from '@/app/lib';

/**
 * @description ActionDropDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const ActionDropDemo = () => {
  const [lastAction, setLastAction] = useState('없음');
  const [actionList] = useState(() => Lib.EasyList([{
    label: '항목 1',
    value: 'one'
  }, {
    label: '항목 2',
    value: 'two'
  }, {
    label: '비활성 항목',
    value: 'disabled',
    disabled: true
  }]));

  return <div className="flex flex-col gap-2 items-start">
      <Lib.Dropdown dataList={actionList} trigger={<span>행 액션</span>} onSelect={actionItemObj => {
        const label = actionItemObj?.get ? actionItemObj.get('label') : actionItemObj?.label;
        setLastAction(label || '없음');
      }} />
      <div className="text-sm text-gray-600">
        마지막 액션: {lastAction}
      </div>
    </div>;
};

/**
 * @description VariantDropDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const VariantDropDemo = () => {
  const [fruitOptionList] = useState(() => Lib.EasyList([{
    label: '사과',
    value: 'apple'
  }, {
    label: '바나나',
    value: 'banana'
  }, {
    label: '체리',
    value: 'cherry'
  }]));

  return <div className="flex flex-col gap-2 items-start">
      <Lib.Dropdown dataList={fruitOptionList} variant="filled" size="lg" elevation="shadow-lg" />
    </div>;
};

/**
 * @description TriggerDropDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const TriggerDropDemo = () => {
  const [sortLabel, setSortLabel] = useState('최신순');
  const [sortOptionList] = useState(() => Lib.EasyList([{
    label: '최신순',
    value: 'latest',
    selected: true
  }, {
    label: '오래된순',
    value: 'oldest'
  }, {
    label: '제목순',
    value: 'title'
  }]));

  return <div className="flex flex-col gap-2 items-start">
      <Lib.Dropdown dataList={sortOptionList} placeholder="정렬 기준 선택" variant="text" trigger={({
      selectedLabel
    }) => <span className="inline-flex items-center gap-2 text-blue-700">
                <Lib.Icon icon="ri:RiCircleLine" className="text-blue-700" size="16px" />
                {selectedLabel ?? '정렬 기준'}
              </span>} onSelect={sortItemObj => {
      const label = sortItemObj?.get ? sortItemObj.get('label') : sortItemObj?.label;
      setSortLabel(label || '');
    }} />
      <div className="text-sm text-gray-600">
        현재 정렬 기준: {sortLabel}
      </div>
    </div>;
};

/**
 * @description AlignDropDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const AlignDropDemo = () => {
  const [placementMenuList] = useState(() => Lib.EasyList([{
    label: 'Top',
    value: 'top'
  }, {
    label: 'Middle',
    value: 'mid'
  }, {
    label: 'Bottom',
    value: 'bot'
  }]));

  return <div className="flex flex-col gap-2 items-start">
      <Lib.Dropdown dataList={placementMenuList} side="top" align="end" />
    </div>;
};

/**
 * @description PresetDropDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const PresetDropDemo = () => {
  const [presetChoiceList] = useState(() => Lib.EasyList([{
    label: '선택 A',
    value: 'A',
    selected: true
  }, {
    label: '선택 B',
    value: 'B'
  }, {
    label: '선택 C',
    value: 'C'
  }]));

  return <div className="flex flex-col gap-2 items-start">
      <Lib.Dropdown dataList={presetChoiceList} />
    </div>;
};

/**
 * @description MultiDropDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const MultiDropDemo = () => {
  const [multiRoleList] = useState(() => Lib.EasyList([{
    label: '개발',
    value: 'dev',
    selected: true
  }, {
    label: '디자인',
    value: 'design'
  }, {
    label: '기획',
    value: 'pm'
  }]));

  return <div className="flex flex-col gap-2 items-start">
      <Lib.Dropdown dataList={multiRoleList} multiSelect placeholder="역할 선택 (다중 선택)" />
      <div className="text-sm text-gray-600">
        선택된 항목은 multiRoleList 내부의 <code>selected</code> 플래그로만 관리되고,
        드롭다운은 바깥을 클릭하거나 트리거를 다시 눌러야 닫힌다.
      </div>
    </div>;
};

export const basicExampleObj = {
  exampleId: 'basic',
  component: <ActionDropDemo />,
  description: '테이블 행 우측 ⋯ 같은 액션 메뉴 — 선택 시 onSelect로 액션 처리하고 닫힌다.',
  code: `const [lastAction, setLastAction] = useState('없음');

<Dropdown
  dataList={actionList}
  trigger={<span>행 액션</span>}
  onSelect={(actionItemObj) => {
    const label = actionItemObj?.label;
    setLastAction(label || '없음');
  }}
/>`
};

export const variantExampleObj = {
  exampleId: 'variant',
  component: <VariantDropDemo />,
  description: '스타일 변형: filled + lg + shadow-lg',
  code: '<Dropdown dataList={fruitOptionList} variant="filled" size="lg" elevation="shadow-lg" />'
};

export const triggerExampleObj = {
  exampleId: 'trigger',
  component: <TriggerDropDemo />,
  description: '정렬 기준 선택 드롭다운 — 선택 시 정렬 기준 상태만 바꾸는 필터/정렬 메뉴.',
  code: `const [sortLabel, setSortLabel] = useState('최신순');

<Dropdown
  dataList={sortOptionList}
  variant="text"
  placeholder="정렬 기준 선택"
  trigger={({ selectedLabel }) => (
    <span>{selectedLabel ?? '정렬 기준'}</span>
  )}
  onSelect={(sortItemObj) => {
    const label = sortItemObj?.label;
    setSortLabel(label || '');
  }}
/>`
};

export const alignExampleObj = {
  exampleId: 'align',
  component: <AlignDropDemo />,
  description: '메뉴 위치/정렬: side="top" align="end"',
  code: '<Dropdown dataList={placementMenuList} side="top" align="end" />'
};

export const presetExampleObj = {
  exampleId: 'preset',
  component: <PresetDropDemo />,
  description: '사전 선택(selected: true) 값 표시',
  code: '<Dropdown dataList={presetChoiceList} />'
};

export const styledExampleObj = {
  exampleId: 'multi',
  component: <MultiDropDemo />,
  description: 'multiSelect 모드 — 여러 항목을 체크해도 닫히지 않고, selected 플래그만 토글',
  code: '<Dropdown dataList={multiRoleList} multiSelect placeholder="역할 선택 (다중 선택)" />'
};
