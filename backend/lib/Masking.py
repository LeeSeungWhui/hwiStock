"""
파일명: backend/lib/Masking.py
작성자: LSH
갱신일: 2026-02-25
설명: 로그 출력용 식별자 마스킹 유틸
"""


def maskUserIdentifierForLog(identifier: str | None) -> str | None:
    """
    설명: 사용자 식별자(이메일/아이디)를 로그 출력용으로 마스킹
    처리 규칙: 이메일은 로컬파트만 마스킹하고, 일반 문자열은 앞 1~2글자만 노출
    반환값: 마스킹된 식별자 문자열을 반환하며, 공백/빈 입력은 None을 반환
    갱신일: 2026-02-25
    """
    value = (identifier or "").strip()
    if not value:
        return None
    if "@" in value:
        localPart, domainPart = value.split("@", 1)
        if not localPart:
            return f"***@{domainPart}"
        if len(localPart) == 1:
            maskedLocal = "*"
        elif len(localPart) == 2:
            maskedLocal = f"{localPart[0]}*"
        else:
            maskedLocal = f"{localPart[:2]}{'*' * (len(localPart) - 2)}"
        return f"{maskedLocal}@{domainPart}"
    if len(value) == 1:
        return "*"
    if len(value) == 2:
        return f"{value[0]}*"
    return f"{value[:2]}{'*' * (len(value) - 2)}"
