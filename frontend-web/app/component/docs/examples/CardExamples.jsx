"use client";

/**
 * 파일명: CardExamples.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Card 컴포넌트 예제
 */
import * as Lib from '@/app/lib';
import { useGlobalUi } from '@/app/common/store/SharedStore';

/**
 * @description 액션 버튼이 포함된 카드 예시를 렌더링. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 * @updated 2026-02-27
 */
const ActionCard = () => {
  const {
    showAlert
  } = useGlobalUi();
  return <Lib.Card title="액션 카드" subtitle="버튼과 함께" actions={<Lib.Button onClick={() => showAlert('버튼 액션')}>Action</Lib.Button>} footer="푸터 텍스트">
      <div className="space-y-2">
        <div>리스트 항목 1</div>
        <div>리스트 항목 2</div>
      </div>
    </Lib.Card>;
};

/**
 * @description Card 예제 계약을 정의. 입력/출력 계약을 함께 명시
 * @returns { basicExampleList: Array, actionExampleList: Array, plainExampleList: Array, composedExampleList: Array }
 * @updated 2026-02-24
 */
export const basicExampleList = [{
  component: <Lib.Card title="간단 카드" subtitle="보조 설명">
          카드 본문을 간결하게 구성합니다.
        </Lib.Card>,
  description: '기본 Card: title + subtitle + 본문',
  code: `<Lib.Card title=\"간단 카드\" subtitle=\"보조 설명\">\n  카드 본문을 간결하게 구성합니다.\n</Lib.Card>`
}];
export const actionExampleList = [{
  component: <ActionCard />,
  description: 'actions + footer 사용',
  code: `<Lib.Card\n  title=\"액션 카드\"\n  subtitle=\"버튼과 함께\"\n  actions={<Lib.Button onClick={() => showAlert('버튼 액션')}>Action</Lib.Button>}\n  footer=\"푸터 텍스트\"\n>\n  <div className=\"space-y-2\">\n    <div>리스트 항목 1</div>\n    <div>리스트 항목 2</div>\n  </div>\n</Lib.Card>`
}];
export const plainExampleList = [{
  component: <Lib.Card className="bg-slate-50" bodyClassName="p-6" headerClassName="p-3" footerClassName="p-2">
          헤더/푸터 패딩이 있는 카드입니다.
        </Lib.Card>,
  description: '헤더/푸터 패딩(custom className*)',
  code: `<Lib.Card className=\"bg-slate-50\" bodyClassName=\"p-6\">\n  헤더/푸터 패딩이 있는 카드입니다.\n</Lib.Card>`
}];
export const composedExampleList = [{
  component: <Lib.Card title="조합 예시" actions={<Lib.Badge variant="primary">New</Lib.Badge>} footer={<div className="flex items-center gap-2 text-xs"><Lib.Icon icon="md:MdSchedule" /> 업데이트: 방금 전</div>}>
          <div className="flex items-start gap-3">
            <div className="h-12 w-12 rounded bg-blue-100 flex items-center justify-center text-blue-700">IMG</div>
            <div>
              <div className="font-medium">이미지/아이콘과 텍스트</div>
              <div className="text-sm text-gray-600">레이아웃과 구성 예시</div>
            </div>
          </div>
        </Lib.Card>,
  description: 'Badge, Icon 조합',
  code: `<Lib.Card\n  title=\"조합 예시\"\n  actions={<Lib.Badge variant=\"primary\">New</Lib.Badge>}\n  footer={<div className=\"flex items-center gap-2 text-xs\"><Lib.Icon icon=\"md:MdSchedule\" /> 업데이트: 방금 전</div>}\n>\n  <div className=\"flex items-start gap-3\">\n    <div className=\"h-12 w-12 rounded bg-blue-100 flex items-center justify-center text-blue-700\">IMG</div>\n    <div>\n      <div className=\"font-medium\">이미지/아이콘과 텍스트</div>\n      <div className=\"text-sm text-gray-600\">레이아웃과 구성 예시</div>\n    </div>\n  </div>\n</Lib.Card>`
}];
