"use client";

/**
 * 파일명: ToastExamples.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Toast 컴포넌트 예제
 */
import * as Lib from '@/app/lib';
import { useGlobalUi } from '@/app/common/store/SharedStore';

/**
 * @description 를 렌더링. 입력/출력 계약을 함께 명시
 * 반환값: 기본 토스트 호출 버튼 예제 JSX.
 * @updated 2026-02-27
 */
const ToastBasic = () => {
  const {
    showToast
  } = useGlobalUi();
  return <Lib.Button onClick={() => showToast('기본 토스트 메시지입니다.')}>기본 토스트</Lib.Button>;
};

/**
 * @description 를 렌더링. 입력/출력 계약을 함께 명시
 * 반환값: info/success/warning/error 타입 토스트 버튼 그룹 JSX.
 * @updated 2026-02-27
 */
const ToastTypes = () => {
  const {
    showToast
  } = useGlobalUi();
  return <div className="flex flex-wrap gap-2">
      <Lib.Button onClick={() => showToast('정보 토스트 메시지입니다.', {
      type: 'info'
    })}>정보 토스트</Lib.Button>
      <Lib.Button onClick={() => showToast('성공 토스트 메시지입니다.', {
      type: 'success'
    })}>성공 토스트</Lib.Button>
      <Lib.Button onClick={() => showToast('경고 토스트 메시지입니다.', {
      type: 'warning'
    })}>경고 토스트</Lib.Button>
      <Lib.Button onClick={() => showToast('오류 토스트 메시지입니다.', {
      type: 'error'
    })}>오류 토스트</Lib.Button>
    </div>;
};

/**
 * @description 를 렌더링. 입력/출력 계약을 함께 명시
 * 반환값: top/bottom 위치별 토스트 표시 버튼 그룹 JSX.
 * @updated 2026-02-27
 */
const ToastPositions = () => {
  const {
    showToast
  } = useGlobalUi();
  return <div className="flex flex-wrap gap-2">
      <Lib.Button onClick={() => showToast('상단 왼쪽에 표시합니다.', {
      position: 'top-left'
    })}>상단 왼쪽</Lib.Button>
      <Lib.Button onClick={() => showToast('상단 중앙에 표시합니다.', {
      position: 'top-center'
    })}>상단 중앙</Lib.Button>
      <Lib.Button onClick={() => showToast('상단 오른쪽에 표시합니다.', {
      position: 'top-right'
    })}>상단 오른쪽</Lib.Button>
      <Lib.Button onClick={() => showToast('하단 왼쪽에 표시합니다.', {
      position: 'bottom-left'
    })}>하단 왼쪽</Lib.Button>
      <Lib.Button onClick={() => showToast('하단 중앙에 표시합니다.', {
      position: 'bottom-center'
    })}>하단 중앙</Lib.Button>
      <Lib.Button onClick={() => showToast('하단 오른쪽에 표시합니다.', {
      position: 'bottom-right'
    })}>하단 오른쪽</Lib.Button>
    </div>;
};

/**
 * @description 를 렌더링. 입력/출력 계약을 함께 명시
 * 반환값: 유지 시간(duration) 옵션별 토스트 버튼 그룹 JSX.
 * @updated 2026-02-27
 */
const ToastDurations = () => {
  const {
    showToast
  } = useGlobalUi();
  return <div className="flex flex-wrap gap-2">
      <Lib.Button onClick={() => showToast('2초에 사라집니다.', {
      duration: 2000
    })}>2초 유지</Lib.Button>
      <Lib.Button onClick={() => showToast('5초에 사라집니다.', {
      duration: 5000
    })}>5초 유지</Lib.Button>
      <Lib.Button onClick={() => showToast('자동으로 사라지지 않습니다.', {
      duration: Infinity
    })}>자동 닫기 비활성화</Lib.Button>
    </div>;
};

/**
 * @description Toast 예제 계약을 정의. 입력/출력 계약을 함께 명시
 * 반환값: 문서 섹션별 ...ExampleList 계약 객체.
 * @updated 2026-02-24
 */
export const basicExampleList = [{
  component: <div className="space-y-4">
          <ToastBasic />
        </div>,
  description: '기본 토스트',
  code: `// useSharedStore 사용
const { showToast } = useGlobalUi();

// 기본 토스트
showToast('기본 토스트 메시지입니다.');`
}];
export const typeExampleList = [{
  component: <ToastTypes />,
  description: '토스트 유형',
  code: `showToast('정보 토스트 메시지입니다.', { type: 'info' });
showToast('성공 토스트 메시지입니다.', { type: 'success' });
showToast('경고 토스트 메시지입니다.', { type: 'warning' });
showToast('오류 토스트 메시지입니다.', { type: 'error' });`
}];
export const positionExampleList = [{
  component: <ToastPositions />,
  description: '토스트 위치',
  code: `showToast('상단 왼쪽에 표시합니다.', { position: 'top-left' });
showToast('상단 중앙에 표시합니다.', { position: 'top-center' });
showToast('상단 오른쪽에 표시합니다.', { position: 'top-right' });
showToast('하단 왼쪽에 표시합니다.', { position: 'bottom-left' });
showToast('하단 중앙에 표시합니다.', { position: 'bottom-center' });
showToast('하단 오른쪽에 표시합니다.', { position: 'bottom-right' });`
}];
export const durationExampleList = [{
  component: <ToastDurations />,
  description: '토스트 유지 시간',
  code: `showToast('2초에 사라집니다.', { duration: 2000 });
showToast('5초에 사라집니다.', { duration: 5000 });
showToast('자동으로 사라지지 않습니다.', { duration: Infinity });`
}];
