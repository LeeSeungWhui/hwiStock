/**
 * 파일명: PdfViewerDocs.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: PdfViewer 컴포넌트 문서
 */
import { pdfViewerExampleList } from '../examples/PdfViewerExamples';
import DocSection from '../shared/DocSection';
import CodeBlock from '../shared/CodeBlock';

/**
 * @description PdfViewer 문서 섹션을 구성하고 예제 목록을 렌더링. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const PdfViewerDocs = () => {
  return <DocSection id="pdfviewer" title="33. PDF 뷰어 (PdfViewer)" description={<div className="space-y-2 text-sm text-gray-700">
          <p>로컬 파일 또는 외부 URL의 PDF를 미리봅니다. public/pdf-sample.pdf 예제가 포함되어 있습니다.</p>
          <ul className="list-disc pl-5">
            <li>Props: <code>src</code>(string|File|Blob|ArrayBuffer), <code>workerSrc?</code>, <code>withToolbar?</code></li>
            <li>외부 URL은 CORS 허용이 필요합니다.</li>
          </ul>
        </div>}>
      <div className="space-y-10">
        {pdfViewerExampleList.map(exampleItem => <div key={exampleItem.anchor} id={exampleItem.anchor} className="space-y-3 scroll-mt-24">
            <div>{exampleItem.component}</div>
            <p className="text-sm text-gray-600">{exampleItem.description}</p>
            <CodeBlock code={exampleItem.code} />
          </div>)}
      </div>
    </DocSection>;
};

export default PdfViewerDocs;
