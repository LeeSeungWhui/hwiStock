/**
 * 파일명: SelectDocs.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Select 컴포넌트 문서
 */
import { basicExampleList, stateExampleList } from '../examples/SelectExamples';
import DocSection from '../shared/DocSection';
import CodeBlock from '../shared/CodeBlock';

/**
 * @description Select 문서 섹션을 구성하고 예제 목록을 렌더링. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const SelectDocs = () => {
    return (
        <DocSection
            id="selects"
            title="6. 선택 (Select)" description={
                <div>
                    <p>Select 컴포넌트는 dataList의 selected 속성을 통해 선택 상태를 관리합니다.</p>
                    <p>옵션을 선택하면 선택된 항목의 selected가 true로, 나머지는 false로 자동 변경됩니다.</p>
                    <p>또는 <code>dataObj/dataKey</code>를 주면 EasyObj 바인딩으로 동작하며, 선택 값이 자동으로 반영됩니다.</p>
                    <ul className="list-disc pl-5 mt-2 text-sm text-gray-600">
                        <li><code>dataList</code>: 옵션 배열(EasyList 가능)</li>
                        <li><code>valueKey/textKey?</code>: 값/라벨 키 (기본: 'value'/'text')</li>
                        <li><code>dataObj/dataKey?</code>: EasyObj 바인딩 (value prop보다 우선하지 않음)</li>
                        <li><code>value?/onValueChange?</code>: 선택 값을 외부 상태와 동기화할 때 사용</li>
                        <li><code>onChange?</code>: change 이벤트 콜백 (value 포함)</li>
                        <li><code>disabled?</code>: 비활성화 여부</li>
                        <li><code>error?</code>: 에러 상태 표시</li>
                        <li><code>className?</code>: 추가 Tailwind 클래스</li>
                    </ul>
                </div>
            }
        >
            <div id="select-basic" className="mb-8">
                <h3 className="text-lg font-medium mb-4">기본 사용법</h3>
                <div className="grid grid-cols-2 gap-8">
                    {basicExampleList.map((example) => (
                        <div key={example.exampleId}>
                            {example.component}
                            <div className="mt-2 text-sm text-gray-600">
                                {example.description}
                            </div>
                            <CodeBlock code={example.code} />
                        </div>
                    ))}
                </div>
            </div>

            <div id="select-states" className="mb-8">
                <h3 className="text-lg font-medium mb-4">상태</h3>
                <div className="grid grid-cols-2 gap-8">
                    {stateExampleList.map((example) => (
                        <div key={example.exampleId}>
                            {example.component}
                            <div className="mt-2 text-sm text-gray-600">
                                {example.description}
                            </div>
                            <CodeBlock code={example.code} />
                        </div>
                    ))}
                </div>
            </div>
        </DocSection>
    );
};

export default SelectDocs;
