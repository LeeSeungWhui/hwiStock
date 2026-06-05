/**
 * 파일명: tests/dashboard.view.test.jsx
 * 설명: hwiStock 운영 콘솔 뷰 테스트
 */

import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import { apiJSON } from "@/app/lib/runtime/api";
import { PAGE_CONFIG } from "@/app/dashboard/initData";
import DashboardView from "@/app/dashboard/view";

vi.mock("@/app/lib/runtime/api", () => ({
  apiJSON: vi.fn(),
}));

describe("hwiStock operator console view", () => {
  let consoleErrorSpy;
  const originalMode = PAGE_CONFIG.MODE;

  const buildSsrInitialDataObj = ({
    operatorSnapshot = {
      schema_version: "operator_console_snapshot/v0",
      status: {
        mode: "paper_sandbox",
        serviceHealth: "observable",
        orderGate: "blocked_calendar_unconfigured",
      },
      summary: {
        accountId: "12345678-01",
        cashBalance: 2000000,
        reserveBalance: 500000,
        todayPnl: -84200,
        realizedPnl: 12000,
        aiJobStatus: "pro:present / flash:missing_or_safe_blocked",
        reportStatus: "continuous_tick:warn",
        paperNetworkEnabled: false,
        paperOrderEnabled: false,
        paperOrdersSubmitted: false,
        paperObservationAccepted: false,
        operationalTradingReadiness: false,
      },
      readinessTruth: {
        headline: "NOT_READY_FOR_PAPER_TRADING",
        operatorMessage: "서비스가 떠 있어도 모의매매 준비 완료가 아닙니다.",
        blockers: ["paper_network_disabled", "blocked_calendar_unconfigured"],
        paperNetworkEnabled: false,
        paperOrderEnabled: false,
        paperOrdersSubmitted: false,
        paperObservationAccepted: false,
        operationalTradingReadiness: false,
        orderGate: "blocked_calendar_unconfigured",
        serviceVisibilityIsNotReadiness: true,
      },
      holdings: [],
      candidates: [],
      intelligence: [],
      aiThread: [],
      auditLog: [
        { at: "18:00", level: "info", code: "ORDER_GATE", message: "blocked_calendar_unconfigured" },
      ],
    },
  } = {}) => ({
    operator: {
      result: {
        ...operatorSnapshot,
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
    expect(screen.getByTestId("operator-ai-report")).toBeInTheDocument();
    expect(screen.getByTestId("operator-ai-conversation")).toBeInTheDocument();
    expect(screen.getByTestId("operator-ai-conversation-disclaimer")).toBeInTheDocument();
    expect(screen.getByTestId("operator-ai-question-input")).toBeInTheDocument();
    expect(screen.getByTestId("operator-ai-question-submit")).toBeInTheDocument();
    expect(screen.getByTestId("operator-section-nav")).toBeInTheDocument();
    expect(screen.getByTestId("operator-audit-log")).toBeInTheDocument();
    expect(screen.getByText("hwiStock Lucid Command")).toBeInTheDocument();
    expect(screen.queryByText("업무 바로가기")).not.toBeInTheDocument();
    expect(screen.queryByText("MyWebTemplate")).not.toBeInTheDocument();
    expect(screen.queryByText("paper_sandbox")).not.toBeInTheDocument();
    expect(screen.queryByText(/모의매매/)).not.toBeInTheDocument();
    expect(screen.getByText("운영 관찰")).toBeInTheDocument();
    expect(screen.getByText("자동매매 준비 전")).toBeInTheDocument();
    expect(screen.getByText("준비 전")).toBeInTheDocument();
    expect(screen.getByText(/주문 실행 허용/)).toBeInTheDocument();
    expect(screen.getAllByText("시장 시간표 설정 필요").length).toBeGreaterThan(0);
  });

  test("AI 대화 패널은 읽기 전용 안내와 질문 입력을 노출한다", () => {
    render(
      <DashboardView
        initialDataObj={buildSsrInitialDataObj()}
        initialErrorObj={{}}
      />,
    );

    expect(screen.getByText(/설명·분석 전용/)).toBeInTheDocument();
    expect(screen.getByLabelText("질문 입력")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "질문 보내기" })).toBeInTheDocument();
    expect(screen.getAllByText("AI 리포트").length).toBeGreaterThan(0);
    expect(screen.getAllByText("AI 대화").length).toBeGreaterThan(0);
  });

  test("AI 대화 질문은 백엔드 대화 endpoint로 전달되고 거절 응답을 표시한다", async () => {
    apiJSON.mockResolvedValueOnce({
      result: {
        refused: true,
        refusal: "주문 실행은 지원하지 않습니다.",
        requestId: "rid-ai-conversation-1",
      },
    });

    render(
      <DashboardView
        initialDataObj={buildSsrInitialDataObj()}
        initialErrorObj={{}}
      />,
    );

    fireEvent.change(screen.getByLabelText("질문 입력"), {
      target: { value: "지금 바로 주문해줘" },
    });
    fireEvent.click(screen.getByRole("button", { name: "질문 보내기" }));

    await waitFor(() => {
      expect(apiJSON).toHaveBeenCalledWith("/api/v1/hwistock/ai/conversation", {
        method: "POST",
        body: { question: "지금 바로 주문해줘" },
      });
    });
    expect(await screen.findByText(/요청 거절/)).toBeInTheDocument();
    expect(screen.getByText("주문 실행은 지원하지 않습니다.")).toBeInTheDocument();
    expect(screen.getByText("requestId: rid-ai-conversation-1")).toBeInTheDocument();
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

  test("요약 패널은 계좌와 금액을 숨기지 않고 운영자가 읽을 포맷으로 렌더링한다", () => {
    render(
      <DashboardView
        initialDataObj={buildSsrInitialDataObj()}
        initialErrorObj={{}}
      />,
    );

    expect(screen.queryByText(/sked/)).not.toBeInTheDocument();
    expect(screen.queryByText("system_report_only")).not.toBeInTheDocument();
    expect(screen.queryByText("continuous_tick:warn")).not.toBeInTheDocument();
    expect(screen.getByText("12345678-01")).toBeInTheDocument();
    expect(screen.getByText("2,000,000원")).toBeInTheDocument();
    expect(screen.getByText("500,000원")).toBeInTheDocument();
    expect(screen.getByText("-84,200원")).toBeInTheDocument();
    expect(screen.getByText("+12,000원")).toBeInTheDocument();
    expect(screen.getByText("Pro 분석 있음 · Flash 문서 대기/안전 차단")).toBeInTheDocument();
    expect(screen.getByText("자동 점검: 주의")).toBeInTheDocument();
  });

  test("legacy placeholder가 들어와도 sked 같은 잘린 문자열 대신 안내 문구를 렌더링한다", () => {
    render(
      <DashboardView
        initialDataObj={buildSsrInitialDataObj({
          operatorSnapshot: {
            schema_version: "operator_console_snapshot/v0",
            status: {
              mode: "paper_sandbox",
              serviceHealth: "observable",
              orderGate: "blocked_calendar_unconfigured",
            },
            summary: {
              accountId: "paper_account_alias:masked",
              cashBalance: "masked",
              reserveBalance: "masked",
              todayPnl: "system_report_only",
              realizedPnl: "system_report_only",
              aiJobStatus: "pro:present / flash:present",
              reportStatus: "continuous_tick:ok",
            },
            readinessTruth: {
              headline: "NOT_READY_FOR_PAPER_TRADING",
              operatorMessage: "서비스가 떠 있어도 모의매매 준비 완료가 아닙니다.",
              blockers: ["blocked_calendar_unconfigured"],
              paperNetworkEnabled: false,
              paperOrderEnabled: false,
              paperOrdersSubmitted: false,
              paperObservationAccepted: false,
              operationalTradingReadiness: false,
              orderGate: "blocked_calendar_unconfigured",
              serviceVisibilityIsNotReadiness: true,
            },
            holdings: [],
            candidates: [],
            intelligence: [],
            aiThread: [],
            auditLog: [],
          },
        })}
        initialErrorObj={{}}
      />,
    );

    expect(screen.queryByText(/sked/)).not.toBeInTheDocument();
    expect(screen.getByText("계좌 조회 미연동")).toBeInTheDocument();
    expect(screen.getAllByText("조회 미연동").length).toBeGreaterThan(0);
    expect(screen.getAllByText("손익 집계 대기").length).toBeGreaterThanOrEqual(2);
  });

  test("에러는 code/requestId만 노출하고 raw JSON 페이로드는 렌더하지 않는다", () => {
    const rawPayload = '{"account":"50123456789012","apiKey":"secret-key"}';
    render(
      <DashboardView
        initialDataObj={buildSsrInitialDataObj()}
        initialErrorObj={{
          operator: {
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
              accountId: "12345678-01",
              cashBalance: 2000000,
              reserveBalance: 500000,
              todayPnl: 0,
              realizedPnl: 0,
              aiJobStatus: "pro:present / flash:present",
              reportStatus: "continuous_tick:ok",
              paperNetworkEnabled: false,
              paperOrderEnabled: false,
              paperOrdersSubmitted: false,
            paperObservationAccepted: false,
            operationalTradingReadiness: false,
          },
          readinessTruth: {
            headline: "NOT_READY_FOR_PAPER_TRADING",
            operatorMessage: "서비스가 떠 있어도 모의매매 준비 완료가 아닙니다.",
            blockers: ["paper_network_disabled", "blocked_calendar_unconfigured"],
            paperNetworkEnabled: false,
            paperOrderEnabled: false,
            paperOrdersSubmitted: false,
            paperObservationAccepted: false,
            operationalTradingReadiness: false,
            orderGate: "blocked_calendar_unconfigured",
            serviceVisibilityIsNotReadiness: true,
          },
          holdings: [],
          auditLog: [
            { at: "18:00", level: "info", code: "ORDER_GATE", message: "blocked_calendar_unconfigured" },
          ],
        },
      });
    });

    await waitFor(() => {
      expect(screen.getByText("ORDER_GATE")).toBeInTheDocument();
    });
    expect(screen.getByTestId("operator-ai-report")).toBeInTheDocument();
    expect(screen.getByTestId("operator-ai-conversation")).toBeInTheDocument();
    expect(screen.getAllByText("시장 시간표 설정 필요").length).toBeGreaterThan(0);
    expect(screen.queryByText("blocked_calendar_unconfigured")).not.toBeInTheDocument();
  });
});
