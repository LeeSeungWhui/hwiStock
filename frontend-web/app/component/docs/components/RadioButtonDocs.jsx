/**
 * 파일명: RadioButtonDocs.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: RadioButton 컴포넌트 문서
 */
import { advancedExampleList, basicExampleList } from '../examples/RadioButtonExamples';
import DocSection from '../shared/DocSection';
import CodeBlock from '../shared/CodeBlock';

/**
 * @description RadioButton 문서 섹션을 구성하고 예제 목록을 렌더링. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const RadioButtonDocs = () => {
    return (
        <DocSection
            id="radiobuttons"
            title="10. 라디오버튼 (RadioButton)" description={
                <div>
                    <p>RadioButton 컴포넌트는 Radiobox와 동일한 방식으로 dataObj와 dataKey를 통해 양방향 바인딩을 지원합니다.</p>
                    <p>버튼 형태로 라디오박스 기능을 제공합니다.</p>
                    <p>name prop이 없을 경우 dataKey 또는 children을 name으로 사용합니다.</p>
                    <ul className="list-disc pl-5 mt-2 text-sm text-gray-600">
                        <li><code>children</code>: 버튼 내부 콘텐츠</li>
                        <li><code>name?</code>: 그룹/폼 이름</li>
                        <li><code>value</code>: 선택 값</li>
                        <li><code>checked?</code>: 선택 상태 제어</li>
                        <li><code>dataObj?/dataKey?</code>: 바운드 상태 객체와 키</li>
                        <li><code>onChange?</code>: 선택 변경 콜백</li>
                        <li><code>color?</code>: 버튼 색상</li>
                        <li><code>disabled?</code>: 비활성화 여부</li>
                        <li><code>className?</code>: 추가 Tailwind 클래스</li>
                    </ul>
                </div>
            }
        >
            <div id="radiobutton-basic" className="mb-8">
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

            <div id="radiobutton-advanced" className="mb-8">
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

export default RadioButtonDocs;
