"use client";

/**
 * 파일명: ToastDocs.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Toast 컴포넌트 문서
 */
import { basicExampleList, typeExampleList, positionExampleList, durationExampleList } from '../examples/ToastExamples';
import DocSection from '../shared/DocSection';
import CodeBlock from '../shared/CodeBlock';

/**
 * @description Toast 문서 섹션을 구성하고 예제 목록을 렌더링. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const ToastDocs = () => {
  return <DocSection id="toasts" title="19. 토스트 (Toast)" description={<div>
          <p>전역 스토어(useGlobalUi)의 showToast로 간단한 알림 배너를 표시합니다.</p>
          <p>정보/성공/경고/오류 유형, 6가지 위치, 지속시간 제어를 지원합니다.</p>
          <ul className="list-disc pl-5 mt-2 text-sm text-gray-600">
            <li><code>message</code>: 표시 내용</li>
            <li><code>type?</code>: 'info' | 'success' | 'warning' | 'error'</li>
            <li><code>position?</code>: top/bottom - left/center/right</li>
            <li><code>duration?</code>: 자동 닫힘 시간(ms), <code>Infinity</code>로 무한</li>
          </ul>
        </div>}>
      <div id="toast-basic" className="mb-8">
        <h3 className="text-lg font-medium mb-4">기본 사용</h3>
        <div className="grid grid-cols-1 gap-8">
          <div>
            {basicExampleList[0].component}
            <div className="mt-2 text-sm text-gray-600">{basicExampleList[0].description}</div>
            <CodeBlock code={basicExampleList[0].code} />
          </div>
        </div>
      </div>

      <div id="toast-types" className="mb-8">
        <h3 className="text-lg font-medium mb-4">토스트 유형</h3>
        <div className="grid grid-cols-1 gap-8">
          <div>
            {typeExampleList[0].component}
            <div className="mt-2 text-sm text-gray-600">{typeExampleList[0].description}</div>
            <CodeBlock code={typeExampleList[0].code} />
          </div>
        </div>
      </div>

      <div id="toast-positions" className="mb-8">
        <h3 className="text-lg font-medium mb-4">토스트 위치</h3>
        <div className="grid grid-cols-1 gap-8">
          <div>
            {positionExampleList[0].component}
            <div className="mt-2 text-sm text-gray-600">{positionExampleList[0].description}</div>
            <CodeBlock code={positionExampleList[0].code} />
          </div>
        </div>
      </div>

      <div id="toast-duration" className="mb-8">
        <h3 className="text-lg font-medium mb-4">토스트 지속시간</h3>
        <div className="grid grid-cols-1 gap-8">
          <div>
            {durationExampleList[0].component}
            <div className="mt-2 text-sm text-gray-600">{durationExampleList[0].description}</div>
            <CodeBlock code={durationExampleList[0].code} />
          </div>
        </div>
      </div>
    </DocSection>;
};

export default ToastDocs;
