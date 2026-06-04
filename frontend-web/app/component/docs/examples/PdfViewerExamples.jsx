/**
 * 파일명: PdfViewerExamples.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: PdfViewer 컴포넌트 예제
 */
import * as Lib from '@/app/lib';
import { useState } from 'react';

/**
 * @description LocalPdfDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const LocalPdfDemo = () => {
  const [localFile, setLocalFile] = useState(null);

  return <div className="space-y-3">
      <div className="flex items-center gap-2">
        <input type="file" accept="application/pdf" onChange={event => setLocalFile(event.target.files?.[0] ?? null)} />
      </div>
      {localFile && <Lib.PdfViewer src={localFile} />}
    </div>;
};

/**
 * @description RemotePdfDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const RemotePdfDemo = () => {
  const [remoteUrl, setRemoteUrl] = useState('');

  return <div className="space-y-3">
      <div className="flex items-center gap-2">
        <input className="w-full max-w-md border rounded px-2 py-1 text-sm" placeholder="https://example.com/sample.pdf" value={remoteUrl} onChange={event => setRemoteUrl(event.target.value)} />
      </div>
      {remoteUrl && <Lib.PdfViewer src={remoteUrl} />}
    </div>;
};

/**
 * @description PdfViewer 예제 계약을 정의. 입력/출력 계약을 함께 명시
 * @updated 2026-02-24
 * 처리 규칙: 상태가 필요한 예제는 demo 컴포넌트 안으로 가두고 계약은 직접 export한다.
 */
export const pdfViewerExampleList = [{
  anchor: 'pdf-basic',
  component: <div className="space-y-3">
      <p className="text-sm text-gray-600">public/pdf-sample.pdf 파일이 제공되면 아래 뷰어가 렌더링됩니다.</p>
      <Lib.PdfViewer src="/pdf-sample.pdf" />
    </div>,
  description: 'public 폴더의 pdf-sample.pdf 미리보기',
  code: '<Lib.PdfViewer src="/pdf-sample.pdf" />'
}, {
  anchor: 'pdf-no-toolbar',
  component: <div className="space-y-3">
      <p className="text-sm text-gray-600">툴바 비활성화(페이지/검색/줌 UI 숨김)</p>
      <Lib.PdfViewer src="/pdf-sample.pdf" withToolbar={false} />
    </div>,
  description: 'withToolbar=false 예시',
  code: '<Lib.PdfViewer src="/pdf-sample.pdf" withToolbar={false} />'
}, {
  anchor: 'pdf-local',
  component: <LocalPdfDemo />,
  description: '로컬 파일 선택 후 뷰어로 표시',
  code: `const [localFile, setLocalFile] = useState(null);

<input
  type="file"
  accept="application/pdf"
  onChange={(event) => setLocalFile(event.target.files?.[0] ?? null)}
/>
{localFile && <Lib.PdfViewer src={localFile} />}`
}, {
  anchor: 'pdf-remote',
  component: <RemotePdfDemo />,
  description: '원격 URL로 PDF 표시(서버 CORS 허용 필요)',
  code: `const [remoteUrl, setRemoteUrl] = useState('');

<input
  value={remoteUrl}
  onChange={(event) => setRemoteUrl(event.target.value)}
/>
{remoteUrl && <Lib.PdfViewer src={remoteUrl} />}`
}, {
  anchor: 'pdf-error',
  component: <div className="space-y-3">
      <p className="text-sm text-gray-600">오류 상태(404) 시 Empty 안내로 대체</p>
      <Lib.PdfViewer src="/not-exists.pdf" />
    </div>,
  description: '404/네트워크 오류시 오류 안내 렌더링',
  code: '<Lib.PdfViewer src="/not-exists.pdf" />'
}];
