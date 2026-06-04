/**
 * 파일명: BadgeDocs.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Badge 컴포넌트 문서
 */
import DocSection from '../shared/DocSection';
import CodeBlock from '../shared/CodeBlock';
import { variantExampleList, outlineExampleList, sizeExampleList, iconExampleList } from '../examples/BadgeExamples';

/**
 * @description Badge 문서 섹션을 구성하고 예제 목록을 렌더링. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const BadgeDocs = () => {
  return <DocSection id="badges" title="21. 배지/태그 (Badge/Tag)" description={<div>
          <p>상태 표시용 레이블입니다. 색상, 크기, 모양을 지원합니다.</p>
          <ul className="list-disc pl-5 mt-2 text-sm text-gray-600">
            <li><code>children</code>: 표시할 내용</li>
            <li><code>variant?</code>: 색상 스타일 (기본: 'neutral')</li>
            <li><code>size?</code>: 크기 'sm' | 'md' (기본: 'sm')</li>
            <li><code>pill?</code>: 둥근 모양 여부 (기본: false)</li>
            <li><code>className?</code>: 추가 Tailwind 클래스</li>
          </ul>
        </div>}>
      <div id="badge-variants" className="mb-8">
        <h3 className="text-lg font-medium mb-4">색상 Variants</h3>
        <div>
          {variantExampleList[0]?.component}
          <div className="mt-2 text-sm text-gray-600">{variantExampleList[0]?.description}</div>
          <CodeBlock code={variantExampleList[0]?.code || ''} />
        </div>
      </div>

      <div id="badge-outline-pill" className="mb-8">
        <h3 className="text-lg font-medium mb-4">Outline / Pill</h3>
        <div>
          {outlineExampleList[0]?.component}
          <div className="mt-2 text-sm text-gray-600">{outlineExampleList[0]?.description}</div>
          <CodeBlock code={outlineExampleList[0]?.code || ''} />
        </div>
      </div>

      <div id="badge-sizes" className="mb-8">
        <h3 className="text-lg font-medium mb-4">크기</h3>
        <div>
          {sizeExampleList[0]?.component}
          <div className="mt-2 text-sm text-gray-600">{sizeExampleList[0]?.description}</div>
          <CodeBlock code={sizeExampleList[0]?.code || ''} />
        </div>
      </div>

      <div id="badge-icons" className="mb-8">
        <h3 className="text-lg font-medium mb-4">아이콘 포함</h3>
        <div>
          {iconExampleList[0]?.component}
          <div className="mt-2 text-sm text-gray-600">{iconExampleList[0]?.description}</div>
          <CodeBlock code={iconExampleList[0]?.code || ''} />
        </div>
      </div>
    </DocSection>;
};

export default BadgeDocs;
