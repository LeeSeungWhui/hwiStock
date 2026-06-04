/**
 * 파일명: SwitchDocs.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Switch 컴포넌트 문서
 */
import DocSection from '../shared/DocSection';
import CodeBlock from '../shared/CodeBlock';
import { accessExampleObj, boundExampleObj, controlExampleObj, stateExampleObj } from '../examples/SwitchExamples';

/**
 * @description Switch 문서 섹션을 구성하고 예제 목록을 렌더링. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const SwitchDocs = () => {
  return <DocSection id="switches" title="11. 스위치 (Switch)" description={<div>
          <p>접근성을 준수하기 위해 role="switch"와 aria-checked를 사용합니다. dataObj와 dataKey 또는 제어 모드를 지원합니다.</p>
          <ul className="list-disc pl-5 mt-2 text-sm text-gray-600">
            <li><code>name?</code>: 그룹/폼 이름</li>
            <li><code>checked?</code>: 선택 상태 제어</li>
            <li><code>defaultChecked?</code>: 초기 선택 상태</li>
            <li><code>dataObj?/dataKey?</code>: 바운드 상태 객체와 키</li>
            <li><code>onChange?/onValueChange?</code>: 값 변경 콜백</li>
            <li><code>disabled?</code>: 비활성화 여부</li>
            <li><code>label?</code>: 스위치 라벨</li>
            <li><code>className?</code>: 추가 Tailwind 클래스</li>
            <li><code>id?</code>: input id 지정</li>
          </ul>
        </div>}>
      <div id="switch-bound" className="mb-8">
        <h3 className="text-lg font-medium mb-4">바운드 모드</h3>
        <div>
          {boundExampleObj.component}
          <div className="mt-2 text-sm text-gray-600">{boundExampleObj.description}</div>
          <CodeBlock code={boundExampleObj.code} />
        </div>
      </div>

      <div id="switch-controlled" className="mb-8">
        <h3 className="text-lg font-medium mb-4">컨트롤드 모드</h3>
        <div>
          {controlExampleObj.component}
          <div className="mt-2 text-sm text-gray-600">{controlExampleObj.description}</div>
          <CodeBlock code={controlExampleObj.code} />
        </div>
      </div>

      <div id="switch-disabled" className="mb-8">
        <h3 className="text-lg font-medium mb-4">비활성/기본값</h3>
        <div>
          {stateExampleObj.component}
          <div className="mt-2 text-sm text-gray-600">{stateExampleObj.description}</div>
          <CodeBlock code={stateExampleObj.code} />
        </div>
      </div>

      <div id="switch-a11y" className="mb-8">
        <h3 className="text-lg font-medium mb-4">접근성</h3>
        <div>
          {accessExampleObj.component}
          <div className="mt-2 text-sm text-gray-600">{accessExampleObj.description}</div>
          <CodeBlock code={accessExampleObj.code} />
        </div>
      </div>
    </DocSection>;
};

export default SwitchDocs;
