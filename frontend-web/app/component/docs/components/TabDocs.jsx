/**
 * 파일명: TabDocs.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Tab 컴포넌트 문서
 */
import { basicExampleObj, controlExampleObj, iconExampleObj, styleExampleObj } from '../examples/TabExamples';
import DocSection from '../shared/DocSection';
import CodeBlock from '../shared/CodeBlock';

/**
 * @description Tab 문서 섹션을 구성하고 예제 목록을 렌더링. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const TabDocs = () => {
    return (
        <DocSection
            id="tabs"
            title="28. 탭 (Tab)" description={
                <div>
                    <p>Tab 컴포넌트는 Tab.Item을 사용하여 탭 패널을 구성합니다.</p>
                    <p>기본 상태는 EasyObj 바인딩을 우선 사용하고, 제어 props 동작 설명용 예제에서만 useState를 함께 보여줍니다.</p>
                    <p>className prop을 통해 커스텀 스타일링을 지원합니다.</p>
                    <ul className="list-disc pl-5 mt-2 text-sm text-gray-600">
                        <li><code>dataObj?/dataKey?</code>: 현재 탭 인덱스 바인딩</li>
                        <li><code>tabIndex?</code>: 초기 탭 인덱스</li>
                        <li><code>onChange?</code>: 탭 변경 시 호출</li>
                        <li><code>className?</code>: 래퍼 추가 클래스</li>
                        <li><code>children</code>: <code>Tab.Item</code> 목록</li>
                    </ul>
                </div>
            }
        >
            <div id="tab-basic" className="mb-8">
                <h3 className="text-lg font-medium mb-4">기본 사용법</h3>
                <div className="grid grid-cols-1 gap-8">
                    <div>
                        {basicExampleObj.component}
                        <div className="mt-2 text-sm text-gray-600">
                            {basicExampleObj.description}
                        </div>
                        <CodeBlock code={basicExampleObj.code} />
                    </div>
                </div>
            </div>

            <div id="tab-controlled" className="mb-8">
                <h3 className="text-lg font-medium mb-4">제어 컴포넌트</h3>
                <div className="grid grid-cols-1 gap-8">
                    <div>
                        {controlExampleObj.component}
                        <div className="mt-2 text-sm text-gray-600">
                            {controlExampleObj.description}
                        </div>
                        <CodeBlock code={controlExampleObj.code} />
                    </div>
                </div>
            </div>

            <div id="tab-styled" className="mb-8">
                <h3 className="text-lg font-medium mb-4">스타일링</h3>
                <div className="grid grid-cols-1 gap-8">
                    <div>
                        {styleExampleObj.component}
                        <div className="mt-2 text-sm text-gray-600">
                            {styleExampleObj.description}
                        </div>
                        <CodeBlock code={styleExampleObj.code} />
                    </div>
                </div>
            </div>

            <div id="tab-icons" className="mb-8">
                <h3 className="text-lg font-medium mb-4">아이콘 탭</h3>
                <div className="grid grid-cols-1 gap-8">
                    <div>
                        {iconExampleObj.component}
                        <div className="mt-2 text-sm text-gray-600">
                            {iconExampleObj.description}
                        </div>
                        <CodeBlock code={iconExampleObj.code} />
                    </div>
                </div>
            </div>
        </DocSection>
    );
};

export default TabDocs;
