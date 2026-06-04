"""
파일명: backend/service/TransactionService.py
작성자: LSH
갱신일: 2025-12-18
설명: 트랜잭션/세이브포인트 동작을 검증하기 위한 데모 서비스
"""

from __future__ import annotations

import uuid

from lib import Database as DB
from lib.Transaction import transaction


async def ensureTables(dbName: str = "main_db") -> None:
    """
    설명: 테스트용 트랜잭션 테이블 존재만 확인(런타임 DDL 금지)
    갱신일: 2026-02-24
    """
    db = DB.getManager(dbName)
    if not db:
        raise RuntimeError(f"database not found: {dbName}")
    try:
        await db.fetchOneQuery("transaction.pingTestTable")
    except Exception as e:
        raise RuntimeError("T_TEST_TRANSACTION table is missing. seed/migrate schema before runtime.") from e


@transaction("main_db")
async def testSingle() -> dict:
    """
    설명: 테스트 테이블에 단일 값을 insert하고 커밋된 값을 결과로 반환. 호출 맥락의 제약을 기준으로 동작 기준 확정
    실패 동작: 테이블 누락/DB 오류가 발생하면 예외를 전파해 데코레이터가 롤백
    반환값: 삽입된 값을 포함한 {"inserted": "..."} dict를 반환
    갱신일: 2026-02-24
    """
    await ensureTables("main_db")
    db = DB.getManager("main_db")
    assert db is not None
    value = f"tx-{uuid.uuid4().hex[:8]}"
    await db.executeQuery("transaction.insertValue", {"val": value})
    return {"inserted": value}


@transaction("main_db")
async def testUniqueViolation() -> None:
    """
    설명: 동일 값을 2회 insert해 UNIQUE 제약 위반 롤백 경로를 의도적으로 유발
    실패 동작: 두 번째 insert에서 예외가 발생하며 데코레이터가 전체 트랜잭션을 롤백
    반환값: 성공 반환값은 없고, 정상 동작 시 예외를 통해 상위 레이어가 409를 응답
    갱신일: 2026-02-24
    """
    await ensureTables("main_db")
    db = DB.getManager("main_db")
    assert db is not None

    # UNIQUE 제약 위반을 의도적으로 유발한다. 데코레이터가 전체 트랜잭션을 롤백해야 한다.
    await db.executeQuery("transaction.insertValue", {"val": "tx-dup"})
    await db.executeQuery("transaction.insertValue", {"val": "tx-dup"})
