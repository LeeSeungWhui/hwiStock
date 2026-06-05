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
    orderGate: "blocked_fixture",
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
    paperNetworkEnabled: false,
    paperOrderEnabled: false,
    paperOrdersSubmitted: false,
    paperObservationAccepted: false,
    operationalTradingReadiness: false,
  },
  readinessTruth: {
    headline: "NOT_READY_FOR_PAPER_TRADING",
    severity: "danger",
    operatorMessage: "로컬 폴백 데이터입니다. 모의매매 관찰 준비 완료로 해석하면 안 됩니다.",
    blockers: [
      "fallback_fixture",
      "paper_network_disabled",
      "paper_orders_not_submitted",
      "paper_observation_not_accepted",
      "operational_trading_readiness_false",
    ],
    paperNetworkEnabled: false,
    paperOrderEnabled: false,
    paperOrdersSubmitted: false,
    paperObservationAccepted: false,
    operationalTradingReadiness: false,
    orderGate: "blocked_fixture",
    fallbackArtifactKeys: [],
    serviceVisibilityIsNotReadiness: true,
  },
  holdings: [],
  candidates: [],
  intelligence: [],
  aiThread: [],
  auditLog: [],
  runtime: {
    kisPaperRunnerServicePolicy: {
      paperNetworkEnabledByService: false,
      paperOrderEnabledByService: false,
      orderFlagContradictsReadiness: false,
      serviceFiles: [],
    },
  },
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
        readinessTruth: { ...OPERATOR_FALLBACK_FIXTURE.readinessTruth, ...operatorResult.readinessTruth },
        holdings: operatorResult.holdings || OPERATOR_FALLBACK_FIXTURE.holdings,
        candidates: operatorResult.candidates || OPERATOR_FALLBACK_FIXTURE.candidates,
        intelligence: operatorResult.intelligence || OPERATOR_FALLBACK_FIXTURE.intelligence,
        aiThread: operatorResult.aiThread || OPERATOR_FALLBACK_FIXTURE.aiThread,
        auditLog: operatorResult.auditLog || OPERATOR_FALLBACK_FIXTURE.auditLog,
        runtime: { ...OPERATOR_FALLBACK_FIXTURE.runtime, ...operatorResult.runtime },
      },
      dataSource: "api",
      usesFallback: false,
    };
  }

  return {
    snapshot: OPERATOR_FALLBACK_FIXTURE,
    dataSource: "fixture",
    usesFallback: true,
  };
};

export { DASHBOARD_ERROR_KEYS };
