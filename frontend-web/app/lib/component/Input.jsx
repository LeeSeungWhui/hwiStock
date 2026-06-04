/**
 * 파일명: Input.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 필터 및 마스크가 적용된 입력 컴포넌트
 */
import { useEffect, useState, forwardRef, useRef } from "react";
import Icon from "./Icon";
import {
  getBoundValue,
  setBoundValue,
  buildCtx,
  fireValueHandlers,
} from "../binding";
import { COMMON_COMPONENT_LANG_KO } from "@/app/common/i18n/lang.ko";

const MASK_TOKEN_RE = /[#Aa?*]/;

/**
 * @description 렌더링 및 필터/마스크 기반 입력 동기화 처리
 * 처리 규칙: 바인딩/controlled/uncontrolled 모드에 따라 값을 확정하고 변경 이벤트를 상위에 전파.
 * @updated 2026-02-27
 */
const Input = forwardRef(
  (
    {
      dataObj,
      dataKey,
      type = "text",
      className = "",
      placeholder,
      onChange,
      onValueChange,
      value: propValue,
      defaultValue = "",
      error,
      filter,
      mask,
      maxDigits,
      maxDecimals,
      prefix,
      suffix,
      togglePassword,
      ...rest
    },

    ref
  ) => {

    const isBoundControlled = Boolean(dataObj && dataKey);
    const isPropControlled =
      !isBoundControlled && typeof propValue !== "undefined";
    const [showPassword, setShowPassword] = useState(false);
    const [draftValue, setDraftValue] = useState(undefined);
    const [isComposing, setIsComposing] = useState(false);

    // IME compositionEnd 이후 브라우저가 포커스를 흔드는 경우가 있어 DOM focus 복구용으로만 사용한다.
    const inputFocusRef = useRef(null);
    const [shouldSkipNextCompositionChange, setShouldSkipNextCompositionChange] = useState(false);
    const [innerValue, setInnerValue] = useState(
      () => propValue ?? defaultValue ?? ""
    );
    const baseClassName =
      "appearance-none block w-full px-3 py-2 border rounded-md shadow-sm text-sm focus:outline-none focus:ring-2 focus:ring-offset-0";
    const HANGUL_RE = /[\u1100-\u11FF\u3130-\u318F\uAC00-\uD7A3]/; // 한글 범위

    const inputStateMapObj = {
      default: "border-gray-300 focus:ring-blue-500 focus:border-blue-500",
      error: "border-red-300 focus:ring-red-500 focus:border-red-500",
    };
    const hasStringMask = typeof mask === "string" && mask.trim().length > 0;
    const hasFunctionMask = typeof mask === "function";
    const hasInputConstraint = Boolean(filter) || hasStringMask || type === "number";

    /**
     * @description 마스크 패턴에 맞춰 입력 문자열을 변환. 입력/출력 계약을 함께 명시
     * 처리 규칙: 토큰(`#,A,a,?,*`) 기준으로 허용 문자만 소비하고 최종 마스크 문자열을 구성한다.
     * @updated 2026-02-27
     */
    const applyMask = (value, maskPattern) => {

      // 마스크에서 실제 입력 가능한 문자 개수 계산
      const maxLength = maskPattern.replace(/[^#A-Za-z?*]/g, "").length;

      // 마스크 패턴에 맞지 않는 문자 먼저 제거
      let cleanValue = "";
      let maskPosition = 0;

      for (let inputIndex = 0; inputIndex < value.length && cleanValue.length < maxLength; inputIndex += 1) {

        // 마스크의 다음 입력 위치 찾기
        while (
          maskPosition < maskPattern.length &&
          !MASK_TOKEN_RE.test(maskPattern[maskPosition])
        ) {
          maskPosition++;
        }

        if (maskPosition >= maskPattern.length) break;

        if (maskPattern[maskPosition] === "#") {
          if (/\d/.test(value[inputIndex])) {
            cleanValue += value[inputIndex];
            maskPosition++;
          }
        } else if (maskPattern[maskPosition] === "A") {
          if (/[a-zA-Z]/.test(value[inputIndex])) {
            cleanValue += value[inputIndex].toUpperCase();
            maskPosition++;
          }
        } else if (maskPattern[maskPosition] === "a") {
          if (/[a-zA-Z]/.test(value[inputIndex])) {
            cleanValue += value[inputIndex].toLowerCase();
            maskPosition++;
          }
        } else if (maskPattern[maskPosition] === "?") {
          if (/[a-zA-Z]/.test(value[inputIndex])) {
            cleanValue += value[inputIndex];
            maskPosition++;
          }
        } else if (maskPattern[maskPosition] === "*") {
          cleanValue += value[inputIndex];
          maskPosition++;
        }
      }

      // 마스크 적용
      let maskedValue = "";
      let valueIndex = 0;

      for (
        let maskIndex = 0;
        maskIndex < maskPattern.length && valueIndex < cleanValue.length;
        maskIndex += 1
      ) {
        if (MASK_TOKEN_RE.test(maskPattern[maskIndex])) {
          maskedValue += cleanValue[valueIndex];
          valueIndex++;
        } else {
          maskedValue += maskPattern[maskIndex];
        }
      }

      return maskedValue;
    };

    /**
     * @description propValue가 draftValue와 일치하면 조합 임시 표시 상태 해제
     * 처리 규칙: isPropControlled일 때만 draftValue를 undefined로 초기화한다.
     */
    useEffect(() => {
      if (!isPropControlled) return;
      if (draftValue !== undefined && propValue === draftValue) {
        setDraftValue(undefined);
      }
    }, [isPropControlled, propValue, draftValue]);

    /**
     * @description 바인딩 입력 조합 임시값 동기화 완료 확인
     * 처리 규칙: 외부 바인딩 값이 조합 임시값과 같아지면 임시 표시 상태를 비운다.
     */
    useEffect(() => {
      if (!isBoundControlled) return;
      if (draftValue === undefined) return;
      const boundValue = getBoundValue(dataObj, dataKey) ?? "";
      if (boundValue === draftValue) {
        setDraftValue(undefined);
      }
    }, [isBoundControlled, dataObj, dataKey, draftValue]);

    /**
     * @description 입력값을 필터/마스크 규칙으로 정제해 실제 상태에 커밋
     * 처리 규칙: bound/prop/uncontrolled 모드별로 쓰기 위치를 분기하고 커밋 성공 시 정제값을 반환한다.
     * @updated 2026-02-27
     */
    const commitValue = (rawInputValue) => {
      let inputValue = rawInputValue;
      if (filter) {
        const filterRejectPattern = new RegExp(`[^${filter}]`, "g");
        inputValue = inputValue.replace(filterRejectPattern, "");
      }
      if (hasFunctionMask) {
        const maskedValue = mask(inputValue);
        if (maskedValue === null || typeof maskedValue === "undefined") {
          inputValue = "";
        } else if (typeof maskedValue === "string") {
          inputValue = maskedValue;
        } else {
          inputValue = String(maskedValue);
        }
      } else if (hasStringMask) {
        inputValue = applyMask(inputValue, mask);
      }
      if (
        type === "number" &&
        (maxDigits !== undefined || maxDecimals !== undefined)
      ) {

        // 정규식 이스케이프 정리
        const numberInputPattern = new RegExp(
          `^-?\\d{0,${maxDigits ?? 2}}(\\.\\d{0,${maxDecimals ?? 2}})?$`
        );
        if (!numberInputPattern.test(inputValue)) {
          return;
        }
      }
      if (isBoundControlled) {
        setBoundValue(dataObj, dataKey, inputValue);
      } else if (isPropControlled) {

        // prop 기반 controlled 입력은 부모 상태를 단일 소스로 유지한다.
      } else {
        setInnerValue(inputValue);
      }
      if (isPropControlled || isBoundControlled) {
        setDraftValue(inputValue);
      } else {
        setDraftValue(undefined);
      }
      return inputValue;
    };

    // 조합 중 임시 문자열 허용 여부 판단

    /**
     * @description 조합 중 draft 문자열이 허용 규칙을 만족하는지 판별
     * 처리 규칙: filter/mask/number 타입 제약을 순차 검증해 허용 여부를 boolean으로 반환한다.
     * @updated 2026-02-27
     */
    const isAllowedDraft = (draftText) => {
      if (filter) {
        const allowHangulDraft = /가-힣/.test(filter);
        const allowedPatternText = allowHangulDraft ? `${filter}ㄱ-ㅎㅏ-ㅣ가-힣` : filter;
        if (!new RegExp(`^[${allowedPatternText}]*$`).test(draftText)) return false;
      }
      if (hasStringMask) {
        if (HANGUL_RE.test(draftText)) return false; // 마스크 존재 시 한글 금지 가정
      }
      if (type === "number" && !/^[0-9.\-]*$/.test(draftText)) return false;
      return true;
    };

    let committedValue = innerValue ?? "";
    if (isBoundControlled) {
      committedValue = getBoundValue(dataObj, dataKey) ?? "";
    } else if (isPropControlled) {
      committedValue = propValue ?? "";
    }

    // 마스크/필터/number가 있을 때 입력 직전 1차 필터링

    /**
     * @description beforeinput 단계에서 허용되지 않은 문자를 선차단
     * 처리 규칙: filter/mask/number 규칙 위반 입력은 `preventDefault()`로 즉시 차단한다.
     * @updated 2026-02-27
    */
    const handleBeforeInput = (event) => {
      if (!hasInputConstraint) return;
      const inputText = event.data;

      // 참고: 조합(insertCompositionText)은 onCompositionUpdate/Change에서 정밀 처리한다.
      // beforeinput 단계에서는 data가 없을 수 있으므로 무조건 차단하지 않는다.

      if (typeof inputText === "string" && inputText.length > 0) {

        // filter 기반 허용 목록
        if (filter) {
          const allowedInputPattern = new RegExp(`^[${filter}]+$`);
          if (!allowedInputPattern.test(inputText)) {
            event.preventDefault();
            return;
          }
        }

        // 마스크: 다음 슬롯 토큰을 계산해 토큰 유형과 입력 문자를 즉시 검증
        if (hasStringMask) {
          const currentInputText = event.currentTarget.value || "";
          let maskPosition = 0;
          for (
            let inputIndex = 0;
            inputIndex < currentInputText.length;
            inputIndex += 1
          ) {
            while (
              maskPosition < mask.length &&
              !MASK_TOKEN_RE.test(mask[maskPosition])
            ) {
              maskPosition += 1;
            }
            if (maskPosition >= mask.length) break;
            let isTokenMatched = false;
            if (mask[maskPosition] === "#") {
              isTokenMatched = /\d/.test(currentInputText[inputIndex]);
            } else if (
              mask[maskPosition] === "A" ||
              mask[maskPosition] === "a" ||
              mask[maskPosition] === "?"
            ) {
              isTokenMatched = /[a-zA-Z]/.test(currentInputText[inputIndex]);
            } else if (mask[maskPosition] === "*") {
              isTokenMatched = true;
            }
            if (isTokenMatched) maskPosition += 1;
          }
          while (
            maskPosition < mask.length &&
            !MASK_TOKEN_RE.test(mask[maskPosition])
          ) {
            maskPosition += 1;
          }

          const maskToken = maskPosition < mask.length ? mask[maskPosition] : null;
          if (maskToken) {
            let isInputAllowed = true;
            const isAlphaMaskToken =
              maskToken === "A" || maskToken === "a" || maskToken === "?";
            if (maskToken === "#") isInputAllowed = /\d/.test(inputText[0]);
            else if (isAlphaMaskToken)
              isInputAllowed = /[a-zA-Z]/.test(inputText[0]);
            else if (maskToken === "*") isInputAllowed = true;
            if (!isInputAllowed) {
              event.preventDefault();
              return;
            }
          }
        }

        // 숫자 타입: 숫자/점/부호만 허용 (붙여넣기 포함)
        if (type === "number") {
          if (!/^[0-9.\-]+$/.test(inputText)) {
            event.preventDefault();
            return;
          }
        }
      }
    };

    /**
     * 키다운 단계에서 허용되지 않은 문자를 즉시 차단
     * @date 2025-02-14
     * @description keydown 단계에서 단일 문자 입력 허용 여부를 점검
     * 처리 규칙: 조합 중 입력은 통과시키고, filter/mask/number 규칙 위반 키는 즉시 차단한다.
     * @updated 2026-02-27
    */
    const handleKeyDown = (event) => {
      if (!hasInputConstraint) return;
      if (event.isComposing || event.nativeEvent.isComposing) return;
      const eventKey = event.key;
      if (eventKey.length !== 1) return; // 제어 키는 허용

      if (filter) {
        const allowedKeyPattern = new RegExp(`^[${filter}]+$`);
        if (!allowedKeyPattern.test(eventKey)) {
          event.preventDefault();
          return;
        }
      }

      if (hasStringMask) {
        if (HANGUL_RE.test(eventKey)) {
          event.preventDefault();
          return;
        }
      }

      if (type === "number") {
        if (!/^[0-9.\-]$/.test(eventKey)) {
          event.preventDefault();
          return;
        }
      }
    };

    /**
     * @description change 이벤트에서 조합 상태를 고려해 입력값을 커밋
     * 처리 규칙: 조합 중에는 draft만 유지하고, 조합 종료 후에는 commitValue 결과를 상태/핸들러로 전파한다.
     * @updated 2026-02-27
    */
    const handleChange = (event) => {
      const nativeEvent = event.nativeEvent;
      const nativeInputType = String(nativeEvent?.inputType ?? "");
      const isImeInputType = nativeInputType.includes("composition");
      const rawInputValue = event.target.value;

      if (shouldSkipNextCompositionChange) {
        setShouldSkipNextCompositionChange(false);
        if (isImeInputType && rawInputValue === committedValue) {
          return;
        }
      }

      if (isImeInputType && !isComposing) {
        setIsComposing(true);
      }

      const isTextComposing = Boolean(
          nativeEvent?.isComposing ||
          isComposing ||
          isImeInputType
      );

      // IME(한글 등) 조합 중에는 value를 커밋하지 않는다.
      // 조합 중에 커밋/DOM value를 만지면 자모 분리 현상이 발생할 수 있다.
      if (isTextComposing) {
        if (hasInputConstraint) {

          // 제약이 있을 때, 허용되지 않는 조합 문자열은 화면에 반영하지 않음
          if (!isAllowedDraft(rawInputValue)) {
            if (event.target.value !== committedValue) event.target.value = committedValue; // DOM 즉시 되돌리기
            return;
          }
        }
        setDraftValue(rawInputValue);
        return;
      }

      const committedValue = commitValue(rawInputValue);
      if (typeof committedValue !== "undefined") {
        event.target.value = committedValue;
      }
      const bindingCtx = buildCtx({
        dataKey,
        dataObj,
        source: "user",
        valid: null,
        dirty: true,
      });
      fireValueHandlers({
        onChange,
        onValueChange,
        value: committedValue,
        ctx: bindingCtx,
        event,
      });
    };

    const inputClassName = `
        ${baseClassName}
        ${error ? inputStateMapObj.error : inputStateMapObj.default}
        ${className}
    `.trim();

    let inputType = type;
    if (togglePassword) {
      inputType = showPassword ? "text" : "password";
    } else if (type === "number") {
      inputType = "text";
    }

    return (
      <div className="relative flex items-center">
        {prefix && (
          <div className="absolute left-3 top-1/2 transform -translate-y-1/2">
            {prefix}
          </div>
        )}
        <input
          ref={(el) => {
            inputFocusRef.current = el;
            if (typeof ref === "function") ref(el);
            else if (ref) ref.current = el;
          }}
          type={inputType}
          pattern={type === "number" ? "[0-9]*" : undefined}
          inputMode={type === "number" ? "decimal" : undefined}
          placeholder={placeholder || (hasStringMask ? mask : undefined)}
          value={draftValue ?? committedValue}
          onKeyDown={handleKeyDown}
          onBeforeInput={handleBeforeInput}
          onInput={(event) => {
            const nativeInputType = String(event.nativeEvent?.inputType ?? "");
            if (nativeInputType.includes("composition") && !isComposing) {
              setIsComposing(true);
            }
          }}
          onChange={handleChange}
          onCompositionStart={() => {
            setIsComposing(true);
            setShouldSkipNextCompositionChange(false);
          }}
          onCompositionUpdate={(event) => {
            if (hasInputConstraint) {
              const compositionText = event.currentTarget.value;
              if (!isAllowedDraft(compositionText)) {
                event.preventDefault?.();
                if (event.currentTarget.value !== committedValue) {
                  event.currentTarget.value = committedValue;
                }
              }
            }
          }}
          onCompositionEnd={(event) => {
            setIsComposing(false);
            setShouldSkipNextCompositionChange(true);
            const committedValue = commitValue(event.target.value);
            if (typeof committedValue !== "undefined") {
              event.target.value = committedValue;
            }
            const bindingCtx = buildCtx({
              dataKey,
              dataObj,
              source: "user",
              valid: null,
              dirty: true,
            });
            fireValueHandlers({
              onChange,
              onValueChange,
              value: committedValue,
              ctx: bindingCtx,
              event,
            });
            if (inputFocusRef.current && typeof inputFocusRef.current.focus === "function") {
              try {
                inputFocusRef.current.focus();
                const caretIndex = inputFocusRef.current.value?.length ?? 0;
                if (typeof inputFocusRef.current.setSelectionRange === "function") {
                  inputFocusRef.current.setSelectionRange(caretIndex, caretIndex);
                }
              } catch {}
            }
          }}
          onBlur={(event) => {

            const committedValue = commitValue(event.target.value);
            if (typeof committedValue !== "undefined") {
              event.target.value = committedValue;
            }
            const bindingCtx = buildCtx({
              dataKey,
              dataObj,
              source: "user",
              valid: null,
              dirty: true,
            });
            fireValueHandlers({
              onChange,
              onValueChange,
              value: committedValue,
              ctx: bindingCtx,
              event,
            });
          }}
          className={`
                    ${inputClassName}
                    ${prefix ? "pl-10" : ""}
                    ${suffix ? "pr-10" : ""}
                    ${togglePassword ? "pr-10" : ""}
                `}
          aria-invalid={Boolean(error)}
          {...rest}
        />
        {suffix && (
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
            {suffix}
          </div>
        )}
        {togglePassword && (
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-1/2 transform -translate-y-1/2"
            aria-label={
              showPassword
                ? COMMON_COMPONENT_LANG_KO.input.hidePassword
                : COMMON_COMPONENT_LANG_KO.input.showPassword
            }
            aria-pressed={showPassword}
          >
            <Icon
              icon={showPassword ? "ri:RiEyeLine" : "ri:RiEyeOffLine"}
              className="w-5 h-5 text-gray-400"
            />
          </button>
        )}
      </div>
    );
  }

);

Input.displayName = "Input";

/**
 * @description 엔트리를 외부에 노출
 * 처리 규칙: forwardRef로 정의된 Input 컴포넌트를 default export 한다.
 */
export default Input;
