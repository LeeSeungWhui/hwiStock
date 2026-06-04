/**
 * 파일명: demoSharedState.test.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-03
 * 설명: sample/demoSharedState 훅의 shared snapshot/updater 회귀 테스트
 */

import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import { useSharedStore } from "@/app/common/store/SharedStore";
import { useDemoSharedState } from "@/app/sample/demoSharedState";

describe("useDemoSharedState", () => {
  beforeEach(() => {
    useSharedStore.setState({ shared: {} });
  });

  it("연속 updater 호출도 최신 shared snapshot 기준으로 누적 반영한다", async () => {
    const { result } = renderHook(() => useDemoSharedState({
      stateKey: "counter",
      initialValue: 0,
    }));

    await waitFor(() => {
      expect(result.current.isInitialized).toBe(true);
      expect(result.current.value).toBe(0);
    });

    act(() => {
      result.current.setValue((prevValue) => Number(prevValue || 0) + 1);
      result.current.setValue((prevValue) => Number(prevValue || 0) + 1);
    });

    await waitFor(() => {
      expect(result.current.value).toBe(2);
    });
  });
});
