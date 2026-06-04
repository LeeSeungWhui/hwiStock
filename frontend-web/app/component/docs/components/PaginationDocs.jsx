/**
 * 파일명: PaginationDocs.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 경량 Pagination 문서 (독립 컴포넌트 + Table 내장 사용)
 */
import { basicExampleObj, limitExampleObj } from '../examples/PaginationExamples';
import DocSection from '../shared/DocSection';
import CodeBlock from '../shared/CodeBlock';

/**
 * @description Pagination 문서 섹션을 구성하고 예제 목록을 렌더링. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const PaginationDocs = () => {
  return <DocSection id="pagination" title="27. 페이지네이션 (Pagination)" description={<div>
      <p>독립 컴포넌트로 제어형 페이지 이동을 제공하며, Table 내장 페이징으로도 사용할 수 있습니다.</p>
      <ul className="list-disc pl-5 mt-2 text-sm text-gray-600">
        <li><code>page</code>: 현재 페이지 번호 (1부터)</li>
        <li><code>pageCount</code>: 전체 페이지 수</li>
        <li><code>onChange</code>: 페이지 변경 시 호출 (새 페이지 전달)</li>
        <li><code>maxButtons?</code>: 표시할 최대 번호 버튼 (기본 7)</li>
        <li><code>showEdges?</code>: 처음/끝 버튼 및 ... 표시 여부 (기본 true)</li>
        <li><code>className?</code>: 래퍼 추가 클래스</li>
      </ul>
    </div>}>
      <div id="pagination-basic" className="mb-8">
        <h3 className="text-lg font-medium mb-4">기본 (독립 컴포넌트)</h3>
        <div>
          {basicExampleObj.component}
          <div className="mt-2 text-sm text-gray-600">{basicExampleObj.description}</div>
          <CodeBlock code={basicExampleObj.code} />
        </div>
      </div>
      <div id="pagination-advanced" className="mb-8">
        <h3 className="text-lg font-medium mb-4">대용량/버튼 제한</h3>
        <div>
          {limitExampleObj.component}
          <div className="mt-2 text-sm text-gray-600">{limitExampleObj.description}</div>
          <CodeBlock code={limitExampleObj.code} />
        </div>
      </div>
    </DocSection>;
};

export default PaginationDocs;
