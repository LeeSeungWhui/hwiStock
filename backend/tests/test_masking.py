"""
파일명: backend/tests/test_masking.py
작성자: LSH
갱신일: 2026-03-03
설명: 로그 식별자 마스킹 유틸 동작 검증
"""

from lib.Masking import maskUserIdentifierForLog


def testMaskUserIdentifierForLogHandlesEmpty():
    assert maskUserIdentifierForLog(None) is None
    assert maskUserIdentifierForLog("") is None
    assert maskUserIdentifierForLog("   ") is None


def testMaskUserIdentifierForLogMasksEmail():
    assert maskUserIdentifierForLog("a@demo.com") == "*@demo.com"
    assert maskUserIdentifierForLog("ab@demo.com") == "a*@demo.com"
    assert maskUserIdentifierForLog("abcdef@demo.com") == "ab****@demo.com"


def testMaskUserIdentifierForLogMasksPlainText():
    assert maskUserIdentifierForLog("a") == "*"
    assert maskUserIdentifierForLog("ab") == "a*"
    assert maskUserIdentifierForLog("abcdef") == "ab****"
