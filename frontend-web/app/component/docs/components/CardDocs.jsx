"use client";

/**
 * 파일명: CardDocs.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Card 컴포넌트 문서
 */
import DocSection from '../shared/DocSection';
import CodeBlock from '../shared/CodeBlock';
import { basicExampleList, actionExampleList, plainExampleList, composedExampleList } from '../examples/CardExamples';

/**
 * @description Card 문서 섹션을 구성하고 예제 목록을 렌더링. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const CardDocs = () => {
  return <DocSection id="cards" title="25. 카드 (Card)" description={<div>
          <p>헤더, 본문, 푸터로 구성된 컴포넌트입니다.</p>
          <ul className="list-disc pl-5 mt-2 text-sm text-gray-600">
            <li><code>children</code>: 본문 콘텐츠</li>
            <li><code>title?</code>: 헤더 제목</li>
            <li><code>subtitle?</code>: 제목 아래 보조 텍스트</li>
            <li><code>actions?</code>: 헤더 우측 액션 요소</li>
            <li><code>footer?</code>: 하단 푸터 콘텐츠</li>
            <li><code>className?</code>: 추가 Tailwind 클래스</li>
          </ul>
        </div>}>
      <div id="card-basic" className="mb-8">
        <h3 className="text-lg font-medium mb-4">기본 Card</h3>
        <div>
          {basicExampleList[0]?.component}
          <div className="mt-2 text-sm text-gray-600">{basicExampleList[0]?.description}</div>
          <CodeBlock code={basicExampleList[0]?.code || ''} />
        </div>
      </div>

      <div id="card-actions" className="mb-8">
        <h3 className="text-lg font-medium mb-4">액션/푸터</h3>
        <div>
          {actionExampleList[0]?.component}
          <div className="mt-2 text-sm text-gray-600">{actionExampleList[0]?.description}</div>
          <CodeBlock code={actionExampleList[0]?.code || ''} />
        </div>
      </div>

      <div id="card-plain" className="mb-8">
        <h3 className="text-lg font-medium mb-4">본문 전용</h3>
        <div>
          {plainExampleList[0]?.component}
          <div className="mt-2 text-sm text-gray-600">{plainExampleList[0]?.description}</div>
          <CodeBlock code={plainExampleList[0]?.code || ''} />
        </div>
      </div>

      <div id="card-composed" className="mb-8">
        <h3 className="text-lg font-medium mb-4">조합 예시</h3>
        <div>
          {composedExampleList[0]?.component}
          <div className="mt-2 text-sm text-gray-600">{composedExampleList[0]?.description}</div>
          <CodeBlock code={composedExampleList[0]?.code || ''} />
        </div>
      </div>
    </DocSection>;
};

export default CardDocs;
