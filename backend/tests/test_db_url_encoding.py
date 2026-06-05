import os
import sys


baseDir = os.path.dirname(os.path.dirname(__file__))
if baseDir not in sys.path:
    sys.path.insert(0, baseDir)


def testBuildMysqlUrlEncodesUserInfo():
    from server import buildNetworkDbUrl

    dbUrl = buildNetworkDbUrl(
        scheme="mysql+aiomysql",
        host="localhost",
        port="3306",
        database="sample_db",
        user="demo@user",
        password="p@ss:wo/rd+space ok",
    )

    assert dbUrl == "mysql+aiomysql://demo%40user:p%40ss%3Awo%2Frd%2Bspace+ok@localhost:3306/sample_db"


def testBuildPostgresqlUrlEncodesUserInfo():
    from server import buildNetworkDbUrl

    dbUrl = buildNetworkDbUrl(
        scheme="postgresql",
        host="127.0.0.1",
        port="5432",
        database="appdb",
        user="team:user",
        password="!:@",
    )

    assert dbUrl == "postgresql://team%3Auser:%21%3A%40@127.0.0.1:5432/appdb"


def testBuildPostgresqlUrlWrapsIpv6Host():
    from server import buildNetworkDbUrl

    dbUrl = buildNetworkDbUrl(
        scheme="postgresql",
        host="::1",
        port="5432",
        database="appdb",
        user="demo",
        password="secret",
    )

    assert dbUrl == "postgresql://demo:secret@[::1]:5432/appdb"


def testBuildPostgresqlUrlKeepsBracketedIpv6Host():
    from server import buildNetworkDbUrl

    dbUrl = buildNetworkDbUrl(
        scheme="postgresql",
        host="[::1]",
        port="5432",
        database="appdb",
        user="demo",
        password="secret",
    )

    assert dbUrl == "postgresql://demo:secret@[::1]:5432/appdb"


def testBuildPostgresqlConnectOptionsSetsHwiStockSearchPath():
    from server import buildPostgresqlConnectOptions

    options = buildPostgresqlConnectOptions("hwistock_core")

    assert options == {"server_settings": {"search_path": "hwistock_core,public"}}


def testResolveHwiStockPostgresqlRuntimeConnectionOverridesTemplateDatabase(monkeypatch):
    from server import resolveHwiStockPostgresqlRuntimeConnection

    monkeypatch.delenv("HWISTOCK_DATABASE_URL", raising=False)
    monkeypatch.setenv("HWISTOCK_DB_ISOLATION_ENABLED", "true")
    monkeypatch.setenv("HWISTOCK_POSTGRES_DB", "hwistock")
    monkeypatch.setenv("HWISTOCK_POSTGRES_SCHEMA", "hwistock_core")

    dbUrl, options, meta = resolveHwiStockPostgresqlRuntimeConnection(
        {
            "host": "127.0.0.1",
            "port": "5432",
            "database": "mywebtemplate",
            "user": "demo",
            "password": "secret",
        }
    )

    assert dbUrl == "postgresql://demo:secret@127.0.0.1:5432/hwistock"
    assert options == {"server_settings": {"search_path": "hwistock_core,public"}}
    assert meta["database"] == "hwistock"
    assert meta["schema"] == "hwistock_core"
