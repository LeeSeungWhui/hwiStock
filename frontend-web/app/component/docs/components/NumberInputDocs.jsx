/**
 * 파일명: NumberInputDocs.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: NumberInput 컴포넌트 문서
 */
import DocSection from '../shared/DocSection';
import CodeBlock from '../shared/CodeBlock';
import { basicExampleObj, rangeExampleObj, unboundExampleObj } from '../examples/NumberInputExamples';

/**
 * @description NumberInput 문서 섹션을 구성하고 예제 목록을 렌더링. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const NumberInputDocs = () => {
  return <DocSection id="number-inputs" title="12. 숫자 입력 (Number)" description={<div>
          <p>스텝 버튼이 있는 숫자 입력입니다. EasyObj 바운드와 컨트롤드 모드를 지원합니다.</p>
          <ul className="list-disc pl-5 mt-2 text-sm text-gray-600">
            <li><code>value?/defaultValue?</code>: 제어/초기 값</li>
            <li><code>min?/max?</code>: 허용 범위</li>
            <li><code>step?</code>: 증감 단위 (기본: 1)</li>
            <li><code>dataObj?/dataKey?</code>: 바운드 상태 객체와 키</li>
            <li><code>placeholder?</code>: 안내 문구</li>
            <li><code>onChange?/onValueChange?</code>: 값 변경 콜백</li>
            <li><code>className?</code>: 추가 Tailwind 클래스</li>
            <li><code>disabled?</code>: 비활성화 여부</li>
            <li><code>readOnly?</code>: 읽기 전용</li>
            <li><code>id?</code>: input id 지정</li>
          </ul>
        </div>}>
      <div id="number-basic" className="mb-8">
        <h3 className="text-lg font-medium mb-4">기본</h3>
        <div>
          {basicExampleObj.component}
          <div className="mt-2 text-sm text-gray-600">{basicExampleObj.description}</div>
          <CodeBlock code={basicExampleObj.code} />
        </div>
      </div>

      <div id="number-range" className="mb-8">
        <h3 className="text-lg font-medium mb-4">범위/스텝</h3>
        <div>
          {rangeExampleObj.component}
          <div className="mt-2 text-sm text-gray-600">{rangeExampleObj.description}</div>
          <CodeBlock code={rangeExampleObj.code} />
        </div>
      </div>

      <div id="number-unbound" className="mb-8">
        <h3 className="text-lg font-medium mb-4">언바운드</h3>
        <div>
          {unboundExampleObj.component}
          <div className="mt-2 text-sm text-gray-600">{unboundExampleObj.description}</div>
          <CodeBlock code={unboundExampleObj.code} />
        </div>
      </div>
    </DocSection>;
};

export default NumberInputDocs;
