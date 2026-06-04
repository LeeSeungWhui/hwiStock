/**
 * 파일명: EasyEditorDocs.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: EasyEditor 컴포넌트 문서
 */
import { editorExampleList } from '../examples/EasyEditorExamples';
import DocSection from '../shared/DocSection';
import CodeBlock from '../shared/CodeBlock';

/**
 * @description EasyEditor 문서 섹션을 구성하고 예제 목록을 렌더링. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const EasyEditorDocs = () => {
  return (
    <DocSection
      id="editors"
      title="31. 리치 에디터 (EasyEditor)"
      description={
        <div className="space-y-2 text-sm text-gray-700 leading-relaxed">
          <p>
            <code>EasyEditor</code>는 Tiptap 기반 리치 텍스트 에디터로, EasyObj 바인딩과 프리셋 확장을 통해 쉽게 사용할 수 있습니다.
            기본 직렬화는 JSON이며 <code>serialization="html" | "text"</code>로 모드를 바꿀 수 있습니다.
            글자 크기, 색상, 정렬, 링크, 이미지/파일 첨부, Editor/HTML 모드 전환 등 핵심 기능을 제공합니다.
          </p>
          <ul className="list-disc pl-5 space-y-1">
            <li><code>dataObj</code> + <code>dataKey</code>: EasyObj 객체 바인딩 (JSON이 기본 직렬화)</li>
            <li><code>value</code> + <code>onChange</code>: 컨트롤드 모드</li>
            <li><code>serialization?</code>: <code>'json' | 'html' | 'text'</code> (기본: <code>'json'</code>)</li>
            <li><code>extensions?</code>: Tiptap Extension 배열 (메모이즈되어 불필요한 재생성 방지)</li>
            <li><code>imageUploadUrl?</code>, <code>fileUploadUrl?</code>: 업로드 엔드포인트 (기본 제공 Alert 안내)</li>
            <li><code>onUploadImage?</code>, <code>onUploadFile?</code>: 커스텀 업로드 함수 주입 가능</li>
            <li><code>toolbar?</code>: 툴바 표시 여부 (기본: <code>true</code>)</li>
            <li><code>status?</code>: <code>'idle' | 'loading' | 'error' | 'success'</code>, 상태에 따른 스타일</li>
            <li><code>readOnly?</code>: 읽기 전용 모드 (HTML 모드 전환 시 비활성화)</li>
            <li>Editor/HTML 모드 전환 시 HTML을 즉시 반영하며, 바인딩에도 동기화됩니다.</li>
          </ul>
        </div>
      }
    >
      <div className="space-y-10">
        {editorExampleList.map((example) => (
          <div key={example.anchor} id={example.anchor} className="space-y-3 scroll-mt-24">
            <div>{example.component}</div>
            <p className="text-sm text-gray-600">{example.description}</p>
            <CodeBlock code={example.code} />
          </div>
        ))}
      </div>
    </DocSection>
  );
};

export default EasyEditorDocs;
