/**
 * 파일명: DrawerDocs.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Drawer 컴포넌트 문서
 */

import DocSection from '../shared/DocSection';
import CodeBlock from '../shared/CodeBlock';
import { basicExampleObj, bottomExampleObj, cardExampleObj, leftSizeExampleObj, menuExampleObj, rightSizeExampleObj, topExampleObj } from '../examples/DrawerExamples';

/**
 * @description Drawer 문서 섹션을 구성하고 예제 목록을 렌더링. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const DrawerDocs = () => {
  return (
    <DocSection id="drawers" title="29. 드로어 (Drawer)" description={
      <div>
        <p>화면 측면에서 슬라이드 인 되는 패널입니다. 외부 Collapse 탭과 리사이즈를 지원하며 Tailwind px 클래스 기반 크기 설정이 가능합니다.</p>
        <ul className="list-disc pl-5 mt-2 text-sm text-gray-600">
          <li><code>isOpen</code>: 열림 상태</li>
          <li><code>onClose?</code>: 닫힘 콜백</li>
          <li><code>side?</code>: 위치 'right' | 'left' | 'top' | 'bottom'</li>
          <li><code>size?</code>: 패널 크기 Tailwind 클래스 문자열(<code>min-[1468px]:w-[360px]</code>, <code>min-[1468px]:h-[220px]</code> 등)</li>
          <li><code>closeOnBackdrop?</code>: 배경 클릭 시 닫힘</li>
          <li><code>closeOnEsc?</code>: ESC 키로 닫힘</li>
          <li><code>resizable?</code>: 드래그로 크기 조절</li>
          <li><code>collapseButton?</code>: 접기 버튼 표시</li>
          <li><code>className?</code>: 추가 Tailwind 클래스</li>
          <li><code>children?</code>: 패널 내용</li>
        </ul>
      </div>
    }>
      <div id="drawer-right" className="mb-8">
        <h3 className="text-lg font-medium mb-4">오른쪽 (기본)</h3>
        <div>
          {basicExampleObj.component}
          <div className="mt-2 text-sm text-gray-600">{basicExampleObj.description}</div>
          <CodeBlock code={basicExampleObj.code} />
        </div>
      </div>
      <div id="drawer-right-sized" className="mb-8">
        <h3 className="text-lg font-medium mb-4">오른쪽 (size="min-[1468px]:w-[360px]")</h3>
        <div>
          {rightSizeExampleObj.component}
          <div className="mt-2 text-sm text-gray-600">{rightSizeExampleObj.description}</div>
          <CodeBlock code={rightSizeExampleObj.code} />
        </div>
      </div>
      <div id="drawer-left" className="mb-8">
        <h3 className="text-lg font-medium mb-4">왼쪽 (size="min-[1468px]:w-[420px]")</h3>
        <div>
          {leftSizeExampleObj.component}
          <div className="mt-2 text-sm text-gray-600">{leftSizeExampleObj.description}</div>
          <CodeBlock code={leftSizeExampleObj.code} />
        </div>
      </div>
      <div id="drawer-top" className="mb-8">
        <h3 className="text-lg font-medium mb-4">위쪽 (size="min-[1468px]:h-[220px]")</h3>
        <div>
          {topExampleObj.component}
          <div className="mt-2 text-sm text-gray-600">{topExampleObj.description}</div>
          <CodeBlock code={topExampleObj.code} />
        </div>
      </div>
      <div id="drawer-bottom" className="mb-8">
        <h3 className="text-lg font-medium mb-4">아래쪽 (size="min-[1468px]:h-[260px]")</h3>
        <div>
          {bottomExampleObj.component}
          <div className="mt-2 text-sm text-gray-600">{bottomExampleObj.description}</div>
          <CodeBlock code={bottomExampleObj.code} />
        </div>
      </div>
      <div id="drawer-card" className="mb-8">
        <h3 className="text-lg font-medium mb-4">카드 샘플</h3>
        <div>
          {cardExampleObj.component}
          <div className="mt-2 text-sm text-gray-600">{cardExampleObj.description}</div>
          <CodeBlock code={cardExampleObj.code} />
        </div>
      </div>
      <div id="drawer-menu" className="mb-8">
        <h3 className="text-lg font-medium mb-4">메뉴 샘플</h3>
        <div>
          {menuExampleObj.component}
          <div className="mt-2 text-sm text-gray-600">{menuExampleObj.description}</div>
          <CodeBlock code={menuExampleObj.code} />
        </div>
      </div>
    </DocSection>
  );
};

export default DrawerDocs;
