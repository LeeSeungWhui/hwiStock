/**
 * 파일명: EasyEditorExamples.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: EasyEditor 컴포넌트 예제
 */
import * as Lib from '@/app/lib';

/**
 * @description HTML 문자열을 요약 텍스트로 변환. 입력/출력 계약을 함께 명시
 * @returns {string}
 * @updated 2026-02-27
 */
const summariseHtml = (value) => {
  const editorText = typeof value === 'string' ? value : '';
  const stripped = editorText.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
  if (!stripped) return '내용 없음';
  return stripped.length > 40 ? `${stripped.slice(0, 40)} ...` : stripped;
};

/**
 * @description NoticeEditorDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const NoticeEditorDemo = () => {
  const editorDataObj = Lib.EasyObj({
    announcement: '<p></p>'
  });

  return <div className="space-y-3">
      <Lib.EasyEditor dataObj={editorDataObj} dataKey="announcement" serialization="html" placeholder="팀 공지를 작성하세요" label="공지 작성" helperText="툴바에서 폰트, 색상, 정렬, HTML 모드를 시험해보세요." />
      <div className="rounded border bg-gray-50 p-3 text-sm text-gray-600">
        <strong>현재 값 요약:</strong>{' '}
        {summariseHtml(editorDataObj.announcement)}
      </div>
    </div>;
};

/**
 * @description GuideEditorDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const GuideEditorDemo = () => {
  const editorDataObj = Lib.EasyObj({
    onboardingGuide: '<h2>온보딩 가이드</h2><p>새로운 팀원을 환영합니다. 아래 체크리스트를 확인하세요.</p>'
  });

  return <div className="space-y-3">
      <Lib.EasyEditor dataObj={editorDataObj} dataKey="onboardingGuide" serialization="html" placeholder="온보딩 가이드를 작성하세요" label="가이드 편집" status="success" helperText="status='success'로 상태 프리셋을 표시합니다." />
      <div className="rounded border bg-gray-50 p-3 text-sm text-gray-600">
        <strong>현재 값 요약:</strong>{' '}
        {summariseHtml(editorDataObj.onboardingGuide)}
      </div>
    </div>;
};

/**
 * @description CtrlEditorDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const CtrlEditorDemo = () => {
  const editorDataObj = Lib.EasyObj({
    htmlMemo: '<h3>HTML 메모</h3><p>컨트롤드 모드에서는 <strong>serialization="html"</strong>을 사용하십시오.</p>'
  });

  return <div className="space-y-3">
      <Lib.EasyEditor dataObj={editorDataObj} dataKey="htmlMemo" serialization="html" placeholder="HTML 문자열을 직접 관리" label="컨트롤드 HTML 편집기" toolbar />
      <pre className="rounded bg-gray-900 p-3 text-xs text-gray-100 overflow-auto">
        {editorDataObj.htmlMemo}
      </pre>
    </div>;
};

export const editorExampleList = [{
  anchor: 'editor-basic',
  component: <NoticeEditorDemo />,
  description: 'EasyObj 바인딩 기반 기본 사용',
  code: `<Lib.EasyEditor
  dataObj={editorDataObj}
  dataKey="announcement"
  serialization="html"
  placeholder="팀 공지를 작성하세요"
  label="공지 작성"
  helperText="툴바에서 폰트, 색상, 정렬, HTML 모드를 시험해보세요."
/>`
}, {
  anchor: 'editor-bound',
  component: <GuideEditorDemo />,
  description: '스타터 콘텐츠가 있는 바인딩 케이스',
  code: `<Lib.EasyEditor
  dataObj={editorDataObj}
  dataKey="onboardingGuide"
  serialization="html"
  placeholder="온보딩 가이드를 작성하세요"
  label="가이드 편집"
  status="success"
  helperText="status='success'로 상태 프리셋을 표시합니다."
/>`
}, {
  anchor: 'editor-controlled',
  component: <CtrlEditorDemo />,
  description: 'EasyObj 바인딩 + HTML 직렬화',
  code: `const editorDataObj = Lib.EasyObj({ htmlMemo: '<p>초기 HTML</p>' });

<Lib.EasyEditor
  dataObj={editorDataObj}
  dataKey="htmlMemo"
  serialization="html"
  placeholder="HTML 문자열을 직접 관리"
  label="컨트롤드 HTML 편집기"
/>`
}, {
  anchor: 'editor-states',
  component: <div className="space-y-4">
      <div className="grid md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Lib.EasyEditor value={'<p>읽기 전용 내용</p>'} serialization="html" readOnly toolbar={false} label="읽기 전용(readOnly)" helperText="툴바 숨김 + 수정 불가" />
        </div>
        <div className="space-y-2">
          <Lib.EasyEditor value={'<p>유효성 오류 예시</p>'} serialization="html" invalid label="유효성 오류(invalid)" helperText="오류 스타일 및 안내" />
        </div>
        <div className="space-y-2">
          <Lib.EasyEditor value={'<p>로딩 상태</p>'} serialization="html" status="loading" label="status=loading" helperText="처리 중 상태" />
        </div>
        <div className="space-y-2">
          <Lib.EasyEditor value={'<p>성공 상태</p>'} serialization="html" status="success" label="status=success" helperText="성공 스타일" />
        </div>
      </div>
    </div>,
  description: 'readOnly/invalid/status 매트릭스 예시',
  code: `<div className="grid md:grid-cols-2 gap-4">
  <Lib.EasyEditor value={'<p>읽기 전용 내용</p>'} serialization="html" readOnly toolbar={false} />
  <Lib.EasyEditor value={'<p>유효성 오류 예시</p>'} serialization="html" invalid />
  <Lib.EasyEditor value={'<p>로딩 상태</p>'} serialization="html" status="loading" />
  <Lib.EasyEditor value={'<p>성공 상태</p>'} serialization="html" status="success" />
</div>`
}];
