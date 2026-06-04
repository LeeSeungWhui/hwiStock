/**
 * 파일명: EmptyExamples.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Empty 컴포넌트 예제
 */
import * as Lib from '@/app/lib';

/**
 * @description Empty 예제 계약을 정의. 입력/출력 계약을 함께 명시
 * @returns { basicExampleList: Array, actionExampleList: Array }
 * @updated 2026-02-24
 */
export const basicExampleList = [{
  component: <Lib.Empty />,
  description: '기본 Empty',
  code: `<Lib.Empty />`
}];
export const actionExampleList = [{
  component: <Lib.Empty title="검색 결과 없음" description="다른 키워드로 다시 시도해 보세요" action={<Lib.Button>새로 만들기</Lib.Button>} />,
  description: '설명/액션 포함',
  code: `<Lib.Empty title="검색 결과 없음" description="다른 키워드로 다시 시도해 보세요" action={<Lib.Button>새로 만들기</Lib.Button>} />`
}];
