/**
 * 파일명: tests/login.view.test.jsx
 * 작성자: LSH
 * 갱신일: 2026-06-05
 * 설명: 로그인 뷰 유효성/에러/리다이렉트 테스트
 */

import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi } from "vitest";

vi.mock("@/app/lib/hooks/useSwr", () => ({
  __esModule: true,
  default: vi.fn(),
}));

vi.mock("@/app/lib/runtime/api", () => ({
  __esModule: true,
  apiJSON: vi.fn(),
}));

import Client from "@/app/login/view";
import LANG_KO from "@/app/login/lang.ko";
import useSwr from "@/app/lib/hooks/useSwr";
import { apiJSON } from "@/app/lib/runtime/api";

const mutateMock = vi.fn();

const ensureRaf = () => {
  if (!window.requestAnimationFrame) {
    window.requestAnimationFrame = (cb) => setTimeout(cb, 0);
  }
};

const renderLogin = (props = {}) => {
  useSwr.mockReturnValue({ data: { result: null }, mutate: mutateMock });
  return render(<Client mode="CSR" init={null} nextHint={null} {...props} />);
};

beforeEach(() => {
  vi.clearAllMocks();
  mutateMock.mockReset();
  ensureRaf();
});

test("폼 유효성 검사 후 첫 번째 에러 필드에 포커스한다", async () => {
  renderLogin();

  fireEvent.click(screen.getByRole("button", { name: "로그인" }));

  await waitFor(() => {
    expect(
      screen.getAllByText("비밀번호를 입력해주세요").length,
    ).toBeGreaterThan(0);
  });

  await waitFor(() => {
    expect(document.activeElement?.id).toBe("login-password");
  });
});

test("백엔드 인증 오류를 비밀번호 필드와 에러 요약으로 노출한다", async () => {
  useSwr.mockReturnValue({ data: { result: null }, mutate: mutateMock });
  apiJSON.mockRejectedValue({
    name: "ApiError",
    statusCode: 401,
    code: "AUTH_401_INVALID",
    message: "invalid credentials",
  });

  renderLogin();

  fireEvent.change(screen.getByLabelText("비밀번호"), {
    target: { value: "password123" },
  });
  fireEvent.click(screen.getByRole("button", { name: "로그인" }));

  await waitFor(() => {
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });
  expect(screen.getByRole("alert").textContent).toContain(
    "비밀번호가 올바르지 않습니다",
  );
  expect(
    screen.getAllByText(/비밀번호가 올바르지 않습니다/i).length,
  ).toBeGreaterThan(0);
  await waitFor(() => {
    expect(document.activeElement?.id).toBe("login-password");
  });
});

test("레이트리밋(429) 오류를 에러 요약으로 노출한다", async () => {
  useSwr.mockReturnValue({ data: { result: null }, mutate: mutateMock });
  apiJSON.mockRejectedValue({
    name: "ApiError",
    statusCode: 429,
    code: "AUTH_429_RATE_LIMIT",
    message: "too many requests",
  });

  renderLogin();

  fireEvent.change(screen.getByLabelText("비밀번호"), {
    target: { value: "password123" },
  });
  fireEvent.click(screen.getByRole("button", { name: "로그인" }));

  await waitFor(() => {
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });
  expect(screen.getByRole("alert").textContent).toContain("로그인 시도가 너무 많습니다");
});

test("입력 오류(422) 응답 코드를 사용자 메시지로 매핑한다", async () => {
  useSwr.mockReturnValue({ data: { result: null }, mutate: mutateMock });
  apiJSON.mockRejectedValue({
    name: "ApiError",
    statusCode: 422,
    code: "AUTH_422_INVALID_INPUT",
    message: "invalid input",
  });

  renderLogin();

  fireEvent.change(screen.getByLabelText("비밀번호"), {
    target: { value: "password123" },
  });
  fireEvent.click(screen.getByRole("button", { name: "로그인" }));

  await waitFor(() => {
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });
  expect(screen.getByRole("alert").textContent).toContain("입력값을 확인해 주세요.");
});

test("로그인 성공 시 next가 없으면 대시보드로 이동한다", async () => {
  useSwr.mockReturnValue({ data: { result: null }, mutate: mutateMock });
  mutateMock.mockResolvedValue({ result: { username: "demo" } });
  apiJSON.mockResolvedValue({ status: true, result: {} });

  const assignMock = vi.fn();
  const originalLocation = globalThis.location;
  vi.stubGlobal("location", {
    ...originalLocation,
    assign: assignMock,
    replace: vi.fn(),
  });

  renderLogin();

  fireEvent.change(screen.getByLabelText("비밀번호"), {
    target: { value: "password123" },
  });
  fireEvent.click(screen.getByRole("button", { name: "로그인" }));

  await waitFor(() => {
    expect(assignMock).toHaveBeenCalledWith("/dashboard");
  });
  expect(apiJSON).toHaveBeenCalledWith(
    expect.objectContaining({
      path: "/api/v1/auth/login",
      method: "POST",
    }),
    expect.objectContaining({
      method: "POST",
      body: expect.objectContaining({
        username: "demo@demo.demo",
        password: "password123",
      }),
    }),
  );

  vi.unstubAllGlobals();
});

test("공개 로그인 화면은 hwiStock 운영 안내를 표시하고 샘플·데모·템플릿 문구를 노출하지 않는다", () => {
  renderLogin();

  expect(LANG_KO.page.metadataTitle).toBe("Login | hwiStock");
  expect(screen.getByText("hwiStock 운영 콘솔")).toBeInTheDocument();
  expect(screen.getByText("운영자 비밀번호를 입력하세요")).toBeInTheDocument();
  expect(screen.getByText("아이디 입력 없이 운영자 비밀번호만 확인합니다.")).toBeInTheDocument();
  expect(screen.getByText("운영자 인증")).toBeInTheDocument();
  expect(screen.queryByLabelText("이메일")).not.toBeInTheDocument();
  expect(screen.queryByText("회원가입")).not.toBeInTheDocument();
  expect(screen.queryByText(/MyWebTemplate/i)).not.toBeInTheDocument();
  expect(screen.queryByText(/웹페이지 템플릿/i)).not.toBeInTheDocument();
  expect(screen.queryByText(/샘플 로그인/i)).not.toBeInTheDocument();
  expect(screen.queryByText(/\/component/i)).not.toBeInTheDocument();
  expect(screen.queryByText(/demo@demo\.demo/i)).not.toBeInTheDocument();
  expect(screen.queryByText(/password123/i)).not.toBeInTheDocument();
});

test("비밀번호 표시 토글 버튼으로 입력 타입을 전환한다", () => {
  renderLogin();

  const passwordInput = screen.getByLabelText("비밀번호");
  expect(passwordInput).toHaveAttribute("type", "password");

  fireEvent.click(screen.getByRole("button", { name: "비밀번호 보기" }));
  expect(passwordInput).toHaveAttribute("type", "text");

  fireEvent.click(screen.getByRole("button", { name: "비밀번호 숨기기" }));
  expect(passwordInput).toHaveAttribute("type", "password");
});
