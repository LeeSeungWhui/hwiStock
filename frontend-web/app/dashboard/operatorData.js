/**
 * 파일명: dashboard/operatorData.js
 * 설명: pageData 응답을 운영 콘솔 스냅샷으로 정규화·폴백
 */

const DASHBOARD_ERROR_KEYS = {
  ENDPOINT_MISSING: "ENDPOINT_MISSING",
  INIT_FETCH_FAILED: "INIT_FETCH_FAILED",
};

export const OPERATOR_FALLBACK_FIXTURE = {
  status: {
    mode: "paper",
    sessionKst: "장중 · KST 09:12",
    venueRoute: "KRX · domestic",
    killSwitch: "off",
    serviceHealth: "degraded",
    dataSourceHealth: "fixture",
  },
  summary: {
    cashBalance: "masked",
    reserveBalance: "masked",
    todayPnl: "system_report_only",
    openPositions: 0,
    riskRejects: 0,
    aiJobStatus: "missing_or_safe_blocked",
    reportStatus: "operator_window_required",
    accountId: "paper_account_alias:masked",
    operationalTradingReadiness: false,
  },
  holdings: [],
  candidates: [],
  intelligence: [
    { at: "09:05", source: "disclosure", title: "실적 공시 요약 반영" },
    { at: "08:42", source: "news", title: "반도체 수급 이슈 모니터링" },
  ],
  aiThread: [
    {
      at: "07:02",
      role: "report",
      subject: "장전 브리핑",
      body: "분석/매매문서 artifact는 주문 실행 UI가 아니며, 실행 전 deterministic risk gate를 통과해야 합니다.",
    },
    {
      at: "08:55",
      role: "assistant",
      subject: "상태 질의",
      body: "운영 콘솔은 읽기 전용입니다. 매수/매도/라이브 전환 버튼은 제공하지 않습니다.",
    },
  ],
  auditLog: [
    { at: "09:01", level: "info", code: "INGEST_OK", message: "시장 데이터 수집 정상" },
    { at: "08:58", level: "warn", code: "RISK_REJECT", message: "포지션 한도 초과로 후보 제외" },
  ],
};

const hasOperatorApiShape = (dataObj) => {
  const operator = dataObj?.operator?.result;
  return Boolean(operator && typeof operator === "object");
};

const toPlainRecord = (value) => {
  if (value && typeof value.toJSON === "function") {
    return value.toJSON();
  }
  return value || {};
};

const mapLegacyStatsToSummary = (statList = []) => {
  const totalAmount = statList.reduce(
    (sum, row) => sum + Number(row.amountSum ?? 0),
    0,
  );
  const activeCount = statList
    .filter((row) => row.status === "running" || row.status === "pending")
    .reduce((sum, row) => sum + Number(row.count ?? 0), 0);
  return {
    cashBalance: String(totalAmount || OPERATOR_FALLBACK_FIXTURE.summary.cashBalance),
    reserveBalance: OPERATOR_FALLBACK_FIXTURE.summary.reserveBalance,
    todayPnl: OPERATOR_FALLBACK_FIXTURE.summary.todayPnl,
    openPositions: activeCount || OPERATOR_FALLBACK_FIXTURE.summary.openPositions,
    riskRejects: OPERATOR_FALLBACK_FIXTURE.summary.riskRejects,
    aiJobStatus: "synced",
    reportStatus: OPERATOR_FALLBACK_FIXTURE.summary.reportStatus,
    accountId: OPERATOR_FALLBACK_FIXTURE.summary.accountId,
  };
};

const mapLegacyListToHoldings = (dataList = []) => {
  if (!dataList.length) return OPERATOR_FALLBACK_FIXTURE.holdings;
  return dataList.slice(0, 6).map((row, index) => ({
    symbol: String(row.id || `SYM${index + 1}`).padStart(6, "0").slice(-6),
    name: row.title || `종목 ${index + 1}`,
    qty: Number(row.amount || 0) % 1000 || 10,
    pnl: row.status === "failed" ? "-1200" : "2400",
    weight: `${(8 + index * 2).toFixed(1)}%`,
  }));
};

export const resolveErrorState = ({
  hasEndpoint,
  initialErrorObj = {},
  errorObj = {},
}) => {
  if (!hasEndpoint) {
    return { key: DASHBOARD_ERROR_KEYS.ENDPOINT_MISSING };
  }

  const pickError = (bucket) => {
    if (!bucket) return null;
    if (typeof bucket === "string") {
      return { key: bucket };
    }
    if (typeof bucket === "object") {
      const candidateKey = String(bucket.key || bucket.message || "").toUpperCase();
      const key = candidateKey === DASHBOARD_ERROR_KEYS.ENDPOINT_MISSING
        ? DASHBOARD_ERROR_KEYS.ENDPOINT_MISSING
        : DASHBOARD_ERROR_KEYS.INIT_FETCH_FAILED;
      return {
        key,
        code: bucket.code,
        requestId: bucket.requestId,
      };
    }
    return { key: DASHBOARD_ERROR_KEYS.INIT_FETCH_FAILED };
  };

  const currentErrorObj = toPlainRecord(errorObj);
  const initialErrorRecord = toPlainRecord(initialErrorObj);

  return (
    pickError(currentErrorObj.operator)
    || pickError(currentErrorObj.stats)
    || pickError(currentErrorObj.list)
    || pickError(initialErrorRecord.operator)
    || pickError(initialErrorRecord.stats)
    || pickError(initialErrorRecord.list)
    || null
  );
};

/**
 * @description API/SSR 데이터를 운영 콘솔 스냅샷으로 정규화
 */
export const normalizeOperatorSnapshot = ({
  dataObj = {},
  hasEndpoint = true,
}) => {
  if (!hasEndpoint) {
    return {
      snapshot: OPERATOR_FALLBACK_FIXTURE,
      dataSource: "fixture",
      usesFallback: true,
    };
  }

  const sourceDataObj = toPlainRecord(dataObj);

  if (hasOperatorApiShape(sourceDataObj)) {
    const operatorResult = sourceDataObj.operator.result;
    return {
      snapshot: {
        status: { ...OPERATOR_FALLBACK_FIXTURE.status, ...operatorResult.status },
        summary: { ...OPERATOR_FALLBACK_FIXTURE.summary, ...operatorResult.summary },
        holdings: operatorResult.holdings || OPERATOR_FALLBACK_FIXTURE.holdings,
        candidates: operatorResult.candidates || OPERATOR_FALLBACK_FIXTURE.candidates,
        intelligence: operatorResult.intelligence || OPERATOR_FALLBACK_FIXTURE.intelligence,
        aiThread: operatorResult.aiThread || OPERATOR_FALLBACK_FIXTURE.aiThread,
        auditLog: operatorResult.auditLog || OPERATOR_FALLBACK_FIXTURE.auditLog,
      },
      dataSource: "api",
      usesFallback: false,
    };
  }

  const statList = sourceDataObj?.stats?.result?.statusSummaryList || [];
  const dataList = sourceDataObj?.list?.result?.dataTemplateList || [];
  const hasLegacyPayload = statList.length > 0 || dataList.length > 0;

  if (!hasLegacyPayload) {
    return {
      snapshot: OPERATOR_FALLBACK_FIXTURE,
      dataSource: "fixture",
      usesFallback: true,
    };
  }

  return {
    snapshot: {
      ...OPERATOR_FALLBACK_FIXTURE,
      summary: mapLegacyStatsToSummary(statList),
      holdings: mapLegacyListToHoldings(dataList),
    },
    dataSource: "legacyNormalized",
    usesFallback: false,
  };
};

export { DASHBOARD_ERROR_KEYS };
