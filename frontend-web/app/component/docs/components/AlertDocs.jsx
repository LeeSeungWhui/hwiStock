"use client";

/**
 * 파일명: AlertDocs.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Alert 컴포넌트 문서
 */
import { basicExampleList, typeExampleList, callbackExampleList, focusExampleList } from '../examples/AlertExamples';
import DocSection from '../shared/DocSection';
import CodeBlock from '../shared/CodeBlock';

/**
 * @description Alert 문서 섹션을 구성하고 예제 목록을 렌더링. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const AlertDocs = () => {
  return <DocSection id="alerts" title="17. 알림 (Alert)" description={<div>
          <p>전역 스토어(useGlobalUi)의 showAlert로 간단히 알림을 표시합니다.</p>
          <p>정보/성공/경고/오류 유형을 지원하며 제목과 메시지를 지정할 수 있습니다.</p>
          <ul className="list-disc pl-5 mt-2 text-sm text-gray-600">
            <li><code>title?</code>: 알림 제목 (기본: '알림')</li>
            <li><code>text</code>: 표시 메시지</li>
            <li><code>type?</code>: 'info' | 'success' | 'warning' | 'error'</li>
            <li><code>onClick?</code>: 확인 버튼 클릭 콜백</li>
          </ul>
        </div>}>
      <div id="alert-basic" className="mb-8">
        <h3 className="text-lg font-medium mb-4">기본 사용</h3>
        <div className="grid grid-cols-1 gap-8">
          <div>
            {basicExampleList[0].component}
            <div className="mt-2 text-sm text-gray-600">{basicExampleList[0].description}</div>
            <CodeBlock code={basicExampleList[0].code} />
          </div>
        </div>
      </div>

      <div id="alert-types" className="mb-8">
        <h3 className="text-lg font-medium mb-4">알림 유형</h3>
        <div className="grid grid-cols-1 gap-8">
          <div>
            {typeExampleList[0].component}
            <div className="mt-2 text-sm text-gray-600">{typeExampleList[0].description}</div>
            <CodeBlock code={typeExampleList[0].code} />
          </div>
        </div>
      </div>

      <div id="alert-callback" className="mb-8">
        <h3 className="text-lg font-medium mb-4">콜백 함수</h3>
        <div className="grid grid-cols-1 gap-8">
          <div>
            {callbackExampleList[0].component}
            <div className="mt-2 text-sm text-gray-600">{callbackExampleList[0].description}</div>
            <CodeBlock code={callbackExampleList[0].code} />
          </div>
        </div>
      </div>

      <div id="alert-focus" className="mb-8">
        <h3 className="text-lg font-medium mb-4">포커스 이동</h3>
        <div className="grid grid-cols-1 gap-8">
          <div>
            {focusExampleList[0].component}
            <div className="mt-2 text-sm text-gray-600">{focusExampleList[0].description}</div>
            <CodeBlock code={focusExampleList[0].code} />
          </div>
        </div>
      </div>
    </DocSection>;
};

export default AlertDocs;
