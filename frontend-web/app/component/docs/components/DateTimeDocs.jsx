/**
 * 파일명: DateTimeDocs.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: DateTime 컴포넌트 문서
 */
import DocSection from '../shared/DocSection';
import CodeBlock from '../shared/CodeBlock';
import { dateExampleList } from '../examples/DateInputExamples';
import { timeExampleList } from '../examples/TimeInputExamples';

/**
 * @description DateInput/TimeInput 문서 섹션을 구성하고 예제 목록을 렌더링. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const DateTimeDocs = () => {
  return <DocSection id="datetime-inputs" title="13. 날짜/시간 (Date/Time)" description={<div>
          <p>브라우저 기본 Date와 Time 입력을 래핑한 컴포넌트입니다. EasyObj 바운드와 컨트롤드 모드를 지원합니다.</p>
          <ul className="list-disc pl-5 mt-2 text-sm text-gray-600">
            <li><code>value?</code>: ISO 문자열 제어 값</li>
            <li><code>dataObj?/dataKey?</code>: 바운드 상태 객체와 키</li>
            <li><code>defaultValue?</code>: 초기 값</li>
            <li><code>min?/max?</code>: 선택 가능 범위</li>
            <li><code>onChange?/onValueChange?</code>: 값 변경 콜백</li>
            <li><code>className?</code>: 추가 Tailwind 클래스</li>
            <li><code>disabled?</code>: 입력 비활성화</li>
            <li><code>readOnly?</code>: 읽기 전용</li>
            <li><code>placeholder?</code>: 안내 문구</li>
            <li><code>id?</code>: input id 지정</li>
          </ul>
        </div>}>
      <div id="date-basic" className="mb-8">
        <h3 className="text-lg font-medium mb-4">날짜</h3>
        <div className="space-y-6">
          {dateExampleList.map(example => <div key={example.exampleId}>
              {example.component}
              <div className="mt-2 text-sm text-gray-600">{example.description}</div>
              <CodeBlock code={example.code} />
            </div>)}
        </div>
      </div>

      <div id="time-basic" className="mb-8">
        <h3 className="text-lg font-medium mb-4">시간</h3>
        <div className="space-y-6">
          {timeExampleList.map(example => <div key={example.exampleId}>
              {example.component}
              <div className="mt-2 text-sm text-gray-600">{example.description}</div>
              <CodeBlock code={example.code} />
            </div>)}
        </div>
      </div>
    </DocSection>;
};

export default DateTimeDocs;
