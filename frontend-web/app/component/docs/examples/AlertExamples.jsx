"use client";

/**
 * 파일명: AlertExamples.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Alert 컴포넌트 예제
 */
import * as Lib from '@/app/lib';
import { useRef } from 'react';
import { useGlobalUi } from '@/app/common/store/SharedStore';

/**
 * @description 를 렌더링. 입력/출력 계약을 함께 명시
 * 반환값: 기본 showAlert 호출 버튼 예제 JSX.
 * @updated 2026-02-27
 */
const BasicAlert = () => {
  const {
    showAlert
  } = useGlobalUi();
  return <Lib.Button onClick={() => showAlert('기본 알림 메시지입니다.')}>기본 알림</Lib.Button>;
};

/**
 * @description 를 렌더링. 입력/출력 계약을 함께 명시
 * 반환값: info/success/warning/error 타입별 Alert 호출 버튼 묶음 JSX.
 * @updated 2026-02-27
 */
const AlertVariants = () => {
  const {
    showAlert
  } = useGlobalUi();
  return <div className="flex flex-wrap gap-2">
      <Lib.Button onClick={() => showAlert('정보 알림 메시지입니다.', {
      title: '정보',
      type: 'info'
    })}>정보 알림</Lib.Button>
      <Lib.Button onClick={() => showAlert('성공 알림 메시지입니다.', {
      title: '성공',
      type: 'success'
    })}>성공 알림</Lib.Button>
      <Lib.Button onClick={() => showAlert('경고 알림 메시지입니다.', {
      title: '경고',
      type: 'warning'
    })}>경고 알림</Lib.Button>
      <Lib.Button onClick={() => showAlert('오류 알림 메시지입니다.', {
      title: '오류',
      type: 'error'
    })}>오류 알림</Lib.Button>
    </div>;
};

/**
 * @description 를 렌더링. 입력/출력 계약을 함께 명시
 * 반환값: 알림 닫힘 후 onClick 콜백 동작을 보여주는 JSX.
 * @updated 2026-02-27
 */
const AlertCallback = () => {
  const {
    showAlert
  } = useGlobalUi();
  return <Lib.Button onClick={() => showAlert('작업이 완료되었습니다.', {
    title: '알림',
    onClick: function () {
      alert('알림을 닫았습니다.');
    }
  })}>
      콜백 함수 표시
    </Lib.Button>;
};

/**
 * @description 를 렌더링. 입력/출력 계약을 함께 명시
 * 반환값: alert 닫힘 이후 지정 ref로 포커스를 이동하는 데모 JSX.
 * @updated 2026-02-27
 */
const AlertFocusAfter = () => {
  const {
    showAlert
  } = useGlobalUi();
  const inputRef = useRef(null);
  return <div className="flex gap-4 items-center">
      <Lib.Button onClick={() => showAlert('알림을 닫히면 입력창으로 커서가 이동합니다.', {
      title: '알림',
      onFocus: () => inputRef.current?.focus()
    })}>
        알림 띄우기
      </Lib.Button>
      <Lib.Input ref={inputRef} placeholder="커서가 여기로 이동합니다" />
    </div>;
};

/**
 * @description Alert 예제 계약을 정의. 입력/출력 계약을 함께 명시
 * 반환값: 문서 섹션별 ...ExampleList 계약 객체.
 * @updated 2026-02-24
 */
export const basicExampleList = [{
  component: <div className="space-y-4">
          <BasicAlert />
        </div>,
  description: '기본 알림',
  code: `// useSharedStore 사용
const { showAlert } = useGlobalUi();

// 기본 알림
showAlert('기본 알림 메시지입니다.');`
}];
export const typeExampleList = [{
  component: <AlertVariants />,
  description: '알림 유형',
  code: `// 정보/성공/경고/오류 알림
showAlert('정보 알림 메시지입니다.', { title: '정보', type: 'info' });
showAlert('성공 알림 메시지입니다.', { title: '성공', type: 'success' });
showAlert('경고 알림 메시지입니다.', { title: '경고', type: 'warning' });
showAlert('오류 알림 메시지입니다.', { title: '오류', type: 'error' });`
}];
export const callbackExampleList = [{
  component: <div className="space-y-4">
          <AlertCallback />
        </div>,
  description: '알림 닫힘 콜백',
  code: `// 알림 닫힘 시 실행될 콜백
showAlert('작업이 완료되었습니다.', {
  title: '알림',
  onClick: function() {
    alert('알림을 닫았습니다.');
  }
});`
}];
export const focusExampleList = [{
  component: <div className="space-y-4">
          <AlertFocusAfter />
        </div>,
  description: '알림 닫힘 후 지정된 요소로 포커스 이동',
  code: `// useRef 로 입력창 참조 생성
const inputRef = useRef(null);

// 알림을 닫으면 입력창으로 포커스 이동
<div className="flex gap-4 items-center">
  <Lib.Button
    onClick={() => {
      showAlert('알림을 닫히면 입력창으로 커서가 이동합니다.', {
        title: '알림',
        onFocus: () => inputRef.current?.focus(),
      });
    }}
  >
    알림 띄우기
  </Lib.Button>
  <Lib.Input ref={inputRef} placeholder="커서가 여기로 이동합니다" />
</div>`
}];
