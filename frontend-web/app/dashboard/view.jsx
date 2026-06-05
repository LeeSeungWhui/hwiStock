"use client";

/**
 * 파일명: dashboard/view.jsx
 * 설명: hwiStock Lucid Command 읽기 전용 운영 콘솔 뷰
 */

import { useReducer } from "react";
import { usePageData } from "@/app/lib/hooks/usePageData";
import { apiJSON } from "@/app/lib/runtime/api";
import Badge from "@/app/lib/component/Badge";
import Card from "@/app/lib/component/Card";
import Skeleton from "@/app/lib/component/Skeleton";
import { PAGE_CONFIG } from "./initData";
import LANG_KO from "./lang.ko";
import {
  DASHBOARD_ERROR_KEYS,
  normalizeOperatorSnapshot,
  resolveErrorState,
} from "./operatorData";

/* 1. 상수 ======================================================================================================================= */
const AI_CONVERSATION_ENDPOINT = "/api/v1/hwistock/ai/conversation";

const lucidCardClass = "border-slate-700/80 bg-slate-900/90 text-slate-100 shadow-lg shadow-black/20";
const lucidCardHeaderClass = "border-slate-700/80 [&_h3]:text-slate-100 [&_p]:text-slate-400";
const lucidCardBodyClass = "text-slate-200";

const healthVariantMap = {
  ok: "success",
  healthy: "success",
  degraded: "warning",
  down: "danger",
  off: "neutral",
  on: "danger",
  fixture: "outline",
};

const readinessHeadlineLabelMap = {
  NOT_READY: "준비 전",
  NOT_READY_FOR_PAPER_TRADING: "준비 전",
  READY: "준비 완료",
};

const readinessBlockerLabelMap = {
  artifact_missing_or_safe_blocked: "운영 산출물 없음/안전 차단",
  blocked_calendar_stale: "시장 시간표 갱신 필요",
  blocked_calendar_unconfigured: "시장 시간표 설정 필요",
  blocked_kill_switch: "킬스위치 작동 중",
  blocked_source_unconfigured: "시세 데이터 소스 설정 필요",
  fallback_snapshot: "폴백 스냅샷 표시 중",
  missing_or_safe_blocked: "없음/안전 차단",
  operational_readiness_false: "운영 준비 미완료",
  operational_trading_readiness_false: "운영 준비 미완료",
  paper_network_disabled: "시세 API 연결 차단",
  paper_observation_not_accepted: "관찰 승인 필요",
  paper_orders_not_submitted: "주문 제출 대기",
  systemd_order_enabled_contradicts_readiness: "서비스 주문 설정과 준비 상태 불일치",
  unknown: "상태 확인 필요",
};

const summaryPlaceholderLabelMap = {
  "account_alias:masked": "계좌 조회 미연동",
  "paper_account_alias:masked": "계좌 조회 미연동",
  masked: "조회 미연동",
  system_report_only: "손익 집계 대기",
};

const statusValueLabelMap = {
  paper_sandbox: "운영 관찰",
  paper: "운영 관찰",
  sandbox: "운영 관찰",
  mock: "운영 관찰",
  not_loaded: "미수신",
  observable: "관찰 가능",
  unknown: "확인 필요",
};

const aiJobLabelMap = {
  present: "있음",
  missing: "없음",
  missing_or_safe_blocked: "대기/안전 차단",
};

const reportStatusLabelMap = {
  ok: "정상",
  pass: "정상",
  warn: "주의",
  fail: "오류",
  missing: "리포트 없음",
  missing_or_safe_blocked: "리포트 없음/안전 차단",
  operator_window_required: "운영자 확인 필요",
  safe_block_paper_read_network_disabled: "시세 API 연결 차단",
};

/* 7. 함수 ======================================================================================================================= */
const formatSignedNumber = (value, locale = "ko-KR") => {
  const numeric = Number(String(value).replace(/[^\d.-]/g, ""));
  if (Number.isNaN(numeric)) return String(value || "—");
  const prefix = numeric > 0 ? "+" : "";
  return `${prefix}${numeric.toLocaleString(locale)}`;
};

const normalizeToken = (value) => String(value ?? "").trim();

const normalizedSummaryText = (value, defaultText = "—") => {
  const token = normalizeToken(value);
  return summaryPlaceholderLabelMap[token] || token || defaultText;
};

const formatKrwValue = (value, { signed = false } = {}) => {
  const placeholder = summaryPlaceholderLabelMap[normalizeToken(value)];
  if (placeholder) return placeholder;
  const numeric = Number(String(value).replace(/[^\d.-]/g, ""));
  if (Number.isNaN(numeric)) return normalizedSummaryText(value);
  const prefix = signed && numeric > 0 ? "+" : "";
  return `${prefix}${numeric.toLocaleString("ko-KR")}원`;
};

const humanizeStatusToken = (value) => {
  const token = normalizeToken(value);
  return readinessBlockerLabelMap[token]
    || reportStatusLabelMap[token]
    || aiJobLabelMap[token]
    || statusValueLabelMap[token]
    || token
    || "—";
};

const formatHeadline = (value, ready) => (
  readinessHeadlineLabelMap[normalizeToken(value)] || (ready ? "준비 완료" : "준비 전")
);

const formatReadinessState = (key, value) => {
  const on = Boolean(value);
  const labelByKey = {
    paperNetworkEnabled: ["연결 차단", "연결 허용"],
    paperOrderEnabled: ["주문 차단", "주문 허용"],
    paperOrdersSubmitted: ["제출 대기", "제출 완료"],
    paperObservationAccepted: ["미승인", "승인됨"],
    operationalTradingReadiness: ["준비 전", "준비 완료"],
  };
  const pair = labelByKey[key] || ["아니오", "예"];
  return pair[on ? 1 : 0];
};

const formatAiJobStatus = (value) => {
  const text = normalizeToken(value);
  if (!text) return "AI 산출물 없음";
  return text
    .split("/")
    .map((part) => part.trim())
    .filter(Boolean)
    .map((part) => {
      const [rawName, rawStatus] = part.split(":").map((item) => item.trim());
      const nameMap = { pro: "Pro 분석", flash: "Flash 문서" };
      const name = nameMap[rawName] || rawName || "AI 작업";
      const status = aiJobLabelMap[rawStatus] || humanizeStatusToken(rawStatus);
      return `${name} ${status}`;
    })
    .join(" · ");
};

const formatReportStatus = (value) => {
  const text = normalizeToken(value);
  if (!text) return "리포트 없음";
  if (text.startsWith("continuous_tick:")) {
    return `자동 점검: ${humanizeStatusToken(text.slice("continuous_tick:".length))}`;
  }
  return humanizeStatusToken(text);
};

const formatAuditMessage = (value) => {
  const text = normalizeToken(value);
  if (!text) return "—";
  if (text === "dashboard exposes no order controls") {
    return "대시보드는 주문 실행 버튼을 노출하지 않음";
  }
  if (text === "enabled") return "활성";
  if (text === "disabled") return "비활성";
  if (text.includes(",")) {
    return text
      .split(",")
      .map((item) => humanizeStatusToken(item))
      .join(" · ");
  }
  return humanizeStatusToken(text);
};

const formatOperatorMessage = (value) => {
  const text = normalizeToken(value);
  if (!text) return LANG_KO.view.readiness.serviceVisibilityWarning;
  if (text.includes("모의매매")) {
    return "서비스/타이머/대시보드가 보여도 자동매매 준비 완료가 아닙니다. 시세 API 연결, 주문 제출, 관찰 승인, 시장 시간표를 모두 확인해야 합니다.";
  }
  if (text.includes("paper network") || text.includes("order submission")) {
    return "서비스/타이머/대시보드가 보여도 자동매매 준비 완료가 아닙니다. 시세 API 연결, 주문 제출, 관찰 승인, 시장 시간표를 모두 확인해야 합니다.";
  }
  return text;
};

const initialConversationState = {
  question: "",
  thread: [],
  pending: false,
  panelError: null,
};

const conversationReducer = (state, action) => {
  if (action.type === "question_changed") {
    return { ...state, question: action.value };
  }
  if (action.type === "submit_started") {
    return {
      ...state,
      question: "",
      pending: true,
      panelError: null,
      thread: [...state.thread, action.userTurn],
    };
  }
  if (action.type === "submit_succeeded") {
    return {
      ...state,
      pending: false,
      thread: [...state.thread, action.assistantTurn],
    };
  }
  if (action.type === "submit_failed") {
    return {
      ...state,
      pending: false,
      panelError: LANG_KO.view.aiConversation.unavailable,
      thread: [...state.thread, action.assistantTurn],
    };
  }
  return state;
};

/* 9. 내부 컴포넌트 ============================================================================================================== */
const StatusChip = ({ label, value, variant = "neutral" }) => (
  <div className="flex min-w-[120px] flex-col gap-0.5 rounded-md border border-slate-600/70 bg-slate-800/80 px-3 py-2">
    <span className="text-[10px] font-medium uppercase tracking-wide text-slate-400">{label}</span>
    <Badge variant={healthVariantMap[String(value).toLowerCase()] || variant} size="sm" pill>
      {humanizeStatusToken(value)}
    </Badge>
  </div>
);

const SummaryRow = ({ label, children }) => (
  <div className="flex items-center justify-between gap-3 border-b border-slate-700/60 py-2 last:border-b-0">
    <span className="text-xs font-medium text-slate-400">{label}</span>
    <div className="text-right text-slate-100">{children}</div>
  </div>
);

const SectionNavPill = ({ label, active = false, href }) => {
  const baseClass = "rounded-full border px-3 py-1 text-xs font-medium transition-colors";
  const activeClass = active
    ? "border-cyan-500/60 bg-cyan-950/50 text-cyan-200"
    : "border-slate-600/70 bg-slate-800/60 text-slate-300 hover:border-slate-500 hover:text-slate-100";
  if (href) {
    return (
      <a href={href} className={`${baseClass} ${activeClass}`}>
        {label}
      </a>
    );
  }
  return <span className={`${baseClass} ${activeClass}`}>{label}</span>;
};

const ReadinessTruthBanner = ({ readinessTruth, usesFallback }) => {
  const truth = readinessTruth || {};
  const ready = truth.operationalTradingReadiness
    && truth.paperNetworkEnabled
    && truth.paperOrdersSubmitted
    && truth.paperObservationAccepted
    && !usesFallback;
  const blockerList = Array.isArray(truth.blockers) ? truth.blockers : [];
  return (
    <section
      role="alert"
      aria-labelledby="operator-readiness-heading"
      className={`rounded-lg border px-4 py-3 shadow-md ${
        ready
          ? "border-emerald-600/50 bg-emerald-950/40 text-emerald-100"
          : "border-rose-600/50 bg-rose-950/40 text-rose-50"
      }`}
      data-testid="operator-readiness-truth"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide opacity-80">
            {LANG_KO.view.readiness.title}
          </p>
          <h2 id="operator-readiness-heading" className="mt-0.5 text-base font-bold">
            {ready ? LANG_KO.view.readiness.ready : LANG_KO.view.readiness.notReady}
          </h2>
          <p className="mt-1 text-sm opacity-90">
            {formatOperatorMessage(truth.operatorMessage)}
          </p>
        </div>
        <Badge variant={ready ? "success" : "danger"} size="md">
          {formatHeadline(truth.headline, ready)}
        </Badge>
      </div>
      <div className="mt-3 grid gap-2 text-xs opacity-90 sm:grid-cols-2 lg:grid-cols-6">
        <div><strong>{LANG_KO.view.readiness.paperNetwork}</strong>: {formatReadinessState("paperNetworkEnabled", truth.paperNetworkEnabled)}</div>
        <div><strong>{LANG_KO.view.readiness.paperOrderEnabled}</strong>: {formatReadinessState("paperOrderEnabled", truth.paperOrderEnabled)}</div>
        <div><strong>{LANG_KO.view.readiness.paperOrders}</strong>: {formatReadinessState("paperOrdersSubmitted", truth.paperOrdersSubmitted)}</div>
        <div><strong>{LANG_KO.view.readiness.observation}</strong>: {formatReadinessState("paperObservationAccepted", truth.paperObservationAccepted)}</div>
        <div><strong>{LANG_KO.view.readiness.operational}</strong>: {formatReadinessState("operationalTradingReadiness", truth.operationalTradingReadiness)}</div>
        <div><strong>{LANG_KO.view.readiness.orderGate}</strong>: {humanizeStatusToken(truth.orderGate || "unknown")}</div>
      </div>
      {usesFallback ? (
        <p className="mt-2 text-xs font-semibold text-amber-200">{LANG_KO.view.readiness.fallbackWarning}</p>
      ) : null}
      {blockerList.length ? (
        <div className="mt-2 flex flex-wrap gap-1" aria-label={LANG_KO.view.readiness.blockers}>
          {blockerList.map((blocker) => (
            <Badge key={blocker} variant="danger" size="sm" title={blocker}>
              {humanizeStatusToken(blocker)}
            </Badge>
          ))}
        </div>
      ) : null}
    </section>
  );
};

const AiReportViewer = ({ messages = [], loading }) => (
  <Card
    title={LANG_KO.view.aiReport.title}
    subtitle={LANG_KO.view.aiReport.subtitle}
    className={lucidCardClass}
    headerClassName={lucidCardHeaderClass}
    bodyClassName={lucidCardBodyClass}
    data-testid="operator-ai-report"
  >
    {loading ? (
      <Skeleton variant="text" lines={6} />
    ) : (
      <div className="space-y-3">
        {messages.length ? messages.map((message, index) => (
          <article
            key={`${message.at}-${index}`}
            className="rounded-md border border-slate-600/60 bg-slate-800/50 px-3 py-3"
          >
            <header className="mb-2 flex items-center justify-between gap-2 border-b border-slate-600/50 pb-2">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-cyan-400/90">
                  {message.role === "report"
                    ? LANG_KO.view.aiReport.roleReport
                    : LANG_KO.view.aiReport.roleAssistant}
                </p>
                <h4 className="text-sm font-semibold text-slate-100">{message.subject}</h4>
              </div>
              <time className="text-xs text-slate-400">{message.at}</time>
            </header>
            <p className="text-sm leading-relaxed text-slate-300">{message.body}</p>
          </article>
        )) : (
          <div className="rounded-md border border-slate-700/60 px-3 py-4 text-sm text-slate-400">
            {LANG_KO.view.aiReport.empty}
          </div>
        )}
      </div>
    )}
  </Card>
);

const AiConversationPanel = ({ loading: pageLoading }) => {
  const [{ question, thread, pending, panelError }, dispatchConversation] = useReducer(
    conversationReducer,
    initialConversationState,
  );

  const handleSubmit = async (event) => {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || pending) return;

    const userTurn = {
      role: "user",
      body: trimmed,
      at: new Date().toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" }),
    };
    dispatchConversation({ type: "submit_started", userTurn });

    try {
      const response = await apiJSON(AI_CONVERSATION_ENDPOINT, {
        method: "POST",
        body: { question: trimmed },
      });
      const answerText = response?.result?.answer
        || response?.answer
        || response?.result?.refusal
        || response?.refusal;
      const refused = Boolean(response?.result?.refused || response?.refused);
      dispatchConversation({
        type: "submit_succeeded",
        assistantTurn: {
          role: "assistant",
          body: answerText || LANG_KO.view.aiConversation.unavailable,
          refused,
          at: new Date().toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" }),
          requestId: response?.result?.requestId || response?.requestId,
        },
      });
    } catch {
      dispatchConversation({
        type: "submit_failed",
        assistantTurn: {
          role: "assistant",
          body: LANG_KO.view.aiConversation.unavailable,
          refused: true,
          at: new Date().toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" }),
        },
      });
    }
  };

  return (
    <Card
      title={LANG_KO.view.aiConversation.title}
      subtitle={LANG_KO.view.aiConversation.subtitle}
      className={lucidCardClass}
      headerClassName={lucidCardHeaderClass}
      bodyClassName={lucidCardBodyClass}
      data-testid="operator-ai-conversation"
    >
      {pageLoading ? (
        <Skeleton variant="text" lines={5} />
      ) : (
        <div className="space-y-3">
          <p
            className="rounded-md border border-amber-600/30 bg-amber-950/30 px-3 py-2 text-xs leading-relaxed text-amber-100/90"
            data-testid="operator-ai-conversation-disclaimer"
          >
            {LANG_KO.view.aiConversation.disclaimer}
          </p>

          <div className="max-h-56 space-y-2 overflow-y-auto rounded-md border border-slate-700/60 bg-slate-950/40 p-2">
            {thread.length ? thread.map((turn, index) => (
              <article
                key={`conversation-turn-${index}`}
                className={`rounded-md px-3 py-2 text-sm ${
                  turn.role === "user"
                    ? "border border-slate-600/50 bg-slate-800/60 text-slate-200"
                    : turn.refused
                      ? "border border-rose-700/40 bg-rose-950/30 text-rose-100"
                      : "border border-cyan-800/40 bg-cyan-950/20 text-cyan-50"
                }`}
              >
                <div className="mb-1 flex items-center justify-between gap-2 text-[10px] uppercase tracking-wide text-slate-400">
                  <span>{turn.role === "user" ? "운영자" : "AI 설명"}</span>
                  <time>{turn.at}</time>
                </div>
                {turn.refused ? (
                  <p>
                    <span className="font-medium text-rose-200">{LANG_KO.view.aiConversation.refusedPrefix}: </span>
                    {turn.body}
                  </p>
                ) : (
                  <p className="leading-relaxed">{turn.body}</p>
                )}
                {turn.requestId ? (
                  <p className="mt-1 text-[10px] text-slate-500">requestId: {turn.requestId}</p>
                ) : null}
              </article>
            )) : (
              <p className="px-2 py-3 text-sm text-slate-400">{LANG_KO.view.aiConversation.empty}</p>
            )}
            {pending ? (
              <p className="px-2 text-xs text-slate-400">{LANG_KO.view.aiConversation.pending}</p>
            ) : null}
          </div>

          <form onSubmit={handleSubmit} className="space-y-2">
            <label htmlFor="operator-ai-question" className="text-xs font-medium text-slate-400">
              {LANG_KO.view.aiConversation.inputLabel}
            </label>
            <textarea
              id="operator-ai-question"
              data-testid="operator-ai-question-input"
              value={question}
              onChange={(event) => dispatchConversation({
                type: "question_changed",
                value: event.target.value,
              })}
              placeholder={LANG_KO.view.aiConversation.inputPlaceholder}
              rows={2}
              className="w-full resize-none rounded-md border border-slate-600/70 bg-slate-950/60 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:border-cyan-600/60 focus:outline-none focus:ring-1 focus:ring-cyan-600/40"
            />
            <div className="flex justify-end">
              <button
                type="submit"
                data-testid="operator-ai-question-submit"
                disabled={pending || !question.trim()}
                className="rounded-md border border-slate-500/70 bg-slate-800/80 px-3 py-1.5 text-xs font-medium text-slate-200 transition-colors hover:border-slate-400 hover:bg-slate-700/80 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {LANG_KO.view.aiConversation.submitLabel}
              </button>
            </div>
          </form>

          {panelError ? (
            <p className="text-xs text-amber-300/90">{panelError}</p>
          ) : null}
        </div>
      )}
    </Card>
  );
};

const OperatorConsoleView = ({
  initialDataObj = {},
  initialErrorObj = {},
}) => {

  /* 2. 데이터 ======================================================================================================================= */
  const endpoints = PAGE_CONFIG.API || {};
  const hasEndpoint = Boolean(endpoints.operator || (endpoints.stats && endpoints.list));

  const { dataObj, errorObj, isLoading } = usePageData({
    pageConfig: PAGE_CONFIG,
    initialDataObj,
    initialErrorObj,
  });

  const errorState = resolveErrorState({
    hasEndpoint,
    initialErrorObj,
    errorObj,
  });

  const pageModeText = String(PAGE_CONFIG.MODE || "").toUpperCase();
  const hasLoadedSnapshot =
    Object.prototype.hasOwnProperty.call(dataObj || {}, "operator")
    || Object.prototype.hasOwnProperty.call(dataObj || {}, "stats")
    || Object.prototype.hasOwnProperty.call(dataObj || {}, "list")
    || Boolean(errorObj?.operator || errorObj?.stats || errorObj?.list);
  const shouldForceCsrLoading =
    pageModeText === "CSR"
    && !isLoading
    && !errorState
    && !hasLoadedSnapshot;

  const loading = isLoading || shouldForceCsrLoading;
  const { snapshot, dataSource, usesFallback } = normalizeOperatorSnapshot({
    dataObj,
    hasEndpoint,
  });

  /* 3. UI ========================================================================================================================= */
  let errorText = null;
  if (errorState?.key === DASHBOARD_ERROR_KEYS.ENDPOINT_MISSING) {
    errorText = LANG_KO.view.error.endpointMissing;
  } else if (errorState?.key === DASHBOARD_ERROR_KEYS.INIT_FETCH_FAILED) {
    errorText = LANG_KO.view.error.fetchFailed;
  }

  const dataSourceLabel = LANG_KO.view.dataSource[dataSource] || LANG_KO.view.dataSource.fixture;

  /* 4. 팝업 ======================================================================================================================= */

  // 없음

  /* 5. 기타 ======================================================================================================================= */

  // 없음

  /* 6. 커스텀 훅 =================================================================================================================== */

  // 없음

  /* 8. useEffect ================================================================================================================== */

  // 없음

  /* 10. 렌더링 ==================================================================================================================== */
  return (
    <div className="space-y-3 rounded-xl bg-slate-950 p-3 text-slate-100" data-testid="hwistock-operator-console">
      <header className="rounded-lg border border-slate-700/80 bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 px-4 py-3 shadow-md">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-lg font-semibold tracking-tight text-slate-50">{LANG_KO.view.consoleTitle}</h1>
            <p className="mt-0.5 text-xs text-slate-400">{LANG_KO.view.consoleSubtitle}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline" size="sm">{dataSourceLabel}</Badge>
            {usesFallback ? (
              <Badge variant="warning" size="sm">폴백 데이터</Badge>
            ) : null}
          </div>
        </div>
        <nav
          aria-label="대시보드 섹션"
          className="mt-3 flex flex-wrap gap-2"
          data-testid="operator-section-nav"
        >
          <SectionNavPill label={LANG_KO.view.sectionNav.console} active />
          <SectionNavPill label={LANG_KO.view.sectionNav.aiReport} href="#operator-ai-report" />
          <SectionNavPill label={LANG_KO.view.sectionNav.aiConversation} href="#operator-ai-conversation" />
        </nav>
      </header>

      {errorText ? (
        <section role="alert" aria-labelledby="operator-error-heading">
          <h2 id="operator-error-heading" className="sr-only">
            {LANG_KO.view.error.sectionAriaLabel}
          </h2>
          <div className="rounded-md border border-rose-700/50 bg-rose-950/40 px-4 py-3 text-sm text-rose-100">
            <div>{errorText}</div>
            {errorState?.requestId ? (
              <div className="mt-1 text-xs text-rose-200/80">
                {LANG_KO.view.error.requestIdLabel}: {errorState.requestId}
              </div>
            ) : null}
            {errorState?.code ? (
              <div className="mt-1 text-xs text-rose-200/80">
                {LANG_KO.view.error.codeLabel}: {errorState.code}
              </div>
            ) : null}
          </div>
        </section>
      ) : null}

      {!loading ? (
        <ReadinessTruthBanner
          readinessTruth={snapshot.readinessTruth}
          usesFallback={usesFallback}
        />
      ) : null}

      <section
        aria-label={LANG_KO.view.statusStrip.ariaLabel}
        className="grid gap-2 rounded-lg border border-slate-700/80 bg-slate-900/80 p-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6"
        data-testid="operator-status-strip"
      >
        {loading ? (
          Array.from({ length: 6 }).map((_, index) => (
            <Skeleton key={`status-skeleton-${index}`} className="h-14 rounded-md" />
          ))
        ) : (
          <>
            <StatusChip label={LANG_KO.view.statusStrip.mode} value={snapshot.status.mode} />
            <StatusChip label={LANG_KO.view.statusStrip.session} value={snapshot.status.sessionKst} variant="primary" />
            <StatusChip label={LANG_KO.view.statusStrip.venue} value={snapshot.status.venueRoute} variant="outline" />
            <StatusChip label={LANG_KO.view.statusStrip.killSwitch} value={snapshot.status.killSwitch} />
            <StatusChip label={LANG_KO.view.statusStrip.serviceHealth} value={snapshot.status.serviceHealth} />
            <StatusChip label={LANG_KO.view.statusStrip.dataHealth} value={snapshot.status.dataSourceHealth} />
          </>
        )}
      </section>

      <div className="grid gap-3 xl:grid-cols-12">
        <section className="space-y-3 xl:col-span-3" aria-label={LANG_KO.view.panes.summary} data-testid="operator-pane-summary">
          <Card
            title={LANG_KO.view.panes.summary}
            className={lucidCardClass}
            headerClassName={lucidCardHeaderClass}
            bodyClassName={lucidCardBodyClass}
          >
            {loading ? (
              <Skeleton variant="text" lines={8} />
            ) : (
              <div>
                <SummaryRow label={LANG_KO.view.summary.accountId}>
                  <span className="font-mono text-sm font-semibold">
                    {normalizedSummaryText(snapshot.summary.accountId)}
                  </span>
                </SummaryRow>
                <SummaryRow label={LANG_KO.view.summary.cash}>
                  <span className="font-mono text-sm font-semibold">
                    {formatKrwValue(snapshot.summary.cashBalance)}
                  </span>
                </SummaryRow>
                <SummaryRow label={LANG_KO.view.summary.reserve}>
                  <span className="font-mono text-sm font-semibold">
                    {formatKrwValue(snapshot.summary.reserveBalance)}
                  </span>
                </SummaryRow>
                <SummaryRow label={LANG_KO.view.summary.todayPnl}>
                  <span className="font-mono text-sm font-semibold">
                    {formatKrwValue(snapshot.summary.todayPnl, { signed: true })}
                  </span>
                </SummaryRow>
                <SummaryRow label={LANG_KO.view.summary.realizedPnl}>
                  <span className="font-mono text-sm font-semibold">
                    {formatKrwValue(snapshot.summary.realizedPnl, { signed: true })}
                  </span>
                </SummaryRow>
                <SummaryRow label={LANG_KO.view.summary.openPositions}>
                  <span className="text-sm font-semibold">{snapshot.summary.openPositions}</span>
                </SummaryRow>
                <SummaryRow label={LANG_KO.view.summary.riskRejects}>
                  <Badge variant={snapshot.summary.riskRejects > 0 ? "warning" : "neutral"} size="sm">
                    {snapshot.summary.riskRejects}
                  </Badge>
                </SummaryRow>
                <SummaryRow label={LANG_KO.view.summary.aiJob}>
                  <span className="text-sm text-slate-300">{formatAiJobStatus(snapshot.summary.aiJobStatus)}</span>
                </SummaryRow>
                <SummaryRow label={LANG_KO.view.summary.reports}>
                  <span className="text-xs text-slate-400">{formatReportStatus(snapshot.summary.reportStatus)}</span>
                </SummaryRow>
              </div>
            )}
          </Card>
        </section>

        <section className="space-y-3 xl:col-span-5" aria-label={LANG_KO.view.panes.data} data-testid="operator-pane-data">
          <Card
            title={LANG_KO.view.holdings.title}
            data-testid="operator-holdings"
            className={lucidCardClass}
            headerClassName={lucidCardHeaderClass}
            bodyClassName={lucidCardBodyClass}
          >
            {loading ? (
              <Skeleton variant="text" lines={6} />
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full text-left text-sm">
                  <thead className="border-b border-slate-600/70 text-xs uppercase tracking-wide text-slate-400">
                    <tr>
                      <th className="py-2 pr-3">{LANG_KO.view.holdings.columns.symbol}</th>
                      <th className="py-2 pr-3">{LANG_KO.view.holdings.columns.name}</th>
                      <th className="py-2 pr-3">{LANG_KO.view.holdings.columns.qty}</th>
                      <th className="py-2 pr-3">{LANG_KO.view.holdings.columns.pnl}</th>
                      <th className="py-2">{LANG_KO.view.holdings.columns.weight}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {snapshot.holdings.length ? snapshot.holdings.map((row) => (
                      <tr key={`${row.symbol}-${row.name}`} className="border-b border-slate-700/50 last:border-0">
                        <td className="py-2 pr-3 font-mono text-xs text-slate-300">{row.symbol}</td>
                        <td className="py-2 pr-3 text-slate-100">{row.name}</td>
                        <td className="py-2 pr-3 text-slate-300">{row.qty}</td>
                        <td className="py-2 pr-3 font-mono text-xs text-slate-200">{formatSignedNumber(row.pnl)}</td>
                        <td className="py-2 text-slate-400">{row.weight}</td>
                      </tr>
                    )) : (
                      <tr>
                        <td colSpan={5} className="py-4 text-sm text-slate-400">
                          {LANG_KO.view.holdings.empty}
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </Card>

          <Card
            title={LANG_KO.view.candidates.title}
            data-testid="operator-candidates"
            className={lucidCardClass}
            headerClassName={lucidCardHeaderClass}
            bodyClassName={lucidCardBodyClass}
          >
            {loading ? (
              <Skeleton variant="text" lines={4} />
            ) : (
              <ul className="space-y-2">
                {snapshot.candidates.length ? snapshot.candidates.map((item) => (
                  <li
                    key={`${item.symbol}-${item.name}`}
                    className="flex items-center justify-between rounded-md border border-slate-700/60 bg-slate-800/40 px-3 py-2"
                  >
                    <div>
                      <div className="text-sm font-medium text-slate-100">{item.name}</div>
                      <div className="font-mono text-xs text-slate-400">{item.symbol}</div>
                      {item.reason ? (
                        <div className="mt-1 text-xs text-slate-400">{item.reason}</div>
                      ) : null}
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" size="sm">{item.signal}</Badge>
                      <Badge variant={item.risk === "high" ? "danger" : item.risk === "medium" ? "warning" : "success"} size="sm">
                        {item.risk}
                      </Badge>
                    </div>
                  </li>
                )) : (
                  <li className="rounded-md border border-slate-700/60 px-3 py-4 text-sm text-slate-400">
                    {LANG_KO.view.candidates.empty}
                  </li>
                )}
              </ul>
            )}
          </Card>

          <Card
            title={LANG_KO.view.intelligence.title}
            data-testid="operator-intelligence"
            className={lucidCardClass}
            headerClassName={lucidCardHeaderClass}
            bodyClassName={lucidCardBodyClass}
          >
            {loading ? (
              <Skeleton variant="text" lines={4} />
            ) : (
              <ol className="space-y-2">
                {snapshot.intelligence.length ? snapshot.intelligence.map((item, index) => (
                  <li key={`${item.at}-${index}`} className="rounded-md border border-slate-700/60 bg-slate-800/40 px-3 py-2">
                    <div className="flex items-center justify-between gap-2 text-xs text-slate-400">
                      <span>{item.at}</span>
                      <Badge variant="outline" size="sm">{item.source}</Badge>
                    </div>
                    <p className="mt-1 text-sm text-slate-200">{item.title}</p>
                  </li>
                )) : (
                  <li className="rounded-md border border-slate-700/60 px-3 py-4 text-sm text-slate-400">
                    {LANG_KO.view.intelligence.empty}
                  </li>
                )}
              </ol>
            )}
          </Card>
        </section>

        <section className="space-y-3 xl:col-span-4" aria-label={LANG_KO.view.panes.review} data-testid="operator-pane-review">
          <div id="operator-ai-report">
            <AiReportViewer messages={snapshot.aiThread} loading={loading} />
          </div>

          <div id="operator-ai-conversation">
            <AiConversationPanel loading={loading} />
          </div>

          <Card
            title={LANG_KO.view.audit.title}
            data-testid="operator-audit-log"
            className={lucidCardClass}
            headerClassName={lucidCardHeaderClass}
            bodyClassName={lucidCardBodyClass}
          >
            {loading ? (
              <Skeleton variant="text" lines={5} />
            ) : (
              <ul className="space-y-2">
                {snapshot.auditLog.length ? snapshot.auditLog.map((entry, index) => (
                  <li
                    key={`${entry.at}-${entry.code}-${index}`}
                    className="rounded-md border border-slate-700/60 bg-slate-800/40 px-3 py-2"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-xs text-slate-400">{entry.at}</span>
                      <Badge
                        variant={entry.level === "error" ? "danger" : entry.level === "warn" ? "warning" : "neutral"}
                        size="sm"
                      >
                        {entry.code}
                      </Badge>
                    </div>
                    <p className="mt-1 text-sm text-slate-300" title={entry.message}>
                      {formatAuditMessage(entry.message)}
                    </p>
                  </li>
                )) : (
                  <li className="rounded-md border border-slate-700/60 px-3 py-4 text-sm text-slate-400">
                    {LANG_KO.view.audit.empty}
                  </li>
                )}
              </ul>
            )}
          </Card>
        </section>
      </div>
    </div>
  );
};

export default OperatorConsoleView;
