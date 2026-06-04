/**
 * 파일명: BadgeExamples.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Badge 컴포넌트 예제
 */
import * as Lib from '@/app/lib';

/**
 * @description Badge 예제 계약을 정의. 입력/출력 계약을 함께 명시
 * @returns { variantExampleList: Array, outlineExampleList: Array, sizeExampleList: Array, iconExampleList: Array }
 * @updated 2026-02-24
 */
export const variantExampleList = [{
  component: <div className="flex flex-wrap gap-2 items-center">
          <Lib.Badge>Neutral</Lib.Badge>
          <Lib.Badge variant="primary">Primary</Lib.Badge>
          <Lib.Badge variant="success">Success</Lib.Badge>
          <Lib.Badge variant="warning">Warning</Lib.Badge>
          <Lib.Badge variant="danger">Danger</Lib.Badge>
        </div>,
  description: '기본/색상 Variant',
  code: `<Lib.Badge>Neutral</Lib.Badge>
<Lib.Badge variant="primary">Primary</Lib.Badge>
<Lib.Badge variant="success">Success</Lib.Badge>
<Lib.Badge variant="warning">Warning</Lib.Badge>
<Lib.Badge variant="danger">Danger</Lib.Badge>`
}];
export const outlineExampleList = [{
  component: <div className="flex flex-wrap gap-2 items-center">
          <Lib.Badge variant="outline">Outline</Lib.Badge>
          <Lib.Badge pill>Rounded</Lib.Badge>
        </div>,
  description: 'outline / pill',
  code: `<Lib.Badge variant="outline">Outline</Lib.Badge>
<Lib.Badge pill>Rounded</Lib.Badge>`
}];
export const sizeExampleList = [{
  component: <div className="flex flex-wrap gap-2 items-center">
          <Lib.Badge size="sm">Small</Lib.Badge>
          <Lib.Badge size="md">Medium</Lib.Badge>
        </div>,
  description: 'size: sm / md',
  code: `<Lib.Badge size="sm">Small</Lib.Badge>
<Lib.Badge size="md">Medium</Lib.Badge>`
}];
export const iconExampleList = [{
  component: <div className="flex flex-wrap gap-2 items-center">
          <Lib.Badge variant="success"><Lib.Icon icon="md:MdCheck" /> 완료</Lib.Badge>
          <Lib.Badge variant="warning"><Lib.Icon icon="md:MdSchedule" /> 진행중</Lib.Badge>
          <Lib.Badge variant="danger"><Lib.Icon icon="md:MdClose" /> 실패</Lib.Badge>
        </div>,
  description: '아이콘을 포함한 Badge',
  code: `<Lib.Badge variant="success"><Lib.Icon icon="md:MdCheck" /> 완료</Lib.Badge>
<Lib.Badge variant="warning"><Lib.Icon icon="md:MdSchedule" /> 진행중</Lib.Badge>
<Lib.Badge variant="danger"><Lib.Icon icon="md:MdClose" /> 실패</Lib.Badge>`
}];
