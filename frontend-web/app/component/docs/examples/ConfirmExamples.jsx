"use client";

/**
 * 파일명: ConfirmExamples.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Confirm 컴포넌트 예제
 */
import * as Lib from '@/app/lib';
import { useRef } from 'react';
import { useGlobalUi } from '@/app/common/store/SharedStore';

/**
 * @description 를 렌더링. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 * @updated 2026-02-27
 */
const BasicConfirm = () => {
  const {
    showConfirm,
    showAlert
  } = useGlobalUi();
  return <Lib.Button onClick={() => {
    showConfirm('정말 진행하시겠습니까?').then(result => {
      if (result) showAlert('확인했습니다.');
    });
  }}>
      기본 확인
    </Lib.Button>;
};

/**
 * @description 를 렌더링. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 * @updated 2026-02-27
 */
const ConfirmVariants = () => {
  const {
    showConfirm
  } = useGlobalUi();
  return <div className="flex flex-wrap gap-2">
      <Lib.Button onClick={() => showConfirm('해당 작업은 되돌릴 수 없습니다.\n계속하시겠습니까?', {
      title: '주의',
      type: 'warning',
      confirmText: '계속',
      cancelText: '중단'
    })}>
        경고 확인
      </Lib.Button>
      <Lib.Button onClick={() => showConfirm('모든 데이터를 삭제합니다.\n정말 삭제하시겠습니까?', {
      title: '위험 확인',
      type: 'danger',
      confirmText: '삭제',
      cancelText: '취소'
    })}>
        위험 확인
      </Lib.Button>
    </div>;
};

/**
 * @description 를 렌더링. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 * @updated 2026-02-27
 */
const ConfirmCallbacks = () => {
  const {
    showConfirm,
    showAlert
  } = useGlobalUi();
  return <Lib.Button onClick={() => showConfirm('삭제를 진행하시겠습니까?', {
    title: '위험 확인',
    type: 'danger',
    confirmText: '삭제',
    cancelText: '취소',
    onConfirm: () => showAlert('삭제가 완료되었습니다.'),
    onCancel: () => showAlert('삭제가 취소되었습니다.')
  })}>
      콜백 함수 표시
    </Lib.Button>;
};

/**
 * @description 를 렌더링. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 * @updated 2026-02-27
 */
const ConfirmFocus = () => {
  const {
    showConfirm
  } = useGlobalUi();
  const inputRef = useRef(null);
  return <div className="flex gap-4 items-center">
      <Lib.Button onClick={() => showConfirm('확인 모달이 닫히면 입력창으로 커서가 이동합니다.', {
      title: '포커스 이동',
      onFocus: () => inputRef.current?.focus()
    })}>
        포커스 이동 표시
      </Lib.Button>
      <Lib.Input ref={inputRef} placeholder="커서가 여기로 이동합니다" />
    </div>;
};

/**
 * @description Confirm 예제 계약을 정의. 입력/출력 계약을 함께 명시
 * @updated 2026-02-24
 * 처리 규칙: 입력값과 상태를 검증해 UI/데이터 흐름을 안전하게 유지한다.
 */
export const basicExampleList = [{
  component: <div className="space-y-4">
          <BasicConfirm />
        </div>,
  description: '기본 확인 모달',
  code: `// useSharedStore 사용
const { showConfirm, showAlert } = useGlobalUi();

// 기본 확인
showConfirm('정말 진행하시겠습니까?').then((result) => {
  if (result) showAlert('확인했습니다.');
});`
}];
export const typeExampleList = [{
  component: <ConfirmVariants />,
  description: '확인 모달 유형',
  code: `// 경고 확인
showConfirm('해당 작업은 되돌릴 수 없습니다.\\n계속하시겠습니까?', {
  title: '주의',
  type: 'warning',
  confirmText: '계속',
  cancelText: '중단',
});

// 위험 확인
showConfirm('모든 데이터를 삭제합니다.\\n정말 삭제하시겠습니까?', {
  title: '위험 확인',
  type: 'danger',
  confirmText: '삭제',
  cancelText: '취소',
});`
}];
export const callbackExampleList = [{
  component: <div className="space-y-4">
          <ConfirmCallbacks />
        </div>,
  description: '확인/취소 콜백',
  code: `// 확인/취소 시 실행될 콜백
showConfirm('삭제를 진행하시겠습니까?', {
  title: '위험 확인',
  type: 'danger',
  confirmText: '삭제',
  cancelText: '취소',
  onConfirm: () => showAlert('삭제가 완료되었습니다.'),
  onCancel: () => showAlert('삭제가 취소되었습니다.'),
});`
}];
export const focusExampleList = [{
  component: <div className="space-y-4">
          <ConfirmFocus />
        </div>,
  description: '확인 모달 닫힘 후 포커스 이동',
  code: `// useRef 로 입력창 참조 생성
const inputRef = useRef(null);

// 모달 닫힘 후 입력창으로 포커스 이동
<div className="flex gap-4 items-center">
  <Lib.Button
    onClick={() => {
      showConfirm('확인 모달이 닫히면 입력창으로 커서가 이동합니다.', {
        title: '포커스 이동',
        onFocus: () => inputRef.current?.focus(),
      });
    }}
  >
    포커스 이동 표시
  </Lib.Button>
  <Lib.Input ref={inputRef} placeholder="커서가 여기로 이동합니다" />
</div>`
}];
