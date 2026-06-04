/**
 * 파일명: CheckboxDocs.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Checkbox 컴포넌트 문서
 */
import { advancedExampleList, basicExampleList } from '../examples/CheckboxExamples';
import DocSection from '../shared/DocSection';
import CodeBlock from '../shared/CodeBlock';

/**
 * @description Checkbox 문서 섹션을 구성하고 예제 목록을 렌더링. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const CheckboxDocs = () => {
    return (
        <DocSection
            id="checkboxes"
            title="7. 체크박스 (Checkbox)" description={
                <div>
                    <p>Checkbox 컴포넌트는 dataObj와 dataKey를 통해 양방향 바인딩을 지원합니다.</p>
                    <p>name prop이 없을 경우 dataKey 또는 label을 name으로 사용합니다.</p>
                    <ul className="list-disc pl-5 mt-2 text-sm text-gray-600">
                        <li><code>label?</code>: 체크박스 옆에 표시할 텍스트</li>
                        <li><code>name?</code>: 그룹/폼 이름</li>
                        <li><code>checked?</code>: 선택 상태 제어</li>
                        <li><code>dataObj?/dataKey?</code>: 바운드 상태 객체와 키</li>
                        <li><code>onChange?</code>: 선택 변경 콜백</li>
                        <li><code>color?</code>: 체크박스 색상 또는 CSS 컬러</li>
                        <li><code>disabled?</code>: 비활성화 여부</li>
                        <li><code>className?</code>: 추가 Tailwind 클래스</li>
                    </ul>
                </div>
            }
        >
            <div id="checkbox-basic" className="mb-8">
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

            <div id="checkbox-advanced" className="mb-8">
                <h3 className="text-lg font-medium mb-4">응용 예시</h3>
                <div className="grid grid-cols-2 gap-8">
                    {advancedExampleList.map((example) => (
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

export default CheckboxDocs;
