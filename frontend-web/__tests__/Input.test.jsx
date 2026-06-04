import React, { useState } from "react";
import { fireEvent, render, screen, act } from "@testing-library/react";
import "@testing-library/jest-dom";
import { vi } from "vitest";
import Input from "../app/lib/component/Input.jsx";
function fireCompositionInput(input, { value, inputType = "insertCompositionText" }) {
  const nativeInputEvent = new InputEvent("input", {
    bubbles: true,
    cancelable: true,
    inputType,
  });
  input.value = value;
  input.dispatchEvent(nativeInputEvent);
}

describe("Input mask behavior", () => {
  it("supports function mask and commits transformed value", () => {
    const onValueChange = vi.fn();
    const maskFn = (rawValue) =>
      String(rawValue || "")
        .replace(/\D/g, "")
        .slice(0, 4);

    render(<Input aria-label="fn-mask" mask={maskFn} onValueChange={onValueChange} />);
    const input = screen.getByLabelText("fn-mask");

    fireEvent.change(input, { target: { value: "ab12cd345" } });

    expect(input).toHaveValue("1234");
    expect(onValueChange).toHaveBeenCalled();
    expect(onValueChange.mock.calls.at(-1)?.[0]).toBe("1234");
    expect(input.getAttribute("placeholder")).toBeNull();
  });

  it("uses string mask as fallback placeholder when placeholder prop is empty", () => {
    render(<Input aria-label="string-mask" mask="###-####-####" />);
    const input = screen.getByLabelText("string-mask");
    expect(input).toHaveAttribute("placeholder", "###-####-####");
  });
});

describe("Input Korean IME behavior", () => {
  it("commits composed Hangul once on compositionEnd", () => {
    const onValueChange = vi.fn();
    render(<Input aria-label="ime-once" filter="가-힣" onValueChange={onValueChange} />);
    const input = screen.getByLabelText("ime-once");

    fireEvent.compositionStart(input);
    fireEvent.change(input, { target: { value: "한" } });
    expect(onValueChange).not.toHaveBeenCalled();

    fireEvent.compositionEnd(input, { target: { value: "한" } });
    expect(onValueChange).toHaveBeenCalledTimes(1);
    expect(onValueChange.mock.calls.at(-1)?.[0]).toBe("한");
    expect(input).toHaveValue("한");
  });

  it("does not call onValueChange for insertCompositionText before compositionstart", () => {
    const onValueChange = vi.fn();
    render(<Input aria-label="ime-early" onValueChange={onValueChange} />);
    const input = screen.getByLabelText("ime-early");

    fireCompositionInput(input, { value: "ㅎ", inputType: "insertCompositionText" });
    expect(onValueChange).not.toHaveBeenCalled();

    fireEvent.compositionStart(input);
    fireEvent.compositionEnd(input, { target: { value: "하" } });
    expect(onValueChange).toHaveBeenCalledTimes(1);
    expect(onValueChange.mock.calls.at(-1)?.[0]).toBe("하");
  });

  it("does not call onValueChange for insertFromComposition inputType until compositionEnd", () => {
    const onValueChange = vi.fn();
    render(<Input aria-label="ime-from" onValueChange={onValueChange} />);
    const input = screen.getByLabelText("ime-from");

    fireCompositionInput(input, { value: "한", inputType: "insertFromComposition" });
    expect(onValueChange).not.toHaveBeenCalled();

    fireEvent.compositionEnd(input, { target: { value: "한" } });
    expect(onValueChange).toHaveBeenCalledTimes(1);
  });

  it("avoids duplicated Hangul syllable commit for dataObj-bound input", () => {
    const onValueChange = vi.fn();
    const dataObj = { name: "" };
    render(
      <Input
        aria-label="ime-bound"
        dataObj={dataObj}
        dataKey="name"
        filter="가-힣"
        onValueChange={onValueChange}
      />
    );
    const input = screen.getByLabelText("ime-bound");

    fireEvent.compositionStart(input);
    fireEvent.change(input, { target: { value: "한" } });
    fireEvent.compositionEnd(input, { target: { value: "한" } });

    expect(input).toHaveValue("한");
    expect(input.value).not.toMatch(/한{2,}/);
    expect(onValueChange).toHaveBeenCalledTimes(1);
    expect(onValueChange.mock.calls.at(-1)?.[0]).toBe("한");
  });

  it("keeps composed value visible when parent controlled update is delayed", async () => {
    vi.useFakeTimers();

    function DelayedControlledInput() {
      const [value, setValue] = useState("");
      return (
        <Input
          aria-label="ime-delayed"
          value={value}
          onValueChange={(nextValue) => {
            setTimeout(() => setValue(nextValue), 100);
          }}
        />
      );
    }

    render(<DelayedControlledInput />);
    const input = screen.getByLabelText("ime-delayed");

    fireEvent.compositionStart(input);
    fireEvent.change(input, { target: { value: "글" } });
    fireEvent.compositionEnd(input, { target: { value: "글" } });

    expect(input).toHaveValue("글");

    await act(async () => {
      vi.advanceTimersByTime(100);
    });

    expect(input).toHaveValue("글");
    vi.useRealTimers();
  });

  it("restores focus on the input after compositionEnd", () => {
    const onValueChange = vi.fn();
    render(
      <div>
        <button type="button">outside</button>
        <Input aria-label="ime-focus" onValueChange={onValueChange} />
      </div>
    );
    const input = screen.getByLabelText("ime-focus");
    input.focus();
    expect(input).toHaveFocus();

    fireEvent.compositionStart(input);
    fireEvent.compositionEnd(input, { target: { value: "가" } });

    expect(input).toHaveFocus();
  });

  it("filters Korean characters when filter allows Hangul", () => {
    const onValueChange = vi.fn();
    render(<Input aria-label="filter-ko" filter="가-힣" onValueChange={onValueChange} />);
    const input = screen.getByLabelText("filter-ko");

    fireEvent.change(input, { target: { value: "abc한글123" } });
    expect(input).toHaveValue("한글");
    expect(onValueChange.mock.calls.at(-1)?.[0]).toBe("한글");
  });

  it("filters English characters when filter allows latin letters", () => {
    const onValueChange = vi.fn();
    render(<Input aria-label="filter-en" filter="a-zA-Z" onValueChange={onValueChange} />);
    const input = screen.getByLabelText("filter-en");

    fireEvent.change(input, { target: { value: "abc123한글" } });
    expect(input).toHaveValue("abc");
    expect(onValueChange.mock.calls.at(-1)?.[0]).toBe("abc");
  });

  it("filters email characters when filter matches email pattern", () => {
    const onValueChange = vi.fn();
    render(
      <Input
        aria-label="filter-email"
        filter="a-zA-Z0-9@._+-"
        onValueChange={onValueChange}
      />
    );
    const input = screen.getByLabelText("filter-email");

    fireEvent.change(input, { target: { value: "user+tag@example.com!" } });
    expect(input).toHaveValue("user+tag@example.com");
    expect(onValueChange.mock.calls.at(-1)?.[0]).toBe("user+tag@example.com");
  });
});
