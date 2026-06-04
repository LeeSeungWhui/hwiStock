"""
파일명: backend/tests/test_casing.py
작성자: LSH
갱신일: 2026-02-27
설명: snake_case -> camelCase 변환 유틸의 회귀 테스트
"""

from lib.Casing import convertKeysToCamelCase
from lib.Casing import toCamelCaseKey


def testToCamelCaseKeyVariants():
    """
    설명: 다양한 입력 키가 예상 camelCase로 변환되는지 검증
    갱신일: 2026-02-27
    """
    cases = {
        "user_no": "userNo",
        "USER_NO": "userNo",
        "id": "id",
        "ID": "id",
        "long_snake_case_name": "longSnakeCaseName",
        "LONG_SNAKE_CASE_NAME": "longSnakeCaseName",
        "_LEADING__UNDER__SCORE_": "leadingUnderScore",
    }
    for key, expected in cases.items():
        assert toCamelCaseKey(key) == expected


def testConvertKeysToCamelCaseNested():
    """
    설명: dict/list 중첩 구조에서 문자열 키만 재귀적으로 변환되는지 검증
    갱신일: 2026-02-27
    """
    inputValue = {
        "user_no": 7,
        "profile_data": {"first_name": "lee", "LAST_NAME": "hwi"},
        "item_list": [{"item_id": 1}, {"item_id": 2}],
        1: "non-string-key",
    }

    converted = convertKeysToCamelCase(inputValue)

    assert converted["userNo"] == 7
    assert converted["profileData"]["firstName"] == "lee"
    assert converted["profileData"]["lastName"] == "hwi"
    assert converted["itemList"][0]["itemId"] == 1
    assert converted["itemList"][1]["itemId"] == 2
    assert converted[1] == "non-string-key"
