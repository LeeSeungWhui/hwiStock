/**
 * 파일명: __tests__/settingsTabQuery.test.jsx
 * 설명: 운영 정책 페이지 탭-쿼리 동기화 동작 테스트
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import SettingsView from "@/app/dashboard/settings/view";
import { apiJSON } from "@/app/lib/runtime/api";

const replaceMock = vi.fn();
let currentSearchParams = new URLSearchParams();

const setSearchParams = (queryObj = {}) => {
  currentSearchParams = new URLSearchParams(queryObj);
};

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: replaceMock }),
  usePathname: () => "/dashboard/settings",
  useSearchParams: () => currentSearchParams,
}));

vi.mock("@/app/common/store/SharedStore", () => ({
  useGlobalUi: () => ({
    showToast: vi.fn(),
  }),
}));

vi.mock("@/app/lib/runtime/api", () => ({
  apiJSON: vi.fn(),
}));

vi.mock("@/app/lib/component/Badge", () => ({
  __esModule: true,
  default: ({ children }) => <span>{children}</span>,
}));

vi.mock("@/app/lib/component/Card", () => ({
  __esModule: true,
  default: ({ title, children }) => (
    <section>
      <h2>{title}</h2>
      {children}
    </section>
  ),
}));

vi.mock("@/app/lib/component/Input", () => ({
  __esModule: true,
  default: ({ value = "", onChange, readOnly, placeholder }) => (
    <input value={value} onChange={onChange} readOnly={Boolean(readOnly || !onChange)} placeholder={placeholder} />
  ),
}));

vi.mock("@/app/lib/component/Switch", () => ({
  __esModule: true,
  default: ({ checked = false, onChange, label, disabled }) => (
    <label>
      <input type="checkbox" checked={checked} onChange={onChange} readOnly={Boolean(disabled || !onChange)} />
      {label}
    </label>
  ),
}));

vi.mock("@/app/lib/component/Tab", () => {
  const Tab = ({ tabIndex = 0, onValueChange, children }) => (
    <div>
      <button type="button" onClick={() => onValueChange?.(0)}>
        policy-tab
      </button>
      <button type="button" onClick={() => onValueChange?.(1)}>
        connection-tab
      </button>
      <div data-testid="active-tab">{String(tabIndex)}</div>
      {children}
    </div>
  );

  const TabItem = ({ children }) => <div>{children}</div>;
  TabItem.displayName = "MockTabItem";
  Tab.Item = TabItem;
  return {
    __esModule: true,
    default: Tab,
  };
});

describe("settings tab query helpers", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setSearchParams();
    apiJSON.mockResolvedValue({
      result: {
        userId: "demo@demo.demo",
        userNm: "데모",
        userEml: "demo@demo.demo",
        roleCd: "user",
        notifyEmail: false,
        notifySms: false,
        notifyPush: false,
      },
    });
  });

  test("tab 쿼리가 없거나 잘못되면 policy 탭으로 정규화한다", async () => {
    setSearchParams();
    const firstRender = render(<SettingsView initialDataObj={{}} initialErrorObj={{}} />);

    await waitFor(() => {
      expect(apiJSON).toHaveBeenCalled();
    });
    expect(screen.getByTestId("active-tab")).toHaveTextContent("0");

    firstRender.unmount();

    vi.clearAllMocks();
    setSearchParams({ tab: "unknown" });
    apiJSON.mockResolvedValue({
      result: {
        userId: "demo@demo.demo",
        userNm: "데모",
        userEml: "demo@demo.demo",
        roleCd: "user",
        notifyEmail: false,
        notifySms: false,
        notifyPush: false,
      },
    });
    render(<SettingsView initialDataObj={{}} initialErrorObj={{}} />);

    await waitFor(() => {
      expect(apiJSON).toHaveBeenCalled();
    });
    expect(screen.getByTestId("active-tab")).toHaveTextContent("0");
  });

  test("tab=connection이면 connection 탭으로 정규화한다", async () => {
    setSearchParams({ tab: "connection" });

    render(<SettingsView initialDataObj={{}} initialErrorObj={{}} />);

    await waitFor(() => {
      expect(apiJSON).toHaveBeenCalled();
    });
    await waitFor(() => {
      expect(screen.getByTestId("active-tab")).toHaveTextContent("1");
    });
  });

  test("탭 인덱스 변경 시 쿼리값 변환이 일관된다", async () => {
    setSearchParams();

    render(<SettingsView initialDataObj={{}} initialErrorObj={{}} />);

    await waitFor(() => {
      expect(apiJSON).toHaveBeenCalled();
    });

    fireEvent.click(screen.getByRole("button", { name: "connection-tab" }));
    expect(replaceMock).toHaveBeenCalledWith("/dashboard/settings?tab=connection", {
      scroll: false,
    });

    fireEvent.click(screen.getByRole("button", { name: "policy-tab" }));
    expect(replaceMock).toHaveBeenCalledWith("/dashboard/settings", {
      scroll: false,
    });
  });

  test("저장 버튼이 노출되지 않는다", async () => {
    render(<SettingsView initialDataObj={{}} initialErrorObj={{}} />);

    await waitFor(() => {
      expect(apiJSON).toHaveBeenCalled();
    });
    expect(screen.queryByRole("button", { name: /저장/i })).not.toBeInTheDocument();
  });
});
