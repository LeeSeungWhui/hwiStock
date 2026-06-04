/**
 * 파일명: SkeletonExamples.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Skeleton 컴포넌트 예제
 */
import * as Lib from '@/app/lib';

/**
 * @description Skeleton 예제 계약을 정의. 입력/출력 계약을 함께 명시
 * @updated 2026-02-24
 * 처리 규칙: 입력값과 상태를 검증해 UI/데이터 흐름을 안전하게 유지한다.
 */
export const textExampleList = [{
  component: <div className="space-y-2">
          <Lib.Skeleton variant="text" lines={3} />
        </div>,
  description: '텍스트 라인 스켈레톤',
  code: `<Lib.Skeleton variant="text" lines={3} />`
}];
export const avatarExampleList = [{
  component: <div className="flex items-center gap-3">
          <Lib.Skeleton variant="circle" circleSize={48} />
          <div className="flex-1">
            <Lib.Skeleton variant="text" lines={2} />
          </div>
        </div>,
  description: '아바타 + 텍스트',
  code: `<Lib.Skeleton variant="circle" circleSize={48} />
<Lib.Skeleton variant="text" lines={2} />`
}];
export const cardExampleList = [{
  component: <Lib.Card className="bg-white">
          <div className="flex items-center gap-3">
            <Lib.Skeleton variant="circle" circleSize={40} />
            <div className="flex-1">
              <Lib.Skeleton variant="text" lines={2} />
            </div>
          </div>
          <div className="mt-4">
            <Lib.Skeleton className="h-24 w-full" />
          </div>
        </Lib.Card>,
  description: '카드 스켈레톤 조합',
  code: `<Lib.Card className="bg-white">
  <div className="flex items-center gap-3">
    <Lib.Skeleton variant="circle" circleSize={40} />
    <div className="flex-1">
      <Lib.Skeleton variant="text" lines={2} />
    </div>
  </div>
  <div className="mt-4">
    <Lib.Skeleton className="h-24 w-full" />
  </div>
</Lib.Card>`
}];
