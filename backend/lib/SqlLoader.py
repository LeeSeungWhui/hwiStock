"""
파일명: backend/lib/SqlLoader.py
작성자: LSH
갱신일: 2025-09-07
설명: sql 파일에서 `-- name:` 블록을 파싱하여 쿼리 레지스트리 구성
"""

import os
from typing import Dict, List, Tuple, Set, Optional

from lib.Logger import logger


nameMark = "-- name:"


def parseSqlFile(filePath: str) -> List[Tuple[str, str]]:
    """
    설명: 단일 SQL 파일을 name/sql 쌍 목록으로 파싱
    제약: 파일 내 중복 금지 / UTF-8.
    갱신일: 2025-11-12
    """
    entries: List[Tuple[str, str]] = []
    if not os.path.exists(filePath):
        return entries

    currentName: Optional[str] = None
    currentBuf: List[str] = []
    with open(filePath, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if nameMark in line:

                # 이전 버퍼를 먼저 기록
                if currentName is not None:
                    sql = ("\n".join(currentBuf)).strip()
                    if sql:
                        entries.append((currentName, sql))
                    currentBuf = []

                # 마커 뒤에서 이름 문자열 추출
                name = line.split(nameMark, 1)[1].strip()
                if not name:
                    raise ValueError(f"empty query name in file: {filePath}")

                # 동일 파일 내 중복 여부 확인
                if any(n == name for (n, _) in entries):
                    raise ValueError(f"duplicate query name in {filePath}: {name}")
                currentName = name
            else:
                if currentName is not None:
                    currentBuf.append(raw)

    if currentName is not None and currentBuf:
        sql = ("\n".join(currentBuf)).strip()
        if sql:
            entries.append((currentName, sql))

    return entries


def scanSqlQueries(folderPath: str) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, Set[str]]]:
    """
    설명: 폴더를 스캔해 쿼리/파일 매핑을 구성. 호출 맥락의 제약을 기준으로 동작 기준 확정
    제약: 파일 간 중복 발견 시 예외.
    갱신일: 2025-11-12
    """
    queries: Dict[str, str] = {}
    nameToFile: Dict[str, str] = {}
    fileToNames: Dict[str, Set[str]] = {}

    if not os.path.exists(folderPath):
        os.makedirs(folderPath, exist_ok=True)
        return queries, nameToFile, fileToNames

    for root, _, files in os.walk(folderPath):
        for fileName in files:
            if not fileName.lower().endswith(".sql"):
                continue
            filePath = os.path.join(root, fileName)
            try:
                pairs = parseSqlFile(filePath)
                for name, sql in pairs:
                    if name in queries and nameToFile.get(name) != filePath:

                        # 파일 간 중복 발견 시 즉시 실패
                        raise ValueError(
                            f"duplicate query key detected: {name} from {filePath}"
                        )
                    queries[name] = sql
                    nameToFile[name] = filePath
                fileToNames[filePath] = set(n for n, _ in pairs)
            except Exception as e:
                logger.error(f"sql.load.error file={filePath} msg={str(e)}")
                raise

    return queries, nameToFile, fileToNames


def loadSqlQueries(folderPath: str) -> Dict[str, str]:
    """
    설명: scanSqlQueries 결과 중 쿼리 dict만 반환
    갱신일: 2025-11-12
    처리 규칙: 입력값을 검증하고 실패 시 예외/기본값 경로로 수렴
    """
    queries, _, _ = scanSqlQueries(folderPath)
    return queries
