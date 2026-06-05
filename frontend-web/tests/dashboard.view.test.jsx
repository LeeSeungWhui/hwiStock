/**
 * 파일명: tests/dashboard.view.test.jsx
 * 설명: hwiStock 운영 콘솔 뷰 테스트
 */

import { act, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import { apiJSON } from "@/app/lib/runtime/api";
import { PAGE_CONFIG } from "@/app/dashboard/initData";
import DashboardView from "@/app/dashboard/view";
import { OPERATOR_FALLBACK_FIXTURE } from "@/app/dashboard/operatorData";

vi.mock("@/app/lib/runtime/api", () => ({
  apiJSON: vi.fn(),
}));

describe("hwiStock operator console view", () => {
  let consoleErrorSpy;
  const originalMode = PAGE_CONFIG.MODE;

  const buildSsrInitialDataObj = ({
    statList = [{ status: "ready", count: 1, amountSum: 1000 }],
    dataList = [
      {
        id: 1,
        title: "삼성전자",
        status: "running",
        amount: 120,
        createdAt: "2026-02-23T00:00:00.000Z",
      },
    ],
  } = {}) => ({
    stats: {
      result: {
        statusSummaryList: statList,
      },
    },
    list: {
      result: {
        dataTemplateList: dataList,
      },
    },
  });

  beforeEach(() => {
    vi.clearAllMocks();
    apiJSON.mockReset();
    consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    PAGE_CONFIG.MODE = originalMode;
  });

  afterEach(() => {
    consoleErrorSpy?.mockRestore();
    PAGE_CONFIG.MODE = originalMode;
  });

  test("운영 콘솔 핵심 섹션이 렌더링된다", () => {
    render(
      <DashboardView
        initialDataObj={buildSsrInitialDataObj()}
        initialErrorObj={{}}
      />,
    );

    expect(screen.getByTestId("hwistock-operator-console")).toBeInTheDocument();
    expect(screen.getByTestId("operator-status-strip")).toBeInTheDocument();
    expect(screen.getByTestId("operator-pane-summary")).toBeInTheDocument();
    expect(screen.getByTestId("operator-pane-data")).toBeInTheDocument();
    expect(screen.getByTestId("operator-pane-review")).toBeInTheDocument();
    expect(screen.getByTestId("operator-readiness-truth")).toBeInTheDocument();
    expect(screen.getByTestId("operator-holdings")).toBeInTheDocument();
    expect(screen.getByTestId("operator-candidates")).toBeInTheDocument();
    expect(screen.getByTestId("operator-intelligence")).toBeInTheDocument();
    expect(screen.getByTestId("operator-ai-thread")).toBeInTheDocument();
    expect(screen.getByTestId("operator-audit-log")).toBeInTheDocument();
    expect(screen.getByText("hwiStock 운영 콘솔")).toBeInTheDocument();
    expect(screen.queryByText("업무 바로가기")).not.toBeInTheDocument();
    expect(screen.queryByText("MyWebTemplate")).not.toBeInTheDocument();
    expect(screen.getByText("모의매매 관찰 준비 아님")).toBeInTheDocument();
    expect(screen.getByText("NOT_READY_FOR_PAPER_TRADING")).toBeInTheDocument();
  });

  test("매수/매도/주문 실행 버튼이 없다", () => {
    render(
      <DashboardView
        initialDataObj={buildSsrInitialDataObj()}
        initialErrorObj={{}}
      />,
    );

    const forbiddenLabelList = ["매수", "매도", "주문", "Buy", "Sell", "Order"];
    forbiddenLabelList.forEach((label) => {
      expect(screen.queryByRole("button", { name: new RegExp(label, "i") })).not.toBeInTheDocument();
    });
  });

  test("계좌 식별자와 잔고류 값은 마스킹된다", () => {
    render(
      <DashboardView
        initialDataObj={buildSsrInitialDataObj({ statList: [], dataList: [] })}
        initialErrorObj={{}}
      />,
    );

    const rawAccountId = OPERATOR_FALLBACK_FIXTURE.summary.accountId;
    expect(screen.queryByText(rawAccountId)).not.toBeInTheDocument();
    expect(screen.getAllByTitle(/masked/i).length).toBeGreaterThan(0);
  });

  test("에러는 code/requestId만 노출하고 raw JSON 페이로드는 렌더하지 않는다", () => {
    const rawPayload = '{"account":"50123456789012","apiKey":"secret-key"}';
    render(
      <DashboardView
        initialDataObj={buildSsrInitialDataObj()}
        initialErrorObj={{
          stats: {
            key: "INIT_FETCH_FAILED",
            code: "OPERATOR_500",
            requestId: "rid-operator-init",
            message: rawPayload,
          },
        }}
      />,
    );

    expect(screen.getByText("운영 콘솔 데이터를 불러오지 못했습니다.")).toBeInTheDocument();
    expect(screen.getByText("requestId: rid-operator-init")).toBeInTheDocument();
    expect(screen.getByText("code: OPERATOR_500")).toBeInTheDocument();
    expect(screen.queryByText(rawPayload)).not.toBeInTheDocument();
    expect(screen.queryByText("secret-key")).not.toBeInTheDocument();
    expect(screen.queryByText("50123456789012")).not.toBeInTheDocument();
  });

  test("CSR fetch 실패 시 sanitized 에러 라벨만 노출한다", async () => {
    PAGE_CONFIG.MODE = "CSR";
    const fetchError = new Error('{"broker":"kis","token":"abc"}');
    fetchError.code = "OPERATOR_FETCH_FAIL";
    fetchError.requestId = "rid-operator-fetch";
    apiJSON.mockRejectedValue(fetchError);

    render(
      <DashboardView
        initialDataObj={{}}
        initialErrorObj={{}}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText("운영 콘솔 데이터를 불러오지 못했습니다.")).toBeInTheDocument();
    });
    expect(screen.getByText("requestId: rid-operator-fetch")).toBeInTheDocument();
    expect(screen.getByText("code: OPERATOR_FETCH_FAIL")).toBeInTheDocument();
    expect(screen.queryByText("abc")).not.toBeInTheDocument();
  });

  test("CSR fetch 지연 중 스켈레톤 후 콘솔 스냅샷을 렌더링한다", async () => {
    PAGE_CONFIG.MODE = "CSR";
    let resolveOperator;
    apiJSON
      .mockImplementationOnce(
        () =>
          new Promise((resolve) => {
            resolveOperator = resolve;
          }),
      );

    render(
      <DashboardView
        initialDataObj={{}}
        initialErrorObj={{}}
      />,
    );

    await act(async () => {
      resolveOperator({
        result: {
          schema_version: "operator_console_snapshot/v0",
          status: { mode: "paper_sandbox", serviceHealth: "observable", orderGate: "blocked_calendar_unconfigured" },
          summary: {
            accountId: "paper_account_alias:masked",
            paperNetworkEnabled: false,
            paperOrdersSubmitted: false,
            paperObservationAccepted: false,
            operationalTradingReadiness: false,
          },
          readinessTruth: {
            headline: "NOT_READY_FOR_PAPER_TRADING",
            operatorMessage: "서비스가 떠 있어도 모의매매 준비 완료가 아닙니다.",
            blockers: ["paper_network_disabled", "blocked_calendar_unconfigured"],
            paperNetworkEnabled: false,
            paperOrdersSubmitted: false,
            paperObservationAccepted: false,
            operationalTradingReadiness: false,
            orderGate: "blocked_calendar_unconfigured",
            serviceVisibilityIsNotReadiness: true,
          },
          holdings: [
            { symbol: "005930", name: "삼성전자", qty: 0, pnl: "system", weight: "0%" },
          ],
        },
      });
    });

    await waitFor(() => {
      expect(screen.getByText("삼성전자")).toBeInTheDocument();
    });
    expect(screen.getByTestId("operator-ai-thread")).toBeInTheDocument();
    expect(screen.getByText("blocked_calendar_unconfigured")).toBeInTheDocument();
  });
});
