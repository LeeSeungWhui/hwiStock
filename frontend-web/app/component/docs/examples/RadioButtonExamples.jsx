/**
 * 파일명: RadioButtonExamples.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: RadioButton 컴포넌트 예제
 */
import * as Lib from '@/app/lib';
import { useState } from 'react';

/**
 * @description BoundRadioBtnDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const BoundRadioBtnDemo = () => {
  const [radioDataObj] = useState(() => Lib.EasyObj({
    selectedSize: ''
  }));

  return <div className="space-x-2">
      <Lib.RadioButton name="size" value="small" dataObj={radioDataObj} dataKey="selectedSize">
        Small
      </Lib.RadioButton>
      <Lib.RadioButton name="size" value="medium" dataObj={radioDataObj} dataKey="selectedSize">
        Medium
      </Lib.RadioButton>
      <Lib.RadioButton name="size" value="large" dataObj={radioDataObj} dataKey="selectedSize">
        Large
      </Lib.RadioButton>
    </div>;
};

/**
 * @description ThemeRadioBtnDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const ThemeRadioBtnDemo = () => {
  const [radioDataObj] = useState(() => Lib.EasyObj({
    selectedTheme: ''
  }));

  return <div className="space-x-2">
      <Lib.RadioButton name="theme" value="light" dataObj={radioDataObj} dataKey="selectedTheme" color="#FF6B6B">
        라이트
      </Lib.RadioButton>
      <Lib.RadioButton name="theme" value="dark" dataObj={radioDataObj} dataKey="selectedTheme" color="#4D96FF">
        다크
      </Lib.RadioButton>
      <Lib.RadioButton name="theme" value="system" dataObj={radioDataObj} dataKey="selectedTheme" color="#6BCB77">
        시스템
      </Lib.RadioButton>
    </div>;
};

/**
 * @description CtrlRadioBtnDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const CtrlRadioBtnDemo = () => {
  const [languageValue, setLanguageValue] = useState('');

  return <div className="space-y-4">
      <div className="space-x-2">
        <Lib.RadioButton name="controlled" value="kr" checked={languageValue === 'kr'} onChange={event => setLanguageValue(event.target.value)}>
          한국어
        </Lib.RadioButton>
        <Lib.RadioButton name="controlled" value="en" checked={languageValue === 'en'} onChange={event => setLanguageValue(event.target.value)}>
          English
        </Lib.RadioButton>
      </div>
      <div className="text-sm text-gray-600">
        선택된 언어: {languageValue || '없음'}
      </div>
    </div>;
};

/**
 * @description RadioButton 예제 계약을 정의. 입력/출력 계약을 함께 명시
 * @updated 2026-02-24
 * 처리 규칙: 상태가 필요한 예제는 demo 컴포넌트 안으로 가두고 계약은 직접 export한다.
 */
export const basicExampleList = [{
  exampleId: 'binding',
  component: <BoundRadioBtnDemo />,
  description: '기본 라디오버튼 (dataObj/dataKey 바인딩).',
  code: `<Lib.RadioButton
    name="size"
    value="small"
    dataObj={radioDataObj}
    dataKey="selectedSize"
>
    Small
</Lib.RadioButton>`
}, {
  exampleId: 'disabled',
  component: <div className="space-x-2">
      <Lib.RadioButton name="disabled" value="disabled1" disabled>
        비활성화 1
      </Lib.RadioButton>
      <Lib.RadioButton name="disabled" value="disabled2" disabled checked>
        비활성화 2
      </Lib.RadioButton>
    </div>,
  description: '비활성화 상태',
  code: `<Lib.RadioButton
    name="disabled"
    value="disabled1"
    disabled
>
    비활성화 1
</Lib.RadioButton>`
}];

export const advancedExampleList = [{
  exampleId: 'theme',
  component: <ThemeRadioBtnDemo />,
  description: '커스텀 색상',
  code: `<Lib.RadioButton
    name="theme"
    value="light"
    dataObj={radioDataObj}
    dataKey="selectedTheme"
    color="#FF6B6B"
>
    라이트
</Lib.RadioButton>`
}, {
  exampleId: 'controlled',
  component: <CtrlRadioBtnDemo />,
  description: '제어 컴포넌트 방식',
  code: `const [languageValue, setLanguageValue] = useState('');

<Lib.RadioButton
    name="controlled"
    value="kr"
    checked={languageValue === 'kr'}
    onChange={(event) => setLanguageValue(event.target.value)}
>
    한국어
</Lib.RadioButton>`
}];
