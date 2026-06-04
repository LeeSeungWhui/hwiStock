/**
 * 파일명: jsonPayload.js
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 백엔드가 반환하는 JSON 문자열을 보정/정규화하는 공용 유틸
 */

const BROKEN_ARRAY_REGEX = /"([^"\\]+)"\s*:\s*](?=\s*[},])/g;

/**
 * 서버가 [] 대신 ]만 내려보내는 경우를 감지해 자동 보정
 * @param {string} text
 * @returns {string}
 * @description 깨진 배열 토큰 교체 기반 파싱 실패 완화
 * @updated 2026-02-27
 */
const autofixBrokenArrays = (text) => {
  if (!text || typeof text !== "string") return text;
  return text.replace(BROKEN_ARRAY_REGEX, '"$1": []');
};

/**
 * @description 문자열 JSON을 보정 가능한 형태로 정규화. 입력/출력 계약을 함께 명시
 * @param {string} text
 * @returns {string}
 */
export const sanitizeJsonString = (text) => {
  if (!text) return text;

  const source = autofixBrokenArrays(text);

  const stack = [];
  let sanitized = "";
  let inString = false;
  let escapeNext = false;
  let stringMode = "value";

  /**
   * @description start 인덱스 이후 첫 비공백 문자와 위치를 반환해 문자열 종료 판단에 사용
   * @param {string} input
   * @param {number} start
   * @returns {{ sourceChar: string, index: number }}
   * @updated 2026-02-27
  */
  const skipWhitespace = (input, start) => {
    for (let inputIndex = start; inputIndex < input.length; inputIndex += 1) {
      const isWhitespaceChar =
        input[inputIndex] === " " ||
        input[inputIndex] === "\t" ||
        input[inputIndex] === "\r" ||
        input[inputIndex] === "\n";
      if (isWhitespaceChar) continue;
      return { sourceChar: input[inputIndex], index: inputIndex };
    }
    return { sourceChar: "", index: input.length };
  };

  for (let index = 0; index < source.length; index += 1) {
    const sourceChar = source.charAt(index);

    if (inString) {
      if (escapeNext) {
        escapeNext = false;
        sanitized += sourceChar;
        continue;
      }
      if (sourceChar === "\\") {
        escapeNext = true;
        sanitized += "\\";
        continue;
      }

      if (sourceChar === '"') {
        const nextInfo = skipWhitespace(source, index + 1);
        let shouldClose;
        if (stringMode === "key") {
          shouldClose = nextInfo.sourceChar === ":";
        } else {
          shouldClose =
            nextInfo.sourceChar === "," ||
            nextInfo.sourceChar === "}" ||
            nextInfo.sourceChar === "]" ||
            nextInfo.sourceChar === "";
          if (nextInfo.sourceChar === "]" || nextInfo.sourceChar === "}") {
            const nextTokenInfo = skipWhitespace(source, nextInfo.index + 1);
            if (nextTokenInfo.sourceChar === '"') {
              shouldClose = false;
            }
          }
        }

        if (shouldClose) {
          inString = false;
          stringMode = "value";
          sanitized += '"';
          continue;
        }

        sanitized += '\\"';
        continue;
      }

      const sourceCharCode = sourceChar.charCodeAt(0);
      if (sourceCharCode <= 0x1f) {
        if (sourceChar === "\n") sanitized += "\\n";
        else if (sourceChar === "\r") sanitized += "\\r";
        else if (sourceChar === "\t") sanitized += "\\t";
        else sanitized += `\\u${sourceCharCode.toString(16).padStart(4, "0")}`;
        continue;
      }

      sanitized += sourceChar;
      continue;
    }

    if (sourceChar === '"') {
      inString = true;
      const topStackItem = stack.at(-1);
      stringMode =
        topStackItem && topStackItem.type === "object" && topStackItem.expectKey ? "key" : "value";
      sanitized += '"';
      continue;
    }

    if (sourceChar === "{") {
      stack.push({ type: "object", expectKey: true });
      sanitized += sourceChar;
      continue;
    }

    if (sourceChar === "[") {
      stack.push({ type: "array" });
      sanitized += sourceChar;
      continue;
    }

    if (sourceChar === "}") {
      stack.pop();
      sanitized += sourceChar;
      if (stack.length && stack[stack.length - 1].type === "object") {
        stack[stack.length - 1].expectKey = false;
      }
      continue;
    }

    if (sourceChar === "]") {
      stack.pop();
      sanitized += sourceChar;
      continue;
    }

    if (sourceChar === ":") {
      sanitized += sourceChar;
      if (stack.length && stack[stack.length - 1].type === "object") {
        stack[stack.length - 1].expectKey = false;
      }
      continue;
    }

    if (sourceChar === ",") {
      sanitized += sourceChar;
      if (stack.length && stack[stack.length - 1].type === "object") {
        stack[stack.length - 1].expectKey = true;
      }
      continue;
    }

    sanitized += sourceChar;
  }

  return sanitized;
};

/**
 * @description JSON 응답을 파싱하되, 실패 시 보정 뒤 재시도
 * @param {string} rawText 서버 응답 텍스트
 * @param {object} [options]
 * @param {string} [options.context='API'] 로깅용 컨텍스트
 * @param {Console} [options.logger=console] 로깅 대상
 * @returns {object|null} 파싱된 객체 또는 null
 */
export const parseJsonPayload = (rawText, options = {}) => {

  if (!rawText) return null;
  const { context = "API", logger = console } = options;
  try {
    return JSON.parse(rawText);
  } catch (error) {
    try {
      return JSON.parse(sanitizeJsonString(rawText));
    } catch (innerParseError) {
      const message = innerParseError?.message || "";
      const positionMatch = /position (\d+)/.exec(message);
      const errorPosition = positionMatch ? Number(positionMatch[1]) : 0;
      logger?.error?.(
        `[${context}] JSON parsing failed`,
        {
          message,
          position: errorPosition,
        },
      );
      return null;
    }
  }
};

const JSON_STRING_KEY_LIST = ["result", "data", "payload"];

/**
 * @description result/data/payload 문자열 필드를 JSON 객체로 자동 파싱
 * @param {object|null} payload 파싱된 초기 객체
 * @param {object} [options]
 * @param {string[]} [options.keys] 파싱 대상 필드 목록
 * @returns {object|null} 정규화된 객체
 */
export const normalizeNestedJsonFields = (payload, options = {}) => {

  if (!payload || typeof payload !== "object") return payload;
  const { keys = JSON_STRING_KEY_LIST } = options;

  keys.forEach((key) => {
    if (!Object.prototype.hasOwnProperty.call(payload, key)) return;
    const payloadValue = Reflect.get(payload, key);
    if (typeof payloadValue !== "string") return;
    const trimmed = payloadValue.trim();
    if (!trimmed) return;
    const parsed = parseJsonPayload(trimmed, { context: `Nested:${key}` });
    if (parsed && typeof parsed === "object") {
      payload[key] = parsed;
    }
  });

  return payload;
};
