/**
 * 파일명: ModalDocs.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Modal 컴포넌트 문서
 */
import { basicExampleList, sizeExampleList, formExampleList, dragExampleList, positionExampleList } from '../examples/ModalExamples';
import DocSection from '../shared/DocSection';
import CodeBlock from '../shared/CodeBlock';

/**
 * @description Modal 문서 섹션을 구성하고 예제 목록을 렌더링. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const ModalDocs = () => {
  return <DocSection id="modals" title="30. 모달 (Modal)" description={<div>
                    <p>Modal 컴포넌트는 Header, Body, Footer 구조를 가진 팝업 대화상자입니다.</p>
                    <p>5가지 크기(sm, md, lg, xl, full)를 지원하며, 드래그 기능을 선택적으로 활성화할 수 있습니다.</p>
                    <p>ESC 키, 백드롭 클릭으로 닫기가 가능하며, 포커스 트랩을 지원합니다.</p>
                    <ul className="list-disc pl-5 mt-2 text-sm text-gray-600">
                        <li><code>isOpen</code>: 열림 상태</li>
                        <li><code>onClose?</code>: 닫힘 콜백</li>
                        <li><code>size?</code>: 'sm' | 'md' | 'lg' | 'xl' | 'full'</li>
                        <li><code>draggable?</code>: 헤더 드래그 이동</li>
                        <li><code>closeOnBackdrop?</code>: 배경 클릭 시 닫힘</li>
                        <li><code>closeOnEsc?</code>: ESC 키로 닫힘</li>
                        <li><code>top?/left?</code>: 초기 위치 지정</li>
                        <li><code>className?</code>: 추가 Tailwind 클래스</li>
                        <li><code>children</code>: 모달 내부 콘텐츠</li>
                    </ul>
                </div>}>
            <div id="modal-basic" className="mb-8">
                <h3 className="text-lg font-medium mb-4">기본 사용법</h3>
                <div className="grid grid-cols-1 gap-8">
                    <div>
                        {basicExampleList[0].component}
                        <div className="mt-2 text-sm text-gray-600">
                            {basicExampleList[0].description}
                        </div>
                        <CodeBlock code={basicExampleList[0].code} />
                    </div>
                </div>
            </div>

            <div id="modal-sizes" className="mb-8">
                <h3 className="text-lg font-medium mb-4">모달 크기</h3>
                <div className="grid grid-cols-1 gap-8">
                    <div>
                        {sizeExampleList[0].component}
                        <div className="mt-2 text-sm text-gray-600">
                            {sizeExampleList[0].description}
                        </div>
                        <CodeBlock code={sizeExampleList[0].code} />
                    </div>
                </div>
            </div>

            <div id="modal-form" className="mb-8">
                <h3 className="text-lg font-medium mb-4">폼이 포함된 모달</h3>
                <div className="grid grid-cols-1 gap-8">
                    <div>
                        {formExampleList[0].component}
                        <div className="mt-2 text-sm text-gray-600">
                            {formExampleList[0].description}
                        </div>
                        <CodeBlock code={formExampleList[0].code} />
                    </div>
                </div>
            </div>

            <div id="modal-drag" className="mb-8">
                <h3 className="text-lg font-medium mb-4">드래그 가능한 모달</h3>
                <div className="grid grid-cols-1 gap-8">
                    <div>
                        {dragExampleList[0].component}
                        <div className="mt-2 text-sm text-gray-600">
                            {dragExampleList[0].description}
                        </div>
                        <CodeBlock code={dragExampleList[0].code} />
                    </div>
                </div>
            </div>

            <div id="modal-position" className="mb-8">
                <h3 className="text-lg font-medium mb-4">모달 위치 지정</h3>
                <div className="grid grid-cols-1 gap-8">
                    <div>
                        {positionExampleList[0].component}
                        <div className="mt-2 text-sm text-gray-600">
                            {positionExampleList[0].description}
                        </div>
                        <CodeBlock code={positionExampleList[0].code} />
                    </div>
                </div>
            </div>
        </DocSection>;
};

export default ModalDocs;
