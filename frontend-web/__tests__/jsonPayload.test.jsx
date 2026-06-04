/**
 * 파일명: jsonPayload.test.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-03
 * 설명: jsonPayload 유틸(parse/sanitize/중첩 JSON 정규화) 테스트
 */

import { describe, expect, it } from "vitest";
import {
  normalizeNestedJsonFields,
  parseJsonPayload,
} from "@/app/lib/runtime/jsonPayload";

describe("jsonPayload utils", () => {
  it("문자열 내부 개행 문자를 정규화한다", () => {
    const rawJsonText = '{"message":"line1\nline2"}';
    const parsed = parseJsonPayload(rawJsonText, { context: "test", logger: console });
    expect(parsed).toEqual({ message: "line1\nline2" });
  });

  it("배열 필드가 ]만 내려와도 []로 자동 보정한다", () => {
    const rawJsonText = '{"languageSkillList": ], "status":"ok"}';
    const parsed = parseJsonPayload(rawJsonText, { context: "test", logger: console });
    expect(parsed).toEqual({ languageSkillList: [], status: "ok" });
  });

  it("하이픈이 포함된 키의 깨진 배열 토큰도 []로 보정한다", () => {
    const rawJsonText = '{"ability-list": ], "status":"ok"}';
    const parsed = parseJsonPayload(rawJsonText, { context: "test", logger: console });
    expect(parsed).toEqual({ "ability-list": [], status: "ok" });
  });

  it("result/data/payload 문자열 JSON을 객체로 정규화한다", () => {
    const nestedPayloadObj = {
      result: '{"status":"ok","count":1}',
      data: '{"items":[1,2]}',
      payload: '{"key":"value"}',
    };
    const normalized = normalizeNestedJsonFields(nestedPayloadObj);
    expect(normalized.result).toEqual({ status: "ok", count: 1 });
    expect(normalized.data).toEqual({ items: [1, 2] });
    expect(normalized.payload).toEqual({ key: "value" });
  });
});
