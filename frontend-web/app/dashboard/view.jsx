"use client";

/**
 * 파일명: dashboard/view.jsx
 * 설명: hwiStock 읽기 전용 운영 콘솔 뷰
 */

import { usePageData } from "@/app/lib/hooks/usePageData";
import Badge from "@/app/lib/component/Badge";
import Card from "@/app/lib/component/Card";
import Skeleton from "@/app/lib/component/Skeleton";
import MaskedValue from "./components/MaskedValue";
import { PAGE_CONFIG } from "./initData";
import LANG_KO from "./lang.ko";
import {
  DASHBOARD_ERROR_KEYS,
  normalizeOperatorSnapshot,
  resolveErrorState,
} from "./operatorData";

/* 1. 상수 ======================================================================================================================= */
const healthVariantMap = {
  ok: "success",
  healthy: "success",
  degraded: "warning",
  down: "danger",
  off: "neutral",
  on: "danger",
  fixture: "outline",
};

/* 7. 함수 ======================================================================================================================= */
const formatSignedNumber = (value, locale = "ko-KR") => {
  const numeric = Number(String(value).replace(/[^\d.-]/g, ""));
  if (Number.isNaN(numeric)) return String(value || "—");
  const prefix = numeric > 0 ? "+" : "";
  return `${prefix}${numeric.toLocaleString(locale)}`;
};

/* 9. 내부 컴포넌트 ============================================================================================================== */
const StatusChip = ({ label, value, variant = "neutral" }) => (
  <div className="flex min-w-[120px] flex-col gap-0.5 rounded-md border border-slate-700/60 bg-slate-800/70 px-3 py-2">
    <span className="text-[10px] font-medium uppercase tracking-wide text-slate-400">{label}</span>
    <Badge variant={healthVariantMap[String(value).toLowerCase()] || variant} size="sm" pill>
      {value}
    </Badge>
  </div>
);

const SummaryRow = ({ label, children }) => (
  <div className="flex items-center justify-between gap-3 border-b border-slate-100 py-2 last:border-b-0">
    <span className="text-xs font-medium text-slate-500">{label}</span>
    <div className="text-right">{children}</div>
  </div>
);

const formatBooleanState = (value) => (value ? "true" : "false");

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
      className={`rounded-lg border px-4 py-3 shadow-sm ${
        ready
          ? "border-green-300 bg-green-50 text-green-900"
          : "border-red-300 bg-red-50 text-red-950"
      }`}
      data-testid="operator-readiness-truth"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide">
            {LANG_KO.view.readiness.title}
          </p>
          <h2 id="operator-readiness-heading" className="mt-0.5 text-base font-bold">
            {ready ? LANG_KO.view.readiness.ready : LANG_KO.view.readiness.notReady}
          </h2>
          <p className="mt-1 text-sm">
            {truth.operatorMessage || LANG_KO.view.readiness.serviceVisibilityWarning}
          </p>
        </div>
        <Badge variant={ready ? "success" : "danger"} size="md">
          {truth.headline || (ready ? "READY" : "NOT_READY_FOR_PAPER_TRADING")}
        </Badge>
      </div>
      <div className="mt-3 grid gap-2 text-xs sm:grid-cols-2 lg:grid-cols-5">
        <div><strong>{LANG_KO.view.readiness.paperNetwork}</strong>: {formatBooleanState(truth.paperNetworkEnabled)}</div>
        <div><strong>{LANG_KO.view.readiness.paperOrders}</strong>: {formatBooleanState(truth.paperOrdersSubmitted)}</div>
        <div><strong>{LANG_KO.view.readiness.observation}</strong>: {formatBooleanState(truth.paperObservationAccepted)}</div>
        <div><strong>{LANG_KO.view.readiness.operational}</strong>: {formatBooleanState(truth.operationalTradingReadiness)}</div>
        <div><strong>{LANG_KO.view.readiness.orderGate}</strong>: {truth.orderGate || "unknown"}</div>
      </div>
      {usesFallback ? (
        <p className="mt-2 text-xs font-semibold">{LANG_KO.view.readiness.fallbackWarning}</p>
      ) : null}
      {blockerList.length ? (
        <div className="mt-2 flex flex-wrap gap-1" aria-label={LANG_KO.view.readiness.blockers}>
          {blockerList.map((blocker) => (
            <Badge key={blocker} variant="danger" size="sm">{blocker}</Badge>
          ))}
        </div>
      ) : null}
    </section>
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
    <div className="space-y-3" data-testid="hwistock-operator-console">
      <header className="rounded-lg border border-slate-200 bg-gradient-to-r from-slate-900 via-slate-800 to-indigo-950 px-4 py-3 text-white shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-lg font-semibold tracking-tight">{LANG_KO.view.consoleTitle}</h1>
            <p className="mt-0.5 text-xs text-slate-300">{LANG_KO.view.consoleSubtitle}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline" size="sm">{dataSourceLabel}</Badge>
            {usesFallback ? (
              <Badge variant="warning" size="sm">폴백 데이터</Badge>
            ) : null}
          </div>
        </div>
      </header>

      {errorText ? (
        <section role="alert" aria-labelledby="operator-error-heading">
          <h2 id="operator-error-heading" className="sr-only">
            {LANG_KO.view.error.sectionAriaLabel}
          </h2>
          <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            <div>{errorText}</div>
            {errorState?.requestId ? (
              <div className="mt-1 text-xs text-red-700/80">
                {LANG_KO.view.error.requestIdLabel}: {errorState.requestId}
              </div>
            ) : null}
            {errorState?.code ? (
              <div className="mt-1 text-xs text-red-700/80">
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
        className="grid gap-2 rounded-lg border border-slate-800 bg-slate-900 p-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6"
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
          <Card title={LANG_KO.view.panes.summary} className="border-slate-200 shadow-sm">
            {loading ? (
              <Skeleton variant="text" lines={8} />
            ) : (
              <div>
                <SummaryRow label={LANG_KO.view.summary.accountId}>
                  <MaskedValue value={snapshot.summary.accountId} label={LANG_KO.view.summary.accountId} />
                </SummaryRow>
                <SummaryRow label={LANG_KO.view.summary.cash}>
                  <MaskedValue value={snapshot.summary.cashBalance} label={LANG_KO.view.summary.cash} />
                </SummaryRow>
                <SummaryRow label={LANG_KO.view.summary.reserve}>
                  <MaskedValue value={snapshot.summary.reserveBalance} label={LANG_KO.view.summary.reserve} />
                </SummaryRow>
                <SummaryRow label={LANG_KO.view.summary.todayPnl}>
                  <span className="font-mono text-sm text-slate-800">
                    {formatSignedNumber(snapshot.summary.todayPnl)}
                  </span>
                </SummaryRow>
                <SummaryRow label={LANG_KO.view.summary.openPositions}>
                  <span className="text-sm font-semibold text-slate-800">{snapshot.summary.openPositions}</span>
                </SummaryRow>
                <SummaryRow label={LANG_KO.view.summary.riskRejects}>
                  <Badge variant={snapshot.summary.riskRejects > 0 ? "warning" : "neutral"} size="sm">
                    {snapshot.summary.riskRejects}
                  </Badge>
                </SummaryRow>
                <SummaryRow label={LANG_KO.view.summary.aiJob}>
                  <span className="text-sm text-slate-700">{snapshot.summary.aiJobStatus}</span>
                </SummaryRow>
                <SummaryRow label={LANG_KO.view.summary.reports}>
                  <span className="text-xs text-slate-600">{snapshot.summary.reportStatus}</span>
                </SummaryRow>
              </div>
            )}
          </Card>
        </section>

        <section className="space-y-3 xl:col-span-5" aria-label={LANG_KO.view.panes.data} data-testid="operator-pane-data">
          <Card title={LANG_KO.view.holdings.title} data-testid="operator-holdings">
            {loading ? (
              <Skeleton variant="text" lines={6} />
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full text-left text-sm">
                  <thead className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
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
                      <tr key={`${row.symbol}-${row.name}`} className="border-b border-slate-100 last:border-0">
                        <td className="py-2 pr-3 font-mono text-xs text-slate-700">{row.symbol}</td>
                        <td className="py-2 pr-3 text-slate-800">{row.name}</td>
                        <td className="py-2 pr-3 text-slate-700">{row.qty}</td>
                        <td className="py-2 pr-3 font-mono text-xs">{formatSignedNumber(row.pnl)}</td>
                        <td className="py-2 text-slate-600">{row.weight}</td>
                      </tr>
                    )) : (
                      <tr>
                        <td colSpan={5} className="py-4 text-sm text-slate-500">
                          {LANG_KO.view.holdings.empty}
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </Card>

          <Card title={LANG_KO.view.candidates.title} data-testid="operator-candidates">
            {loading ? (
              <Skeleton variant="text" lines={4} />
            ) : (
              <ul className="space-y-2">
                {snapshot.candidates.map((item) => (
                  <li
                    key={`${item.symbol}-${item.name}`}
                    className="flex items-center justify-between rounded-md border border-slate-100 bg-slate-50 px-3 py-2"
                  >
                    <div>
                      <div className="text-sm font-medium text-slate-800">{item.name}</div>
                      <div className="font-mono text-xs text-slate-500">{item.symbol}</div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" size="sm">{item.signal}</Badge>
                      <Badge variant={item.risk === "high" ? "danger" : item.risk === "medium" ? "warning" : "success"} size="sm">
                        {item.risk}
                      </Badge>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </Card>

          <Card title={LANG_KO.view.intelligence.title} data-testid="operator-intelligence">
            {loading ? (
              <Skeleton variant="text" lines={4} />
            ) : (
              <ol className="space-y-2">
                {snapshot.intelligence.map((item, index) => (
                  <li key={`${item.at}-${index}`} className="rounded-md border border-slate-100 px-3 py-2">
                    <div className="flex items-center justify-between gap-2 text-xs text-slate-500">
                      <span>{item.at}</span>
                      <Badge variant="outline" size="sm">{item.source}</Badge>
                    </div>
                    <p className="mt-1 text-sm text-slate-800">{item.title}</p>
                  </li>
                ))}
              </ol>
            )}
          </Card>
        </section>

        <section className="space-y-3 xl:col-span-4" aria-label={LANG_KO.view.panes.review} data-testid="operator-pane-review">
          <Card title={LANG_KO.view.aiThread.title} data-testid="operator-ai-thread">
            {loading ? (
              <Skeleton variant="text" lines={6} />
            ) : (
              <div className="space-y-3">
                {snapshot.aiThread.map((message, index) => (
                  <article
                    key={`${message.at}-${index}`}
                    className="rounded-md border border-indigo-100 bg-indigo-50/40 px-3 py-3"
                  >
                    <header className="mb-2 flex items-center justify-between gap-2 border-b border-indigo-100 pb-2">
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-wide text-indigo-700">
                          {message.role === "report" ? "Report" : "Assistant"}
                        </p>
                        <h4 className="text-sm font-semibold text-slate-900">{message.subject}</h4>
                      </div>
                      <time className="text-xs text-slate-500">{message.at}</time>
                    </header>
                    <p className="text-sm leading-relaxed text-slate-700">{message.body}</p>
                  </article>
                ))}
              </div>
            )}
          </Card>

          <Card title={LANG_KO.view.audit.title} data-testid="operator-audit-log">
            {loading ? (
              <Skeleton variant="text" lines={5} />
            ) : (
              <ul className="space-y-2">
                {snapshot.auditLog.map((entry, index) => (
                  <li
                    key={`${entry.at}-${entry.code}-${index}`}
                    className="rounded-md border border-slate-100 px-3 py-2"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-xs text-slate-500">{entry.at}</span>
                      <Badge
                        variant={entry.level === "error" ? "danger" : entry.level === "warn" ? "warning" : "neutral"}
                        size="sm"
                      >
                        {entry.code}
                      </Badge>
                    </div>
                    <p className="mt-1 text-sm text-slate-700">{entry.message}</p>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </section>
      </div>
    </div>
  );
};

export default OperatorConsoleView;
