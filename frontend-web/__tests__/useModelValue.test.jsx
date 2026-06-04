/**
 * 파일명: useModelValue.test.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-03
 * 설명: useModelValue 훅의 경로 구독/쓰기 동작 회귀 테스트
 */

import { act, renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import EasyList from "@/app/lib/dataset/EasyList";
import EasyObj from "@/app/lib/dataset/EasyObj";
import { useModelValue } from "@/app/lib/hooks/useModelValue";

describe("useModelValue", () => {
  it("EasyObj dotted path 값을 구독하고 setter로 갱신한다", async () => {
    const { result } = renderHook(() => {
      const model = EasyObj({
        profile: {
          name: "Ada",
        },
      });
      const [modelValue, setModelValue] = useModelValue({
        model,
        path: "profile.name",
      });
      return { model, value: modelValue, setValue: setModelValue };
    });

    expect(result.current.value).toBe("Ada");

    act(() => {
      result.current.model.profile.name = "Mina";
    });

    await waitFor(() => {
      expect(result.current.value).toBe("Mina");
    });

    act(() => {
      result.current.setValue("Nia");
    });

    await waitFor(() => {
      expect(result.current.model.profile.name).toBe("Nia");
      expect(result.current.value).toBe("Nia");
    });
  });

  it("undefined setter는 해당 경로 키를 삭제한다", async () => {
    const { result } = renderHook(() => {
      const model = EasyObj({
        profile: {
          email: "ada@example.com",
        },
      });
      const [modelValue, setModelValue] = useModelValue({
        model,
        path: "profile.email",
      });
      return { model, value: modelValue, setValue: setModelValue };
    });

    expect(result.current.value).toBe("ada@example.com");

    act(() => {
      result.current.setValue(undefined);
    });

    await waitFor(() => {
      expect(result.current.value).toBeUndefined();
      expect(
        Object.prototype.hasOwnProperty.call(result.current.model.profile, "email"),
      ).toBe(false);
    });
  });

  it("EasyList/EasyObj 하위 배열의 같은 참조 변경도 path 구독으로 반영한다", async () => {
    const { result } = renderHook(() => {
      const model = EasyObj({
        filters: {
          tags: ["seoul"],
        },
      });
      const [modelValue, setModelValue] = useModelValue({
        defaultValue: [],
        model,
        path: "filters.tags",
      });
      return { model, value: modelValue, setValue: setModelValue };
    });

    expect(Array.from(result.current.value)).toEqual(["seoul"]);

    act(() => {
      result.current.model.filters.tags.push("busan");
    });

    await waitFor(() => {
      expect(Array.from(result.current.value)).toEqual(["seoul", "busan"]);
    });
  });

  it("EasyList index 경로 구독도 지원한다", async () => {
    const { result } = renderHook(() => {
      const model = EasyList([
        { name: "Ada" },
        { name: "Mina" },
      ]);
      const [modelValue, setModelValue] = useModelValue({
        model,
        path: "1.name",
      });
      return { model, value: modelValue, setValue: setModelValue };
    });

    expect(result.current.value).toBe("Mina");

    act(() => {
      result.current.model[1].name = "Nia";
    });

    await waitFor(() => {
      expect(result.current.value).toBe("Nia");
    });
  });
});
