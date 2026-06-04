/**
 * 파일명: tests/signup.view.test.jsx
 * 작성자: LSH
 * 갱신일: 2026-03-03
 * 설명: 회원가입 뷰 검증/에러/성공 리다이렉트 테스트
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

vi.mock("@/app/common/store/SharedStore", () => ({
  __esModule: true,
  useGlobalUi: vi.fn(),
}));

vi.mock("@/app/lib/runtime/api", () => ({
  __esModule: true,
  apiJSON: vi.fn(),
}));

import SignupView from "@/app/signup/view";
import { useGlobalUi } from "@/app/common/store/SharedStore";
import { apiJSON } from "@/app/lib/runtime/api";

const showToastMock = vi.fn();

const ensureRaf = () => {
  if (!window.requestAnimationFrame) {
    window.requestAnimationFrame = (cb) => setTimeout(cb, 0);
  }
};

const fillValidForm = () => {
  fireEvent.change(screen.getByLabelText("이름"), {
    target: { value: "테스터" },
  });
  fireEvent.change(screen.getByLabelText("이메일"), {
    target: { value: "tester@demo.com" },
  });
  fireEvent.change(screen.getByLabelText("비밀번호"), {
    target: { value: "password123" },
  });
  fireEvent.change(screen.getByLabelText("비밀번호 확인"), {
    target: { value: "password123" },
  });
  fireEvent.click(screen.getByRole("checkbox"));
};

beforeEach(() => {
  vi.clearAllMocks();
  ensureRaf();
  useGlobalUi.mockReturnValue({
    showToast: showToastMock,
  });
});

test("유효성 검사 실패 시 첫 번째 에러 필드에 포커스한다", async () => {
  render(<SignupView initialDataObj={{}} initialErrorObj={{}} />);

  fireEvent.click(screen.getByRole("button", { name: "회원가입" }));

  await waitFor(() => {
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });
  expect(screen.getByRole("alert").textContent).toContain("이름은 2자 이상 입력해주세요.");

  await waitFor(() => {
    expect(document.activeElement?.id).toBe("signup-name");
  });
});

test("중복 이메일 오류를 이메일 필드/요약 에러로 노출한다", async () => {
  apiJSON.mockRejectedValue({
    name: "ApiError",
    statusCode: 409,
    code: "AUTH_409_USER_EXISTS",
    message: "already exists",
  });

  render(<SignupView initialDataObj={{}} initialErrorObj={{}} />);
  fillValidForm();
  fireEvent.click(screen.getByRole("button", { name: "회원가입" }));

  await waitFor(() => {
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });
  expect(screen.getByRole("alert").textContent).toContain("이미 사용 중인 이메일입니다.");
  await waitFor(() => {
    expect(document.activeElement?.id).toBe("signup-email");
  });
});

test("회원가입 성공 시 로그인 경로로 이동하고 성공 토스트를 노출한다", async () => {
  apiJSON.mockResolvedValue({ status: true, result: {} });

  const assignMock = vi.fn();
  const originalLocation = globalThis.location;
  vi.stubGlobal("location", {
    ...originalLocation,
    assign: assignMock,
    replace: vi.fn(),
  });

  render(<SignupView initialDataObj={{}} initialErrorObj={{}} />);
  fillValidForm();
  fireEvent.click(screen.getByRole("button", { name: "회원가입" }));

  await waitFor(() => {
    expect(assignMock).toHaveBeenCalledWith("/login?signup=done");
  });
  expect(showToastMock).toHaveBeenCalled();
  vi.unstubAllGlobals();
});
