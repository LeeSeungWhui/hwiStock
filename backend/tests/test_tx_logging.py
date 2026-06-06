import os
import sys


baseDir = os.path.dirname(os.path.dirname(__file__))
if baseDir not in sys.path:
    sys.path.insert(0, baseDir)


def testTxLogsIncludeRequestIdAndSqlCount(caplog):
    from lib import Database as DB
    from lib.RequestContext import resetRequestId, setRequestId
    from server import onShutdown, onStartup
    from service import TransactionService
    import anyio

    async def runScenario():
        await onStartup()
        token = setRequestId("rid-tx-1234")
        try:
            caplog.clear()
            await TransactionService.testSingle()
        finally:
            resetRequestId(token)
            await onShutdown()
            DB.dbManagers.clear()
            DB.setPrimaryDbName("main_db")

    anyio.run(runScenario)

    seen = False
    for rec in caplog.records:
        msg = rec.message
        if "tx.commit" in msg and "sql_count=" in msg and "requestId=rid-tx-1234" in msg:
            seen = True
            break
    assert seen
