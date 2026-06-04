/**
 * 파일명: SkeletonDocs.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Skeleton 컴포넌트 문서
 */
import DocSection from '../shared/DocSection';
import CodeBlock from '../shared/CodeBlock';
import { textExampleList, avatarExampleList, cardExampleList } from '../examples/SkeletonExamples';

/**
 * @description Skeleton 문서 섹션을 구성하고 예제 목록을 렌더링. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const SkeletonDocs = () => {
  return <DocSection id="skeletons" title="23. 스켈레톤 (Skeleton)" description={<div>
        <p>로딩 중 콘텐츠 구조를 힌트로 보여주는 플레이스홀더입니다.</p>
        <ul className="list-disc pl-5 mt-2 text-sm text-gray-600">
          <li><code>variant?</code>: 'rect' | 'text' | 'circle'</li>
          <li><code>lines?</code>: 텍스트 라인 수 (variant='text')</li>
          <li><code>circleSize?</code>: 원형 크기(px)</li>
          <li><code>className?</code>: 추가 Tailwind 클래스</li>
        </ul>
      </div>}>
      <div id="skeleton-text" className="mb-8">
        <h3 className="text-lg font-medium mb-4">텍스트</h3>
        <div>
          {textExampleList[0]?.component}
          <div className="mt-2 text-sm text-gray-600">{textExampleList[0]?.description}</div>
          <CodeBlock code={textExampleList[0]?.code || ''} />
        </div>
      </div>
      <div id="skeleton-composed" className="mb-8">
        <h3 className="text-lg font-medium mb-4">아바타 + 텍스트</h3>
        <div>
          {avatarExampleList[0]?.component}
          <div className="mt-2 text-sm text-gray-600">{avatarExampleList[0]?.description}</div>
          <CodeBlock code={avatarExampleList[0]?.code || ''} />
        </div>
      </div>
      <div id="skeleton-card" className="mb-8">
        <h3 className="text-lg font-medium mb-4">카드 스켈레톤</h3>
        <div>
          {cardExampleList[0]?.component}
          <div className="mt-2 text-sm text-gray-600">{cardExampleList[0]?.description}</div>
          <CodeBlock code={cardExampleList[0]?.code || ''} />
        </div>
      </div>
    </DocSection>;
};

export default SkeletonDocs;
