"""
파일명: backend/lib/Transaction.py
작성자: LSH
갱신일: 2026-02-24
설명: 단일/다중 DB 트랜잭션 데코레이터와 예외 처리 유틸
"""

from __future__ import annotations

from functools import wraps
from contextlib import AsyncExitStack
from typing import Awaitable, Callable, List, Union, Tuple, TypeVar
import time
import uuid
import re

from lib.Database import dbManagers
from lib import Database as DB
from lib.RequestContext import getRequestId
from lib.Logger import logger


class TransactionError(Exception):
    pass


TransactionResult = TypeVar("TransactionResult")


def transaction(
    dbNames: Union[str, List[str]],
    *,
    isolation: str | None = None,
    timeoutMs: int | None = None,
    retries: int = 0,
    retryOn: Tuple[type[BaseException], ...] = (),
):
    """
    설명: 단일/다중 DB 트랜잭션 지원 데코레이터 처리
    처리 규칙: timeoutMs를 기준으로 options(timeout)을 구성
    실패 동작: 미지원 키워드 인자 전달 시 TypeError를 발생
    인자: dbNames/isolation/timeoutMs/retries/retryOn
    갱신일: 2026-02-28
    """
    if isinstance(dbNames, str):
        dbList = [dbNames]
    else:
        dbList = list(dbNames)

    transactionOptions: dict[str, object] = {}
    if isinstance(isolation, str) and isolation.strip():
        transactionOptions["isolation"] = isolation.strip()
    effectiveTimeoutMs = timeoutMs
    if effectiveTimeoutMs is not None:
        try:
            timeoutFloat = float(effectiveTimeoutMs) / 1000.0
            if timeoutFloat > 0:
                transactionOptions["timeout"] = timeoutFloat
        except (TypeError, ValueError):
            pass

    def decorator(func):
        """
        설명: 트랜잭션 옵션을 캡처한 데코레이터 생성
        처리 규칙: 외부에서 전달된 옵션을 고정한 wrapper를 반환
        반환값: 트랜잭션 경계를 적용한 비동기 wrapper 함수
        갱신일: 2026-02-28
        """

        @wraps(func)
        async def wrapper(*args, **kwargs):
            """
            설명: 대상 함수 실행 경로에 트랜잭션/재시도 정책 적용
            실패 동작: 예외 발생 시 롤백 로그를 남기고 retryOn/retries 조건에 따라 재시도 후 최종 예외를 재전파
            갱신일: 2026-02-26
            """
            attempt = 0
            lastExc: BaseException | None = None
            while attempt <= max(0, retries):
                attempt += 1
                txId = uuid.uuid4().hex[:12]
                stack: AsyncExitStack | None = None
                started = time.perf_counter()
                startCount = DB.getSqlCount()
                try:
                    stack = AsyncExitStack()

                    # 중첩된 모든 DB 트랜잭션을 열어 동일 커넥션을 보장
                    for name in dbList:
                        if name not in dbManagers:
                            raise TransactionError(f"database not found: {name}")
                        manager = dbManagers[name]
                        await stack.enter_async_context(manager.database.transaction(**transactionOptions))
                        try:
                            logger.info(
                                f"tx.begin txId={txId} db={name} isolation={isolation} timeoutMs={effectiveTimeoutMs} requestId={getRequestId()}"
                            )
                        except Exception:
                            pass
                    result = await func(*args, **kwargs)

                    try:
                        elapsedMs = int((time.perf_counter() - started) * 1000)
                        sqlCount = max(0, DB.getSqlCount() - startCount)
                        logger.info(f"tx.commit txId={txId} latency_ms={elapsedMs} sql_count={sqlCount} requestId={getRequestId()}")
                    except Exception:
                        pass
                    return result

                except BaseException as e:

                    # 하위 트랜잭션이 예외를 인지해 롤백하도록 보장
                    if stack is not None:
                        try:
                            await stack.__aexit__(type(e), e, e.__traceback__)
                        except Exception:
                            pass
                        finally:
                            stack = None
                    try:
                        sqlCount = max(0, DB.getSqlCount() - startCount)
                        logger.error(f"tx.rollback txId={txId} error={e} sql_count={sqlCount} requestId={getRequestId()}")
                    except Exception:
                        pass
                    lastExc = e
                    if retryOn and not isinstance(e, retryOn):
                        break
                    if attempt > retries:
                        break
                    await sleepBackoff(attempt)
                finally:
                    if stack is not None:
                        try:
                            await stack.aclose()
                        except Exception:
                            pass
                    try:
                        elapsedMs = int((time.perf_counter() - started) * 1000)
                        logger.info(f"tx.end txId={txId} latency_ms={elapsedMs} requestId={getRequestId()}")
                    except Exception:
                        pass
            assert lastExc is not None
            raise lastExc

        return wrapper

    return decorator


async def runInTransaction(
    dbNames: Union[str, List[str]],
    operation: Callable[[], Awaitable[TransactionResult]],
    *,
    isolation: str | None = None,
    timeoutMs: int | None = None,
    retries: int = 0,
    retryOn: Tuple[type[BaseException], ...] = (),
) -> TransactionResult:
    """
    설명: 비동기 콜백을 단일/다중 DB 트랜잭션 경계 안에서 실행
    처리 규칙: transaction() 데코레이터 옵션을 그대로 재사용해 operation 실행 결과를 반환
    반환값: operation 비동기 콜백의 반환값
    갱신일: 2026-03-06
    """

    @transaction(
        dbNames,
        isolation=isolation,
        timeoutMs=timeoutMs,
        retries=retries,
        retryOn=retryOn,
    )
    async def runOperation() -> TransactionResult:
        """
        설명: runInTransaction에서 전달된 operation 콜백 실행
        반환값: operation 호출 결과
        갱신일: 2026-03-06
        """
        return await operation()

    return await runOperation()


async def sleepBackoff(attempt: int) -> None:
    """설명: 재시도 간 백오프(최대 0.5초) 수행 처리 규칙: attempt 비례 지연(min(0.05*attempt,0.5)) 적용. 갱신일: 2025-11-12"""
    try:
        import anyio

        await anyio.sleep(min(0.05 * attempt, 0.5))
    except Exception:
        return


class Savepoint:
    """설명: SAVEPOINT 관리용 컨텍스트 갱신일: 2025-11-12"""

    def __init__(self, dbName: str, name: str):
        """
        설명: 대상 DB와 savepoint 이름을 검증해 보관
        부작용: self.dbName/self.name 속성이 초기화
        갱신일: 2026-02-27
        """
        self.dbName = dbName
        self.name = self.validateName(name)

    @staticmethod
    def validateName(name: str) -> str:
        """설명: SAVEPOINT 이름을 SQL 식별자 규칙으로 검증 반환값: 정규화된 savepoint 이름 문자열. 갱신일: 2026-02-22"""
        if not isinstance(name, str):
            raise TransactionError("invalid savepoint name")
        normalizedName = name.strip()
        if not normalizedName:
            raise TransactionError("invalid savepoint name")
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", normalizedName):
            raise TransactionError("invalid savepoint name")
        return normalizedName

    async def __aenter__(self):
        """
        설명: 현재 트랜잭션에 SAVEPOINT를 등록한 뒤 동일 인스턴스를 컨텍스트로 제공
        처리 규칙: 대상 DB가 없으면 예외를 발생시키고, 존재하면 SAVEPOINT SQL을 먼저 실행
        반환값: 현재 SavepointContext 인스턴스(self)
        갱신일: 2025-11-12
        """
        if self.dbName not in dbManagers:
            raise TransactionError(f"database not found: {self.dbName}")
        await dbManagers[self.dbName].execute(f"SAVEPOINT {self.name}")
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """
        설명: 컨텍스트 종료 시점의 예외 유무에 따라 SAVEPOINT 롤백/해제를 분기하는 정리 단계
        처리 규칙: 예외가 있으면 ROLLBACK TO SAVEPOINT 후 RELEASE를 보장하고, 예외가 없으면 RELEASE만 수행
        부작용: 현재 트랜잭션 savepoint 상태를 변경
        갱신일: 2025-11-12
        """
        if exc:

            # 부분 작업을 롤백한 뒤 savepoint 해제
            try:
                await dbManagers[self.dbName].execute(f"ROLLBACK TO SAVEPOINT {self.name}")
            finally:
                await dbManagers[self.dbName].execute(f"RELEASE SAVEPOINT {self.name}")

            # 외부 트랜잭션을 유지하기 위해 예외를 삼킨다
            return True
        else:
            await dbManagers[self.dbName].execute(f"RELEASE SAVEPOINT {self.name}")
            return False


def savepoint(dbName: str, name: str) -> Savepoint:
    """설명: 부분 롤백용 SAVEPOINT 컨텍스트 생성 반환값: Savepoint 컨텍스트 인스턴스. 갱신일: 2025-11-12"""
    return Savepoint(dbName, name)


def transactionDefault():
    """설명: 기본 DB에 대한 transaction() 데코레이터 숏컷 반환값: primary DB 이름이 바인딩된 transaction 데코레이터. 갱신일: 2025-11-12"""
    return transaction(DB.getPrimaryDbName())
