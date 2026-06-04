/**
 * 파일명: EasyChartDocs.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: EasyChart 컴포넌트 소개/Props/예시 섹션
 */

import { easyChartExampleList } from "../examples/EasyChartExamples";
import DocSection from "../shared/DocSection";
import CodeBlock from "../shared/CodeBlock";
const propRows = [{
  name: "dataList",
  desc: "EasyList/배열 차트 데이터"
}, {
  name: "seriesList",
  desc: "EasyList/배열 시리즈 ({seriesId, seriesNm, dataKey, type, color})"
}, {
  name: "xKey",
  desc: "X축에 사용할 필드 키 (기본 label)"
}, {
  name: "type",
  desc: "기본 시리즈 타입 line|bar|area|pie|donut (기본 line)"
}, {
  name: "loading / status",
  desc: "로딩/에러/빈 상태 표시 플래그"
}, {
  name: "empty",
  desc: "빈 상태 메시지 혹은 노드"
}, {
  name: "actions",
  desc: "카드 우측 액션 영역"
}, {
  name: "hideLegend",
  desc: "범례 숨김 여부"
}];

/**
 * @description EasyChart 문서 섹션을 구성하고 예제 목록을 렌더링. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const EasyChartDocs = () => {
  return <DocSection id="easychart" title="32. 차트 (EasyChart)" description="Recharts 기반 카드형 차트 래퍼(EasyList 대응)">
      <div className="mb-4 space-y-2 text-sm text-gray-700">
        <p>
          EasyList/배열 데이터를 그대로 받아 카드 스타일로 차트를 렌더링한다.
        </p>
        <p className="text-gray-600">
          시리즈는 {`{seriesId, seriesNm, dataKey, type, color}`} 구조를 권장.
        </p>
      </div>
      <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500">
            <tr>
              <th className="px-4 py-2">Prop</th>
              <th className="px-4 py-2">설명</th>
            </tr>
          </thead>
          <tbody>
            {propRows.map(row => <tr key={row.name} className="border-t text-gray-800">
                <td className="px-4 py-2 font-medium text-gray-900">
                  {row.name}
                </td>
                <td className="px-4 py-2">{row.desc}</td>
              </tr>)}
          </tbody>
        </table>
      </div>
      <div className="mt-8 space-y-10">
        {easyChartExampleList.map((ex, index) => {
        const needsSample = ["easychart-line", "easychart-bar", "easychart-mixed", "easychart-pie", "easychart-donut", "easychart-error"].includes(ex.anchor);
        const sampleDataSnippet = needsSample ? `const sampleData = [
  { label: "1월", signups: 120, active: 90, churn: 12 },
  { label: "2월", signups: 150, active: 110, churn: 15 },
  { label: "3월", signups: 180, active: 130, churn: 18 },
  { label: "4월", signups: 220, active: 170, churn: 16 },
  { label: "5월", signups: 240, active: 190, churn: 20 },
];\n\n` : "";
        return <div key={ex.anchor || index} id={ex.anchor} className="space-y-3 scroll-mt-24">
              <div className="text-sm text-gray-600">{ex.description}</div>
              <div className="rounded-lg border border-gray-200 bg-white p-4">
                {ex.component}
              </div>
              <CodeBlock code={`${sampleDataSnippet}${ex.code}`} />
            </div>;
      })}
      </div>
    </DocSection>;
};

export default EasyChartDocs;
