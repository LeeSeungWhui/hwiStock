/**
 * 파일명: DropdownDocs.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Dropdown 문서 (EasyList 기반)
 */
import { alignExampleObj, basicExampleObj, presetExampleObj, styledExampleObj, triggerExampleObj, variantExampleObj } from '../examples/DropdownExamples';
import DocSection from '../shared/DocSection';
import CodeBlock from '../shared/CodeBlock';

/**
 * @description Dropdown 문서 섹션을 구성하고 예제 목록을 렌더링. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const DropdownDocs = () => {
  return (
    <DocSection id="dropdowns" title="15. 드롭다운 (Dropdown)" description={<div>
      <p>EasyList(dataList) 기반. 선택 상태는 dataList.selected에 반영되므로 별도 useState가 필요 없습니다. 키보드(↑/↓/Enter/ESC)와 외부 클릭 닫힘 지원.</p>
      <ul className="list-disc pl-5 mt-2 text-sm text-gray-600">
        <li><code>dataList</code>: 항목 배열 또는 EasyList (label, value, selected, disabled)</li>
        <li><code>open?</code>: 외부에서 열림 상태 제어</li>
        <li><code>defaultOpen?</code>: 초기 열림 상태</li>
        <li><code>onOpenChange?</code>: 열림 상태 변경 시 콜백</li>
        <li><code>onSelect?</code>: 항목 선택 시 콜백 (선택 항목 반환)</li>
        <li><code>trigger?</code>: 버튼 대신 사용할 노드 또는 render-prop</li>
        <li><code>labelKey?</code>/<code>valueKey?</code>: 라벨/값 키 (기본 'label'/'value')</li>
        <li><code>placeholder?</code>: 선택 없음 표시 텍스트</li>
        <li><code>variant?</code>: 'outlined' | 'filled' | 'text'</li>
        <li><code>size?</code>: 'sm' | 'md' | 'lg'</li>
        <li><code>rounded?</code>: 모서리 class (기본 'rounded-lg')</li>
        <li><code>elevation?</code>: shadow class (기본 'shadow-md')</li>
        <li><code>buttonClassName?</code>/<code>iconClassName?</code>: 버튼/아이콘 추가 클래스</li>
        <li><code>menuClassName?</code>/<code>itemClassName?</code>/<code>activeClassName?</code>: 메뉴/항목/활성 항목 클래스</li>
        <li><code>selectedItemClassName?</code>: 선택 항목 텍스트 클래스</li>
        <li><code>showCheck?</code>: 선택 체크 표시 여부 (기본 true)</li>
        <li><code>multiSelect?</code>: 다중 선택 모드 (선택해도 자동으로 닫히지 않음)</li>
        <li><code>side?</code>/<code>align?</code>: 메뉴 위치/정렬</li>
        <li><code>closeOnSelect?</code>: 선택 후 자동 닫힘 여부 (기본 true)</li>
        <li><code>disabled?</code>: 드롭다운 비활성화</li>
        <li><code>className?</code>: 루트 추가 클래스</li>
      </ul>
    </div>}>
      <div id="dropdown-basic" className="mb-8">
        <h3 className="text-lg font-medium mb-4">기본</h3>
        <div>
          {basicExampleObj.component}
          <div className="mt-2 text-sm text-gray-600">{basicExampleObj.description}</div>
          <CodeBlock code={basicExampleObj.code} />
        </div>
      </div>
      <div id="dropdown-custom-style" className="mb-8">
        <h3 className="text-lg font-medium mb-4">커스텀 스타일</h3>
        <div>
          {styledExampleObj.component}
          <div className="mt-2 text-sm text-gray-600">{styledExampleObj.description}</div>
          <CodeBlock code={styledExampleObj.code} />
        </div>
      </div>
      <div id="dropdown-styles" className="mb-8">
        <h3 className="text-lg font-medium mb-4">스타일 변형</h3>
        <div>
          {variantExampleObj.component}
          <div className="mt-2 text-sm text-gray-600">{variantExampleObj.description}</div>
          <CodeBlock code={variantExampleObj.code} />
        </div>
      </div>
      <div id="dropdown-custom-trigger" className="mb-8">
        <h3 className="text-lg font-medium mb-4">커스텀 트리거</h3>
        <div>
          {triggerExampleObj.component}
          <div className="mt-2 text-sm text-gray-600">{triggerExampleObj.description}</div>
          <CodeBlock code={triggerExampleObj.code} />
        </div>
      </div>
      <div id="dropdown-placement" className="mb-8">
        <h3 className="text-lg font-medium mb-4">위치/정렬</h3>
        <div>
          {alignExampleObj.component}
          <div className="mt-2 text-sm text-gray-600">{alignExampleObj.description}</div>
          <CodeBlock code={alignExampleObj.code} />
        </div>
      </div>
      <div id="dropdown-preselected" className="mb-8">
        <h3 className="text-lg font-medium mb-4">사전 선택</h3>
        <div>
          {presetExampleObj.component}
          <div className="mt-2 text-sm text-gray-600">{presetExampleObj.description}</div>
          <CodeBlock code={presetExampleObj.code} />
        </div>
      </div>
    </DocSection>
  );
};

export default DropdownDocs;
