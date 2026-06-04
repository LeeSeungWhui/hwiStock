import os
import sys
import pytest


baseDir = os.path.dirname(os.path.dirname(__file__))
if baseDir not in sys.path:
    sys.path.insert(0, baseDir)


def testSavepointPartialRollback():
    from lib import Database as DB
    from lib.Transaction import transaction, savepoint
    from server import onShutdown, onStartup
    from service.TransactionService import ensureTables
    import anyio

    async def runScenario():
        await onStartup()
        try:
            @transaction("main_db")
            async def doOps():
                await ensureTables()
                db = DB.dbManagers["main_db"]
                await db.execute("DELETE FROM T_TEST_TRANSACTION")
                await db.execute("INSERT INTO T_TEST_TRANSACTION (VALUE) VALUES (:val)", {"val": "keep1"})
                try:
                    async with savepoint("main_db", "sp1"):
                        await db.execute("INSERT INTO T_TEST_TRANSACTION (VALUE) VALUES (:val)", {"val": "dup"})
                        await db.execute("INSERT INTO T_TEST_TRANSACTION (VALUE) VALUES (:val)", {"val": "dup"})
                except Exception:
                    pass
                await db.execute("INSERT INTO T_TEST_TRANSACTION (VALUE) VALUES (:val)", {"val": "keep2"})

            await doOps()
            db = DB.dbManagers["main_db"]
            rows = await db.fetchAll("SELECT VALUE AS value, COUNT(*) as cnt FROM T_TEST_TRANSACTION GROUP BY VALUE")
            return {row["value"]: row["cnt"] for row in (rows or [])}
        finally:
            await onShutdown()
            DB.dbManagers.clear()
            DB.setPrimaryDbName("main_db")

    countsByValue = anyio.run(runScenario)
    assert countsByValue.get("keep1") == 1
    assert countsByValue.get("keep2") == 1
    assert countsByValue.get("dup") in (None, 1)


def testSavepointNameValidation():
    from lib.Transaction import savepoint, TransactionError

    with pytest.raises(TransactionError):
        savepoint("main_db", "sp1; DROP TABLE T_USER;")

    with pytest.raises(TransactionError):
        savepoint("main_db", "1bad")

    sp = savepoint("main_db", "sp_valid_1")
    assert sp.name == "sp_valid_1"
