"""
hwiStock KIS paper continuous runner service wrapper.
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from lib.kis_paper_continuous_runtime import (
    buildPaperExperimentReadiness,
    evaluateContinuousPaperRunnerStatus,
    evaluateIntentExecutionPreflight,
    evaluatePaperRiskOverlay,
    evaluatePaperSessionLimits,
    estimateIntentNotionalKrw,
    evaluateRealtimeExitDecision,
    loadContinuousPaperRunnerConfig,
    loadPaperOrderApproval,
    main,
    markIntentConsumed,
    resetContinuousPaperRunnerForTests,
    runContinuousPaperTick,
    writeContinuousPaperEvidence,
)

__all__ = (
    "buildPaperExperimentReadiness",
    "evaluateContinuousPaperRunnerStatus",
    "evaluateIntentExecutionPreflight",
    "evaluatePaperRiskOverlay",
    "evaluatePaperSessionLimits",
    "estimateIntentNotionalKrw",
    "evaluateRealtimeExitDecision",
    "loadContinuousPaperRunnerConfig",
    "loadPaperOrderApproval",
    "main",
    "markIntentConsumed",
    "resetContinuousPaperRunnerForTests",
    "runContinuousPaperTick",
    "writeContinuousPaperEvidence",
)


if __name__ == "__main__":
    raise SystemExit(main())
