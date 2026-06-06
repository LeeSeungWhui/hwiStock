import os
import sys

from conftest import pgTestSettings
from db_support import fetchValPg

baseDir = os.path.dirname(os.path.dirname(__file__))
if baseDir not in sys.path:
    sys.path.insert(0, baseDir)


def testTransactionSingleAndUniqueRollback():
    from lib import Database as DB
    from server import onShutdown, onStartup
    from service import TransactionService
    import anyio

    async def runScenario():
        await onStartup()
        try:
            singleResult = await TransactionService.testSingle()
            assert singleResult["inserted"].startswith("tx-")

            try:
                await TransactionService.testUniqueViolation()
            except Exception as exc:
                assert "unique" in str(exc).lower() or "duplicate" in str(exc).lower()
            else:
                raise AssertionError("unique violation scenario did not raise")
        finally:
            await onShutdown()
            DB.dbManagers.clear()
            DB.setPrimaryDbName("main_db")

    anyio.run(runScenario)

    cnt = fetchValPg(
        pgTestSettings,
        "SELECT COUNT(*) FROM T_TEST_TRANSACTION WHERE VALUE = $1",
        "tx-dup",
    )
    assert cnt == 0


def testTransactionDemoRoutesStayQuarantined():
    from server import app

    route_paths = {getattr(route, "path", "") for route in app.routes}

    assert "/api/v1/transaction/test/single" not in route_paths
    assert "/api/v1/transaction/test/unique-violation" not in route_paths
