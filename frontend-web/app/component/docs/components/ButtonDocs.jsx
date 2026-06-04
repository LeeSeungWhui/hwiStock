/**
 * 파일명: ButtonDocs.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Button 컴포넌트 문서
 */
import { variantExampleList, sizeExampleList } from '../examples/ButtonExamples';
import DocSection from '../shared/DocSection';
import CodeBlock from '../shared/CodeBlock';

/**
 * @description Button 문서 섹션을 구성하고 예제 목록을 렌더링. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const ButtonDocs = () => {
  return <DocSection id="buttons" title="2. 버튼 (Button)" description={<div>
                    <p>Button 컴포넌트는 className prop을 통해 Tailwind CSS로 스타일을 커스터마이징할 수 있습니다.</p>
                    <p>기본 스타일을 유지하면서 추가적인 스타일을 적용하거나, 완전히 새로운 스타일을 정의할 수 있습니다.</p>
                    <ul className="list-disc pl-5 mt-2 text-sm text-gray-600">
                        <li><code>children</code>: 버튼 내용</li>
                        <li><code>variant?</code>: 버튼 색상 스타일 (기본: 'primary')</li>
                        <li><code>size?</code>: 버튼 크기 'sm' | 'md' | 'lg' (기본: 'md')</li>
                        <li><code>icon?</code>: 아이콘 이름 (react-icons)</li>
                        <li><code>iconPosition?</code>: 아이콘 위치 'left' | 'right' (기본: 'left')</li>
                        <li><code>disabled?</code>: 비활성화 상태</li>
                        <li><code>loading?</code>: 로딩 스피너 표시</li>
                        <li><code>onClick?</code>: 클릭 핸들러</li>
                        <li><code>className?</code>: 추가 Tailwind 클래스</li>
                        <li><code>type?</code>: HTML 버튼 타입 (기본: 'button')</li>
                    </ul>
                </div>}>
            <div id="button-variants" className="mb-8">
                <h3 className="text-lg font-medium mb-4">버튼 종류</h3>
                <div className="grid grid-cols-4 gap-8">
                    {variantExampleList.map(example => <div key={example.exampleId}>
                            {example.component}
                            <div className="mt-2 text-sm text-gray-600">
                                {example.description}
                            </div>
                            <CodeBlock code={example.code} />
                        </div>)}
                </div>
            </div>

            <div id="button-sizes" className="mb-8">
                <h3 className="text-lg font-medium mb-4">버튼 크기</h3>
                <div className="grid grid-cols-4 gap-8">
                    {sizeExampleList.map(example => <div key={example.exampleId}>
                            {example.component}
                            <div className="mt-2 text-sm text-gray-600">
                                {example.description}
                            </div>
                            <CodeBlock code={example.code} />
                        </div>)}
                </div>
            </div>
        </DocSection>;
};

export default ButtonDocs;
