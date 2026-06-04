/**
 * 파일명: TableDocs.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Table 컴포넌트 문서
 */
import DocSection from '../shared/DocSection';
import CodeBlock from '../shared/CodeBlock';
import { basicExampleObj, cardExampleObj, controlExampleObj, emptyExampleObj, styleExampleObj } from '../examples/TableExamples';

/**
 * @description Table 문서 섹션을 구성하고 예제 목록을 렌더링. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const TableDocs = () => {
  return (
    <DocSection id="tables" title="26. 테이블 (Table)" description={
      <div>
        <p>데이터 테이블과 카드 리스트를 렌더링합니다. 제어형 및 비제어 페이징을 지원하며 URL과 스토리지에 상태를 보존합니다.</p>
        <ul className="list-disc pl-5 mt-2 text-sm text-gray-600">
          <li><code>data</code>: 행 데이터 배열/EasyList</li>
          <li><code>columns</code>: 열 정의 배열</li>
          <li><code>rowKey?</code>: 행 키 결정 함수/키</li>
          <li><code>className?</code>: 래퍼 추가 클래스</li>
          <li><code>headerClassName?/rowClassName?/cellClassName?/rowsClassName?</code>: 세부 스타일</li>
          <li><code>empty?</code>: 빈 상태 메시지</li>
          <li><code>loading?</code>: 로딩 표시</li>
          <li><code>onRowClick?</code>: 행 클릭 콜백</li>
          <li><code>page?/pageSize?/defaultPage?</code>: 현재/페이지당/초기 페이지</li>
          <li><code>onPageChange?</code>: 페이지 변경 콜백</li>
          <li><code>pageParam?/persist?/persistKey?</code>: URL/스토리지 상태 유지</li>
          <li><code>maxPageButtons?</code>: 페이지 버튼 수</li>
          <li><code>variant?</code>: 'table' | 'card'</li>
          <li><code>renderCard?</code>: 카드 모드 렌더 함수</li>
          <li><code>gridClassName?</code>: 카드 모드 grid 클래스</li>
        </ul>
      </div>
    }>
      <div id="table-basic" className="mb-8">
        <h3 className="text-lg font-medium mb-4">기본</h3>
        <div>
          {basicExampleObj.component}
          <div className="mt-2 text-sm text-gray-600">{basicExampleObj.description}</div>
          <CodeBlock code={basicExampleObj.code} />
        </div>
      </div>
      <div id="table-controlled" className="mb-8">
        <h3 className="text-lg font-medium mb-4">제어형 페이지</h3>
        <div>
          {controlExampleObj.component}
          <div className="mt-2 text-sm text-gray-600">{controlExampleObj.description}</div>
          <CodeBlock code={controlExampleObj.code} />
        </div>
      </div>
      <div id="table-card" className="mb-8">
        <h3 className="text-lg font-medium mb-4">카드</h3>
        <div>
          {cardExampleObj.component}
          <div className="mt-2 text-sm text-gray-600">{cardExampleObj.description}</div>
          <CodeBlock code={cardExampleObj.code} />
        </div>
      </div>
      <div id="table-styled" className="mb-8">
        <h3 className="text-lg font-medium mb-4">커스텀 스타일</h3>
        <div>
          {styleExampleObj.component}
          <div className="mt-2 text-sm text-gray-600">{styleExampleObj.description}</div>
          <CodeBlock code={styleExampleObj.code} />
        </div>
      </div>
      <div id="table-empty" className="mb-8">
        <h3 className="text-lg font-medium mb-4">빈 상태</h3>
        <div>
          {emptyExampleObj.component}
          <div className="mt-2 text-sm text-gray-600">{emptyExampleObj.description}</div>
          <CodeBlock code={emptyExampleObj.code} />
        </div>
      </div>
    </DocSection>
  );
};

export default TableDocs;
