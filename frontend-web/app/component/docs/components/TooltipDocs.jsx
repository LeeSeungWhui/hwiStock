/**
 * 파일명: TooltipDocs.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 툴팁 문서 섹션
 */
import DocSection from '../shared/DocSection';
import CodeBlock from '../shared/CodeBlock';
import { basicExampleList, directionExampleList, triggerExampleList } from '../examples/TooltipExamples';

/**
 * Tooltip 문서 섹션
 * @date 2025-09-13
 */

/**
 * @description Tooltip 문서 섹션을 구성하고 예제 목록을 렌더링. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const TooltipDocs = () => {
  return <DocSection id="tooltips" title="20. 툴팁 (Tooltip)" description={<div>
        <p>hover, focus 또는 클릭에 반응하는 간단한 툴팁입니다.</p>
        <ul className="list-disc pl-5 mt-2 text-sm text-gray-600">
          <li><code>content</code>: 툴팁 내용</li>
          <li><code>placement?</code>: 위치 'top' | 'bottom' | 'left' | 'right'</li>
          <li><code>trigger?</code>: 'hover' | 'click' | 'focus'</li>
          <li><code>delay?</code>: 표시 지연(ms)</li>
          <li><code>disabled?</code>: 비활성화 여부</li>
          <li><code>textDirection?</code>: 텍스트 방향 'lr' | 'tb'</li>
          <li><code>className?</code>: 추가 Tailwind 클래스</li>
          <li><code>children?</code>: 트리거 요소</li>
        </ul>
      </div>}>
      <div id="tooltip-basic" className="mb-8">
        <h3 className="text-lg font-medium mb-4">기본</h3>
        <div>
          {basicExampleList[0]?.component}
          <div className="mt-2 text-sm text-gray-600">{basicExampleList[0]?.description}</div>
          <CodeBlock code={basicExampleList[0]?.code || ''} />
        </div>
      </div>
      <div id="tooltip-placement" className="mb-8">
        <h3 className="text-lg font-medium mb-4">방향</h3>
        <div>
          {directionExampleList[0]?.component}
          <div className="mt-2 text-sm text-gray-600">{directionExampleList[0]?.description}</div>
          <CodeBlock code={directionExampleList[0]?.code || ''} />
        </div>
      </div>
      <div id="tooltip-trigger" className="mb-8">
        <h3 className="text-lg font-medium mb-4">트리거</h3>
        <div>
          {triggerExampleList[0]?.component}
          <div className="mt-2 text-sm text-gray-600">{triggerExampleList[0]?.description}</div>
          <CodeBlock code={triggerExampleList[0]?.code || ''} />
        </div>
      </div>
    </DocSection>;
};

export default TooltipDocs;
