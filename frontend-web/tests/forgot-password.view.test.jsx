/**
 * 파일명: tests/forgot-password.view.test.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-03
 * 설명: 비밀번호 찾기 뷰 유효성/제출 성공 테스트
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

vi.mock("next/link", () => ({
  __esModule: true,
  default: ({ children, ...props }) => <a {...props}>{children}</a>,
}));

vi.mock("@/app/lib/hooks/usePageData", () => ({
  __esModule: true,
  usePageData: vi.fn(),
}));

vi.mock("@/app/lib/runtime/api", () => ({
  __esModule: true,
  apiJSON: vi.fn(),
}));

import ForgotPasswordView from "@/app/forgot-password/view";
import { apiJSON } from "@/app/lib/runtime/api";

const ensureRaf = () => {
  if (!window.requestAnimationFrame) {
    window.requestAnimationFrame = (cb) => setTimeout(cb, 0);
  }
};

beforeEach(() => {
  vi.clearAllMocks();
  ensureRaf();
});

test("이메일 형식이 잘못되면 에러를 노출하고 이메일 입력으로 포커스한다", async () => {
  render(<ForgotPasswordView initialDataObj={{}} initialErrorObj={{}} />);

  fireEvent.change(screen.getByLabelText("이메일"), {
    target: { value: "invalid-email" },
  });
  fireEvent.click(screen.getByRole("button", { name: "재설정 안내 받기" }));

  await waitFor(() => {
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });
  expect(screen.getByRole("alert").textContent).toContain("올바른 이메일 형식을 입력해주세요.");
  await waitFor(() => {
    expect(document.activeElement?.id).toBe("forgot-email");
  });
});

test("유효한 이메일 제출 후 안내 메시지를 노출한다", async () => {
  apiJSON.mockResolvedValue({
    status: true,
    message: "",
    result: { accepted: true },
    requestId: "req-1",
  });

  render(<ForgotPasswordView initialDataObj={{}} initialErrorObj={{}} />);

  fireEvent.change(screen.getByLabelText("이메일"), {
    target: { value: "  tester@demo.com  " },
  });
  fireEvent.click(screen.getByRole("button", { name: "재설정 안내 받기" }));

  await waitFor(() => {
    expect(
      screen.getByText(
        "입력하신 이메일로 안내를 보냈습니다. 샘플 환경에서는 실제 메일이 발송되지 않습니다.",
      ),
    ).toBeInTheDocument();
  });
});

test("요청 실패 시 공통 오류 요약을 노출한다", async () => {
  apiJSON.mockRejectedValue(new Error("network failed"));

  render(<ForgotPasswordView initialDataObj={{}} initialErrorObj={{}} />);

  fireEvent.change(screen.getByLabelText("이메일"), {
    target: { value: "tester@demo.com" },
  });
  fireEvent.click(screen.getByRole("button", { name: "재설정 안내 받기" }));

  await waitFor(() => {
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });
  expect(screen.getByRole("alert").textContent).toContain(
    "요청 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
  );
});
