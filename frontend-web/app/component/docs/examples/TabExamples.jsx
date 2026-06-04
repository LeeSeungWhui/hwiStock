/**
 * 파일명: TabExamples.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Tab 컴포넌트 예제
 */
import * as Lib from '@/app/lib';
import { useState } from 'react';

/**
 * @description BasicTabDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const BasicTabDemo = () => {
  const [tabDataObj] = useState(() => Lib.EasyObj({
    selectedTab: 0
  }));

  return <Lib.Tab dataObj={tabDataObj} dataKey="selectedTab">
      <Lib.Tab.Item title="첫번째 탭">
        <div className="p-4">
          첫번째 탭의 내용입니다.
        </div>
      </Lib.Tab.Item>
      <Lib.Tab.Item title="두번째 탭">
        <div className="p-4">
          두번째 탭의 내용입니다.
        </div>
      </Lib.Tab.Item>
      <Lib.Tab.Item title="세번째 탭">
        <div className="p-4">
          세번째 탭의 내용입니다.
        </div>
      </Lib.Tab.Item>
    </Lib.Tab>;
};

/**
 * @description CtrlTabDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const CtrlTabDemo = () => {
  const [activeTab, setActiveTab] = useState(0);

  return <Lib.Tab tabIndex={activeTab} onChange={setActiveTab}>
      <Lib.Tab.Item title="프로필">
        <div className="p-4 space-y-2">
          <h3 className="font-medium">사용자 프로필</h3>
          <p>tabIndex와 onChange를 직접 연결한 제어 탭 예시입니다.</p>
        </div>
      </Lib.Tab.Item>
      <Lib.Tab.Item title="설정">
        <div className="p-4 space-y-2">
          <h3 className="font-medium">설정</h3>
          <p>tabIndex와 onChange props를 사용합니다.</p>
        </div>
      </Lib.Tab.Item>
    </Lib.Tab>;
};

/**
 * @description StyleTabDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const StyleTabDemo = () => {
  const [tabDataObj] = useState(() => Lib.EasyObj({
    customTab: 0
  }));

  return <Lib.Tab className="bg-gray-100 rounded-lg p-4" dataObj={tabDataObj} dataKey="customTab">
      <Lib.Tab.Item title="커스텀 스타일">
        <div className="p-4">
          className prop으로 커스텀 스타일을 적용할 수 있습니다.
        </div>
      </Lib.Tab.Item>
      <Lib.Tab.Item title="두번째">
        <div className="p-4">
          Tailwind 클래스를 사용해서 쉽게 스타일링이 가능합니다.
        </div>
      </Lib.Tab.Item>
    </Lib.Tab>;
};

/**
 * @description IconTabDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const IconTabDemo = () => {
  const [tabDataObj] = useState(() => Lib.EasyObj({
    iconTab: 0
  }));

  return <Lib.Tab dataObj={tabDataObj} dataKey="iconTab">
      <Lib.Tab.Item title={<div className="flex items-center gap-2">
            <Lib.Icon icon="md:MdHome" className="w-5 h-5" />
            <span>홈</span>
          </div>}>
        <div className="p-4">
          탭 제목에 아이콘과 텍스트를 함께 사용할 수 있습니다.
        </div>
      </Lib.Tab.Item>
      <Lib.Tab.Item title={<div className="flex items-center gap-2">
            <Lib.Icon icon="md:MdSettings" className="w-5 h-5" />
            <span>설정</span>
          </div>}>
        <div className="p-4">
          title prop에 JSX를 전달하여 자유롭게 커스터마이징이 가능합니다.
        </div>
      </Lib.Tab.Item>
    </Lib.Tab>;
};

export const basicExampleObj = {
  exampleId: 'basic',
  component: <BasicTabDemo />,
  description: 'EasyObj를 사용한 기본 탭',
  code: `const tabDataObj = Lib.EasyObj({
    selectedTab: 0
});

<Lib.Tab dataObj={tabDataObj} dataKey="selectedTab">...</Lib.Tab>`
};

export const controlExampleObj = {
  exampleId: 'controlled',
  component: <CtrlTabDemo />,
  description: 'tabIndex와 onChange 제어 예시',
  code: `const [activeTab, setActiveTab] = useState(0);

<Lib.Tab tabIndex={activeTab} onChange={setActiveTab}>...</Lib.Tab>`
};

export const styleExampleObj = {
  exampleId: 'style',
  component: <StyleTabDemo />,
  description: '커스텀 스타일링',
  code: `<Lib.Tab
    className="bg-gray-100 rounded-lg p-4"
    dataObj={tabDataObj}
    dataKey="customTab"
>...</Lib.Tab>`
};

export const iconExampleObj = {
  exampleId: 'icon',
  component: <IconTabDemo />,
  description: '아이콘이 있는 탭',
  code: `<Lib.Tab dataObj={tabDataObj} dataKey="iconTab">...</Lib.Tab>`
};
