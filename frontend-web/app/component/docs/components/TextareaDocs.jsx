/**
 * 파일명: TextareaDocs.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Textarea 컴포넌트 문서
 */
import DocSection from '../shared/DocSection';
import CodeBlock from '../shared/CodeBlock';
import { boundExampleObj, controlExampleObj, errorExampleObj, readonlyExampleObj } from '../examples/TextareaExamples';

/**
 * @description Textarea 문서 섹션을 구성하고 예제 목록을 렌더링. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const TextareaDocs = () => {
  return (
    <DocSection
      id="textareas"
      title="5. 텍스트영역 (Textarea)" description={
        <div>
          <p>바운드와 컨트롤드 모드를 지원하며 줄바꿈을 보존하고 aria-invalid를 사용합니다.</p>
          <ul className="list-disc pl-5 mt-2 text-sm text-gray-600">
            <li><code>rows?</code>: 기본 줄 수 (기본: 4)</li>
            <li><code>dataObj?/dataKey?</code>: 바운드 상태 객체와 키</li>
            <li><code>value?/defaultValue?</code>: 제어/초기 값</li>
            <li><code>error?</code>: 에러 메시지</li>
            <li><code>onChange?/onValueChange?</code>: 값 변경 콜백</li>
            <li><code>placeholder?</code>: 안내 문구</li>
            <li><code>className?</code>: 추가 Tailwind 클래스</li>
            <li><code>disabled?/readOnly?</code>: 상태 제어</li>
          </ul>
        </div>
      }
    >
      <div id="textarea-bound" className="mb-8">
        <h3 className="text-lg font-medium mb-4">바운드 모드</h3>
        <div>
          {boundExampleObj.component}
          <div className="mt-2 text-sm text-gray-600">{boundExampleObj.description}</div>
          <CodeBlock code={boundExampleObj.code} />
        </div>
      </div>

      <div id="textarea-controlled" className="mb-8">
        <h3 className="text-lg font-medium mb-4">컨트롤드 모드</h3>
        <div>
          {controlExampleObj.component}
          <div className="mt-2 text-sm text-gray-600">{controlExampleObj.description}</div>
          <CodeBlock code={controlExampleObj.code} />
        </div>
      </div>

      <div id="textarea-error" className="mb-8">
        <h3 className="text-lg font-medium mb-4">검증/에러 상태</h3>
        <div>
          {errorExampleObj.component}
          <div className="mt-2 text-sm text-gray-600">{errorExampleObj.description}</div>
          <CodeBlock code={errorExampleObj.code} />
        </div>
      </div>

      <div id="textarea-states" className="mb-8">
        <h3 className="text-lg font-medium mb-4">읽기 전용/비활성</h3>
        <div>
          {readonlyExampleObj.component}
          <div className="mt-2 text-sm text-gray-600">{readonlyExampleObj.description}</div>
          <CodeBlock code={readonlyExampleObj.code} />
        </div>
      </div>
    </DocSection>
  );
};

export default TextareaDocs;
