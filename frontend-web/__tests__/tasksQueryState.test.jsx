import { render, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import TasksView from "@/app/dashboard/tasks/view";
import { apiJSON } from "@/app/lib/runtime/api";

const replaceMock = vi.fn();
const pushMock = vi.fn();
let currentSearchParams = new URLSearchParams();

const setSearchParams = (queryObj = {}) => {
  currentSearchParams = new URLSearchParams(queryObj);
};

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: replaceMock, push: pushMock }),
  usePathname: () => "/dashboard/tasks",
  useSearchParams: () => currentSearchParams,
}));

vi.mock("@/app/common/store/SharedStore", () => ({
  useGlobalUi: () => ({
    showToast: vi.fn(),
    showConfirm: vi.fn().mockResolvedValue(true),
  }),
}));

vi.mock("@/app/lib/runtime/api", () => ({
  apiJSON: vi.fn(),
}));

vi.mock("@/app/lib/component/Badge", () => ({
  __esModule: true,
  default: ({ children }) => <span>{children}</span>,
}));

vi.mock("@/app/lib/component/Button", () => ({
  __esModule: true,
  default: ({ children, onClick, className, disabled }) => (
    <button type="button" onClick={onClick} className={className} disabled={disabled}>
      {children}
    </button>
  ),
}));

vi.mock("@/app/lib/component/Card", () => ({
  __esModule: true,
  default: ({ title, actions, children }) => (
    <section>
      <h2>{title}</h2>
      {actions}
      {children}
    </section>
  ),
}));

vi.mock("@/app/lib/component/EasyTable", () => ({
  __esModule: true,
  default: () => <div data-testid="table">table</div>,
}));

vi.mock("@/app/lib/component/Input", () => ({
  __esModule: true,
  default: ({ value = "", onChange, placeholder }) => (
    <input value={value} onChange={onChange} placeholder={placeholder} readOnly={!onChange} />
  ),
}));

vi.mock("@/app/lib/component/Pagination", () => ({
  __esModule: true,
  default: () => null,
}));

vi.mock("@/app/lib/component/Select", () => ({
  __esModule: true,
  default: ({ value = "", onChange, dataList = [] }) => (
    <select value={value} onChange={onChange} disabled={!onChange}>
      {dataList.map((optionItemObj, index) => (
        <option key={`${String(optionItemObj?.value)}-${index}`} value={optionItemObj?.value}>
          {optionItemObj?.text || optionItemObj?.label || String(optionItemObj?.value)}
        </option>
      ))}
    </select>
  ),
}));

describe("tasks query state", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setSearchParams();
    apiJSON.mockResolvedValue({
      count: 0,
      result: {
        dataTemplateList: [],
        listMetaObj: {
          totalCount: 0,
        },
      },
    });
  });

  test("검색 파라미터를 안전하게 정규화해 목록 API를 호출한다", async () => {
    setSearchParams({
      q: "  백엔드  ",
      status: "RUNNING",
      sort: "AMT_DESC",
      page: "3",
    });

    render(<TasksView initialDataObj={{}} initialErrorObj={{}} />);

    await waitFor(() => {
      expect(apiJSON).toHaveBeenCalled();
    });
    const requestSpec = apiJSON.mock.calls[0][0];
    const requestUrl = typeof requestSpec === "string" ? requestSpec : requestSpec.path;
    const decodedRequestUrl = decodeURIComponent(requestUrl);
    expect(decodedRequestUrl).toContain("q=백엔드");
    expect(requestUrl).toContain("status=running");
    expect(requestUrl).toContain("sort=amt_desc");
    expect(requestUrl).toContain("page=3");
    expect(requestUrl).toContain("size=10");
  });

  test("허용되지 않은 값은 기본값으로 보정한다", async () => {
    setSearchParams({
      q: "first",
      status: "UNKNOWN",
      sort: "DROP_TABLE",
      page: "0",
    });

    render(<TasksView initialDataObj={{}} initialErrorObj={{}} />);

    await waitFor(() => {
      expect(apiJSON).toHaveBeenCalled();
    });
    const requestSpec = apiJSON.mock.calls[0][0];
    const requestUrl = typeof requestSpec === "string" ? requestSpec : requestSpec.path;
    expect(requestUrl).toContain("q=first");
    expect(requestUrl).not.toContain("status=");
    expect(requestUrl).toContain("sort=reg_dt_desc");
    expect(requestUrl).toContain("page=1");
  });

  test("초기 목록 조회는 브라우저 쿼리 문자열을 재기록하지 않는다", async () => {
    setSearchParams({ q: "테스트", status: "ready", sort: "amt_desc", page: "2" });

    render(<TasksView initialDataObj={{}} initialErrorObj={{}} />);

    await waitFor(() => {
      expect(apiJSON).toHaveBeenCalled();
    });
    expect(replaceMock).not.toHaveBeenCalled();
  });

  test("유효 상태값이면 상태 필터를 유지한다", async () => {
    setSearchParams({ status: "pending" });

    render(<TasksView initialDataObj={{}} initialErrorObj={{}} />);

    await waitFor(() => {
      expect(apiJSON).toHaveBeenCalled();
    });
    const requestSpec = apiJSON.mock.calls[0][0];
    const requestUrl = typeof requestSpec === "string" ? requestSpec : requestSpec.path;
    expect(requestUrl).toContain("status=pending");
  });

  test("생성·수정·삭제·저장 버튼이 노출되지 않는다", async () => {
    const { container } = render(<TasksView />);

    await waitFor(() => {
      expect(apiJSON).toHaveBeenCalled();
    });
    const buttonText = Array.from(container.querySelectorAll("button"))
      .map((buttonEl) => buttonEl.textContent || "")
      .join(" ");
    expect(buttonText).not.toMatch(/등록|수정|삭제|저장/);
  });
});
