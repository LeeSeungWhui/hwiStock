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
    mode: "unknown",
    sessionKst: "KST -",
    venueRoute: "-",
    killSwitch: "off",
    serviceHealth: "degraded",
    dataSourceHealth: "not_loaded",
    orderGate: "unknown",
  },
  summary: {
    cashBalance: "masked",
    reserveBalance: "masked",
    todayPnl: "system_report_only",
    realizedPnl: "system_report_only",
    openPositions: 0,
    riskRejects: 0,
    aiJobStatus: "missing_or_safe_blocked",
    reportStatus: "operator_window_required",
    accountId: "account_alias:masked",
    paperNetworkEnabled: false,
    paperOrderEnabled: false,
    paperOrdersSubmitted: false,
    paperObservationAccepted: false,
    operationalTradingReadiness: false,
  },
  readinessTruth: {
    headline: "NOT_READY",
    severity: "danger",
    operatorMessage: "운영 API 응답을 아직 받지 못했습니다. 이 값은 실데이터가 아닙니다.",
    blockers: [
      "fallback_snapshot",
      "paper_network_disabled",
      "paper_order_loop_disabled",
    ],
    evidenceGaps: [],
    paperExperimentReady: false,
    paperOrderLoopEnabled: false,
    paperNetworkEnabled: false,
    paperOrderEnabled: false,
    paperOrdersSubmitted: false,
    paperObservationAccepted: false,
    operationalTradingReadiness: false,
    operationalTradingReadinessBlocksPaperOperation: false,
    liveMoneyTradingReady: "not_applicable",
    productionQualityReady: "partial_non_blocking",
    orderGate: "unknown",
    fallbackArtifactKeys: [],
    serviceVisibilityIsNotReadiness: true,
  },
  holdings: [],
  candidates: [],
  intelligence: [],
  aiThread: [],
  auditLog: [],
  runtime: {
    artifactFreshness: {
      snapshotAtKst: null,
      staleKeys: [],
      missingKeys: [],
      allRequiredFresh: false,
      artifacts: {},
    },
    kisPaperRunnerServicePolicy: {
      paperNetworkEnabledByService: false,
      paperOrderEnabledByService: false,
      paperNetworkEnabledEffective: false,
      paperOrderEnabledEffective: false,
      orderFlagContradictsReadiness: false,
      serviceFiles: [],
      livePolicy: {},
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
