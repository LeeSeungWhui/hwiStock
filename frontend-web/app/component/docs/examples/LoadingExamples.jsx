"use client";

/**
 * 파일명: LoadingExamples.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Loading 컴포넌트 예제
 */
import { useEffect, useRef } from 'react';
import * as Lib from '@/app/lib';
import { useGlobalUi } from '@/app/common/store/SharedStore';

/**
 * @description 전역 로딩을 2초간 표시하는 버튼을 렌더링. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 * @updated 2026-02-27
 */
const ShowGlobalLoading = () => {
  const {
    setLoading
  } = useGlobalUi();
  const loadingTimerRef = useRef(null);

  /**
   * @description 전역 로딩 예제 타이머를 정리
   * 처리 규칙: 예제 컴포넌트가 사라지면 pending timeout을 취소한다.
   */
  useEffect(() => () => clearTimeout(loadingTimerRef.current), []);

  /**
   * @description 전역 로딩을 2초간 표시
   * 처리 규칙: 기존 타이머가 있으면 취소하고 새 timeout 하나만 유지한다.
   */
  const handleLoadingClick = () => {
    setLoading(true);
    clearTimeout(loadingTimerRef.current);
    loadingTimerRef.current = setTimeout(() => setLoading(false), 2000);
  };

  return <Lib.Button onClick={handleLoadingClick}>
      전체 화면 로딩 (2초)
    </Lib.Button>;
};

/**
 * @description Loading 예제 계약을 정의. 입력/출력 계약을 함께 명시
 * @updated 2026-02-24
 * 처리 규칙: 입력값과 상태를 검증해 UI/데이터 흐름을 안전하게 유지한다.
 */
export const basicExampleList = [{
  component: <div className="space-y-4">
          <ShowGlobalLoading />
        </div>,
  description: '전체 화면 로딩 표시',
  code: `const loadingTimerRef = useRef(null);
const { setLoading } = useGlobalUi();

/**
 * @description 전역 로딩 예제 타이머를 정리
 * 처리 규칙: 예제 컴포넌트가 사라지면 pending timeout을 취소한다.
 */
useEffect(() => () => clearTimeout(loadingTimerRef.current), []);

/**
 * @description 전역 로딩 버튼 클릭을 처리
 * 처리 규칙: 로딩 표시 후 2초 뒤 자동 해제한다.
 */
const handleLoadingClick = () => {
  setLoading(true);
  clearTimeout(loadingTimerRef.current);
  loadingTimerRef.current = setTimeout(() => setLoading(false), 2000);
};

<Lib.Button onClick={handleLoadingClick}>
  전체 화면 로딩 (2초)
</Lib.Button>`
}];
