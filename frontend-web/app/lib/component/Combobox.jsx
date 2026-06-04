/**
 * 파일명: Combobox.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: EasyList/EasyObj와 동기화되는 필터 가능한 콤보박스
 */
import {
  forwardRef,
  useEffect,
  useId,
  useRef,
  useState,
} from 'react'

import {
  buildCtx,
  fireValueHandlers,
} from '../binding'
import { useModelValue } from '../hooks/useModelValue'
import Icon from './Icon'

import { COMMON_COMPONENT_LANG_KO } from '@/app/common/i18n/lang.ko'

const STATUS_PRESETS = {
  default: {
    buttonClassName:
      'border border-gray-300 focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900',
    messageClassName: 'text-gray-600',
    ariaLive: 'polite',
  },
  success: {
    buttonClassName:
      'border border-green-400 focus:ring-green-500 focus:border-green-500 bg-white text-gray-900',
    messageClassName: 'text-green-600',
    defaultMessage: COMMON_COMPONENT_LANG_KO.combobox.saved,
    ariaLive: 'polite',
  },
  warning: {
    buttonClassName:
      'border border-yellow-400 focus:ring-yellow-500 focus:border-yellow-500 bg-white text-gray-900',
    messageClassName: 'text-yellow-700',
    defaultMessage: COMMON_COMPONENT_LANG_KO.combobox.needsConfirm,
    ariaLive: 'polite',
  },
  error: {
    buttonClassName:
      'border border-red-400 focus:ring-red-500 focus:border-red-500 bg-white text-gray-900',
    messageClassName: 'text-red-600',
    defaultMessage: COMMON_COMPONENT_LANG_KO.combobox.invalidValue,
    ariaLive: 'assertive',
  },
  info: {
    buttonClassName:
      'border border-blue-300 focus:ring-blue-400 focus:border-blue-400 bg-white text-gray-900',
    messageClassName: 'text-blue-600',
    ariaLive: 'polite',
  },
  loading: {
    buttonClassName:
      'border border-blue-300 focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900 pr-9',
    messageClassName: 'text-blue-600',
    defaultMessage: COMMON_COMPONENT_LANG_KO.combobox.loading,
    ariaLive: 'polite',
  },
  empty: {
    buttonClassName:
      'border border-gray-300 bg-white text-gray-500 focus:ring-blue-400 focus:border-blue-400',
    messageClassName: 'text-gray-500',
    defaultMessage: COMMON_COMPONENT_LANG_KO.combobox.noItems,
    ariaLive: 'assertive',
  },
  disabled: {
    buttonClassName:
      'border border-gray-300 bg-gray-100 text-gray-500 cursor-not-allowed',
    messageClassName: 'text-gray-500',
    ariaLive: 'polite',
  },
}

const HANGUL_CHOSEONG_LIST = [
  '\u3131',
  '\u3132',
  '\u3134',
  '\u3137',
  '\u3138',
  '\u3139',
  '\u3141',
  '\u3142',
  '\u3143',
  '\u3145',
  '\u3146',
  '\u3147',
  '\u3148',
  '\u3149',
  '\u314A',
  '\u314B',
  '\u314C',
  '\u314D',
  '\u314E',
]
const HANGUL_BASE_CODE = 0xac00
const HANGUL_LAST_CODE = 0xd7a3

/**
 * @description 한글 문자열을 초성 검색 가능한 비교 문자열로 바꾸는 변환 유틸
 * 처리 규칙: 완성형 한글은 초성 배열로 치환하고, 비한글 문자는 원문을 유지한다.
 * @updated 2026-02-27
 */
const getChoseongText = (sourceText) => {
  if (!sourceText) return ''
  let choseongText = ''
  for (const sourceChar of String(sourceText)) {
    const sourceCharCode = sourceChar.charCodeAt(0)
    if (sourceCharCode >= HANGUL_BASE_CODE && sourceCharCode <= HANGUL_LAST_CODE) {
      const choseongIndex = Math.floor((sourceCharCode - HANGUL_BASE_CODE) / 588)
      choseongText += HANGUL_CHOSEONG_LIST[choseongIndex] || sourceChar
    } else choseongText += sourceChar
  }
  return choseongText
}

/**
 * @description 검색 비교용 문자열 정규화 유틸(소문자/무공백)
 * 반환값: null/undefined 입력도 안전하게 처리한 비교용 문자열.
 * @updated 2026-02-27
 */
const normalizeSearchText = (inputText) =>
  String(inputText ?? '')
    .toLowerCase()
    .replace(/\s+/g, '')

/**
 * @description 입력 옵션 목록을 콤보박스 내부 표준 스키마로 맞추는 매퍼
 * 처리 규칙: iterable만 허용하고 value/label/selected/placeholder 필드를 생성한다.
 * @updated 2026-02-27
 */
const normalizeOptions = (dataList = [], valueKey, textKey) => {
  if (!Array.isArray(dataList) && typeof dataList?.[Symbol.iterator] !== 'function') {
    return []
  }
  return Array.from(dataList).map((optionItemObj, index) => {
    const optionValue = Array.isArray(optionItemObj?.[valueKey])
      ? optionItemObj?.[valueKey].map((rawItemValue) => String(rawItemValue))
      : String(optionItemObj?.[valueKey] ?? '')
    return {
      key: Object.prototype.hasOwnProperty.call(optionItemObj, valueKey) ? optionItemObj?.[valueKey] : index,
      value: optionValue,
      label: String(optionItemObj?.[textKey] ?? ''),
      selected: Boolean(optionItemObj?.selected),
      placeholder: Boolean(optionItemObj?.placeholder),
    }
  })
}

/**
 * @description 렌더링 및 상호작용 처리
 * 처리 규칙: 전달된 props와 바인딩 값을 기준으로 UI 상태를 계산하고 변경 이벤트를 상위로 전달한다.
 * @updated 2026-02-27
 */
const Combobox = forwardRef(({
    dataList = [],
    valueKey = 'value',
    textKey = 'text',
    dataObj = null,
    dataKey = null,
    value: valueProp,
    defaultValue = '',
    onChange,
    onValueChange,
    placeholder = COMMON_COMPONENT_LANG_KO.combobox.placeholder,
    className = '',
    disabled = false,
    id,
    filterable = true,
    noResultsText = COMMON_COMPONENT_LANG_KO.combobox.noResults,
    multi = false,
    multiSummary = false,
    summaryText = COMMON_COMPONENT_LANG_KO.combobox.summaryText,
    showSelectAll = false,
    selectAllText = COMMON_COMPONENT_LANG_KO.combobox.selectAllText,
    clearAllText = COMMON_COMPONENT_LANG_KO.combobox.clearAllText,
    status: statusProp,
    statusMessage,
    assistiveText,
    error,
    'aria-describedby': ariaDescribedByProp,
    ...rest
  }, ref) => {

  const reactId = useId()
  const buttonId = id || `combobox-${reactId}`
  const listboxId = `${buttonId}-listbox`

  const isControlled = valueProp !== undefined
  const [boundValue, setBoundModelValue] = useModelValue({
    model: dataObj,
    path: dataKey,
  })

  const optionList = normalizeOptions(dataList, valueKey, textKey)
  const placeholderOption = optionList.find((optionItem) => optionItem.placeholder)
  const selectedOptionList = optionList.filter((optionItem) => optionItem.selected)
  const selectedOption = optionList.find((optionItem) => optionItem.selected)

  let sourceValue = ''
  if (multi) {
    if (isControlled) {
      const valueList = Array.isArray(valueProp) ? valueProp : []
      sourceValue = valueList.map((valueItem) => String(valueItem))
    } else if (Array.isArray(boundValue)) {
      sourceValue = boundValue.map((valueItem) => String(valueItem))
    } else if (selectedOptionList.length > 0) {
      sourceValue = selectedOptionList.map((optionItem) => optionItem.value)
    } else if (Array.isArray(defaultValue)) {
      sourceValue = defaultValue.map((valueItem) => String(valueItem))
    } else {
      sourceValue = []
    }
  } else if (isControlled) {
    sourceValue = String(valueProp ?? '')
  } else if (boundValue !== undefined && boundValue !== null) {
    sourceValue = String(boundValue)
  } else if (selectedOption) {
    sourceValue = selectedOption.value
  } else if (defaultValue !== undefined && defaultValue !== null) {
    sourceValue = String(defaultValue)
  } else if (placeholderOption) {
    sourceValue = placeholderOption.value
  }
  const sourceValueKey = JSON.stringify(sourceValue)

  const [innerValue, setInnerValue] = useState(sourceValue)
  let currentValue = isControlled ? sourceValue : innerValue
  if (multi) {
    currentValue = currentValue || []
  } else {
    currentValue = String(currentValue ?? '')
  }
  const selectedValueSet = multi
    ? new Set((currentValue || []).map((valueItem) => String(valueItem)))
    : new Set([String(currentValue ?? '')])

  const isEmptySelection = multi
    ? selectedValueSet.size === 0
    : !currentValue && placeholderOption

  const [isOpen, setIsOpen] = useState(false)
  const [query, setQuery] = useState('')
  const rootRef = useRef(null)

  const normalizedStatus = disabled
    ? 'disabled'
    : statusProp || (error ? 'error' : 'default')
  const statusMeta = STATUS_PRESETS[normalizedStatus] || STATUS_PRESETS.default
  const messageText =
    statusMessage ??
    statusMeta.defaultMessage ??
    (normalizedStatus === 'disabled' ? COMMON_COMPONENT_LANG_KO.combobox.disabled : '')

  const messageId =
    messageText || assistiveText
      ? `${buttonId}-status`
      : undefined

  let filteredOptionList = optionList
  if (filterable && query) {
    const normalizedQuery = normalizeSearchText(query)
    const normalizedQueryInitial = normalizeSearchText(getChoseongText(query))
    const isChoseongQuery = /^[\u3131-\u314E]+$/.test(query)
    filteredOptionList = optionList.filter((optionItem) => {
      const normalizedLabel = normalizeSearchText(optionItem.label)
      const normalizedInitial = normalizeSearchText(getChoseongText(optionItem.label))
      if (isChoseongQuery) return normalizedInitial.includes(normalizedQuery)
      return normalizedLabel.includes(normalizedQuery) || normalizedInitial.includes(normalizedQueryInitial)
    })
  }

  const selectableOptionList = optionList.filter((optionItem) => !optionItem.placeholder)
  let isAllSelected = false
  if (multi) {
    if (selectableOptionList.length > 0) {
      isAllSelected = selectableOptionList.every((optionItem) => selectedValueSet.has(String(optionItem.value)))
    }
  }

  /**
   * @description 현재 선택 값을 dataList selected 플래그에 반영
   * 처리 규칙: 다중 선택은 nextSelectionSet 전체 포함 여부로, 단일 선택은 값 일치 여부로 동기화한다.
   */
  useEffect(() => {
    const nextSelectionSet = multi
      ? new Set((currentValue || []).map((valueItem) => String(valueItem)))
      : new Set([String(currentValue ?? '')])

    /**
     * @description 개별 옵션 selected 값을 nextSelectionSet 기준으로 동기화하는 내부 함수
     * 부작용: 원본 optionItemObj.selected 값을 직접 갱신한다.
     * @updated 2026-02-27
     */
    const syncOptionSelected = (optionItemObj) => {
      const optionValueKey = Array.isArray(optionItemObj?.[valueKey])
        ? optionItemObj?.[valueKey].map((valueItem) => String(valueItem))
        : String(optionItemObj?.[valueKey] ?? '')
      const shouldSelect = Array.isArray(optionValueKey)
        ? optionValueKey.every((selectedValue) => nextSelectionSet.has(selectedValue))
        : nextSelectionSet.has(String(optionValueKey))
      if (optionItemObj.selected !== shouldSelect) optionItemObj.selected = shouldSelect
      return optionItemObj
    }

    if (typeof dataList?.forAll === 'function') {
      dataList.forAll(syncOptionSelected)
    } else if (Array.isArray(dataList)) {
      dataList.forEach(syncOptionSelected)
    }
  }, [currentValue, dataList, multi, valueKey])

  /**
   * @description isOpen일 때 document mousedown/keydown으로 패널 닫기 처리
   * 처리 규칙: cleanup에서 outside-click·Escape 리스너를 제거한다.
   */
  useEffect(() => {
    if (!isOpen) return

    /**
     * @description 컴포넌트 외부 클릭 시 드롭다운 닫기
     * 처리 규칙: rootRef 바깥 mousedown 이벤트에서만 close를 수행한다.
     * @updated 2026-02-27
     */
    const handleDocMouseDown = (event) => {
      if (rootRef.current && !rootRef.current.contains(event.target)) {
        setIsOpen(false)
      }
    }

    /**
     * @description Escape 키 입력으로 드롭다운 닫기
     * 처리 규칙: key 값이 Escape일 때 open=false를 반영한다.
     * @updated 2026-02-27
     */
    const handleDocKeyDown = (event) => {
      if (event.key === 'Escape') setIsOpen(false)
    }

    document.addEventListener('mousedown', handleDocMouseDown)
    document.addEventListener('keydown', handleDocKeyDown)
    return () => {
      document.removeEventListener('mousedown', handleDocMouseDown)
      document.removeEventListener('keydown', handleDocKeyDown)
    }
  }, [isOpen])

  /**
   * @description 패널 닫힘 시 검색어 query 초기화
   * 처리 규칙: isOpen=false 전환마다 setQuery('')를 호출한다.
   */
  useEffect(() => {
    if (!isOpen) setQuery('')
  }, [isOpen])

  /**
   * @description 비제어 모드에서 sourceValue 변경을 innerValue에 동기화
   * 처리 규칙: isControlled=false일 때 JSON 비교 후 변경분만 setInnerValue한다.
   */
  useEffect(() => {
    if (isControlled) return
    setInnerValue((prev) => {
      const prevString = JSON.stringify(prev)
      return prevString === sourceValueKey ? prev : sourceValue
    })
  }, [isControlled, sourceValue, sourceValueKey])

  /**
   * @description EasyList 구독 변경을 내부 선택 값에 반영
   * 처리 규칙: 비제어 모드에서만 subscribe 변경분을 innerValue에 동기화한다.
   */
  useEffect(() => {
    if (!dataList || typeof dataList.subscribe !== 'function') return undefined
    const unsubscribe = dataList.subscribe(() => {
      if (isControlled) return
      const currentOptionList = normalizeOptions(dataList, valueKey, textKey)
      const pickedPlaceholder = currentOptionList.find((optionItem) => optionItem.placeholder)
      const pickedOptionList = currentOptionList.filter((optionItem) => optionItem.selected)
      const pickedOption = currentOptionList.find((optionItem) => optionItem.selected)
      let nextValue = ''
      if (multi) {
        if (Array.isArray(boundValue)) {
          nextValue = boundValue.map((valueItem) => String(valueItem))
        } else if (pickedOptionList.length > 0) {
          nextValue = pickedOptionList.map((optionItem) => optionItem.value)
        } else if (Array.isArray(defaultValue)) {
          nextValue = defaultValue.map((valueItem) => String(valueItem))
        } else {
          nextValue = []
        }
      } else if (boundValue !== undefined && boundValue !== null) {
        nextValue = String(boundValue)
      } else if (pickedOption) {
        nextValue = pickedOption.value
      } else if (defaultValue !== undefined && defaultValue !== null) {
        nextValue = String(defaultValue)
      } else if (pickedPlaceholder) {
        nextValue = pickedPlaceholder.value
      }
      setInnerValue((prev) => {
        const prevString = JSON.stringify(prev)
        const nextString = JSON.stringify(nextValue)
        return prevString === nextString ? prev : nextValue
      })
    })
    return () => unsubscribe?.()
  }, [boundValue, dataList, defaultValue, isControlled, multi, textKey, valueKey])

  /**
   * @description 선택 결과를 정규화하고 내부 상태/바인딩/핸들러 호출을 동기화
   * 부작용: innerValue, dataObj[dataKey], onChange/onValueChange에 반영된다.
   * @updated 2026-02-27
   */
  const commitSelectionValue = (nextSelectionValue, event) => {
    let normalizedValue = String(nextSelectionValue ?? '')
    if (multi) {
      normalizedValue = Array.from(
        new Set(Array.isArray(nextSelectionValue) ? nextSelectionValue.map((valueItem) => String(valueItem)) : []),
      )
    }
    const nextSelectionSet = new Set(multi ? normalizedValue : [normalizedValue])

    /**
     * @description 사용자 선택 결과를 dataList selected 플래그에 즉시 반영
     * 부작용: 원본 optionItemObj.selected 값을 직접 갱신한다.
     * @updated 2026-05-02
     */
    const syncOptionSelected = (optionItemObj) => {
      const optionValueKey = Array.isArray(optionItemObj?.[valueKey])
        ? optionItemObj?.[valueKey].map((valueItem) => String(valueItem))
        : String(optionItemObj?.[valueKey] ?? '')
      const shouldSelect = Array.isArray(optionValueKey)
        ? optionValueKey.every((selectedValue) => nextSelectionSet.has(selectedValue))
        : nextSelectionSet.has(String(optionValueKey))
      if (optionItemObj.selected !== shouldSelect) optionItemObj.selected = shouldSelect
      return optionItemObj
    }

    if (typeof dataList?.forAll === 'function') {
      dataList.forAll(syncOptionSelected)
    } else if (Array.isArray(dataList)) {
      dataList.forEach(syncOptionSelected)
    }

    if (!isControlled) setInnerValue(normalizedValue)
    if (dataObj && dataKey) {
      setBoundModelValue(normalizedValue)
    }

    const bindingCtx = buildCtx({
      dataKey,
      dataObj,
      source: 'user',
      valid: null,
      dirty: true,
    })
    let comboChangeEventObj = { target: { value: normalizedValue } }
    if (event) {
      comboChangeEventObj = { ...event, target: { ...event.target, value: normalizedValue } }
    }
    fireValueHandlers({
      onChange,
      onValueChange,
      value: normalizedValue,
      ctx: bindingCtx,
      event: comboChangeEventObj,
    })
  }

  /**
   * @description 옵션 클릭 이벤트를 단일/다중 선택 모델에 맞춰 반영하는 입력 핸들러
   * 처리 규칙: multi 모드면 토글 집합을 만들고, 단일 모드면 즉시 선택 후 패널을 닫는다.
   * @updated 2026-02-27
   */
  const handleSelect = (optionItemObj) => {
    if (multi) {
      const nextSelectionSet = new Set(selectedValueSet)
      if (nextSelectionSet.has(optionItemObj.value)) nextSelectionSet.delete(optionItemObj.value)
      else nextSelectionSet.add(optionItemObj.value)
      commitSelectionValue(Array.from(nextSelectionSet), null)
    } else {
      commitSelectionValue(optionItemObj.value, null)
      setIsOpen(false)
    }
  }

  const ariaDescribedBy = [ariaDescribedByProp, messageId]
    .filter(Boolean)
    .join(' ') || undefined
  let triggerContent = placeholderOption?.label || placeholder
  if (multi) {
    if (selectedValueSet.size > 0) {
      if (multiSummary) {
        triggerContent = (
          <span className="inline-flex items-center rounded-full bg-blue-50 text-blue-700 text-xs font-medium px-2 py-0.5">
            {summaryText.replace('{count}', String(selectedValueSet.size))}
          </span>
        )
      } else {
        const selectedLabelList = optionList
          .filter((optionItem) => selectedValueSet.has(String(optionItem.value)))
          .map((optionItem) => optionItem.label)
        triggerContent = selectedLabelList.join(', ')
      }
    }
  } else {
    const selectedOptionObj = optionList.find((optionItem) =>
      selectedValueSet.has(String(optionItem.value)),
    )
    triggerContent =
      selectedOptionObj?.label ||
      placeholderOption?.label ||
      placeholder
  }

  return (
    <div
      className={`relative ${className}`.trim()}
      ref={rootRef}
      {...rest}
    >
      <button
        type="button"
        id={buttonId}
        className={`w-full text-left px-3 py-2 text-sm rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-0 transition-colors ${
          statusMeta.buttonClassName
        }`}
        onClick={() => {
          if (disabled) return
          setIsOpen((wasOpen) => !wasOpen)
        }}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-controls={isOpen ? listboxId : undefined}
        disabled={disabled || normalizedStatus === 'disabled'}
        aria-invalid={normalizedStatus === 'error' ? true : undefined}
        aria-busy={normalizedStatus === 'loading' ? true : undefined}
        aria-describedby={ariaDescribedBy}
        ref={ref}
      >
        <span className="flex items-center justify-between gap-2">
          <span>{triggerContent}</span>
          <span className="flex items-center gap-1 text-gray-400">
            {normalizedStatus === 'loading' && (
              <span
                className="h-4 w-4 animate-spin rounded-full border-2 border-blue-300 border-t-transparent"
                aria-hidden="true"
              />
            )}
            <Icon icon="hi:HiChevronDown" className="h-4 w-4" size="1em" />
          </span>
        </span>
      </button>

      {isOpen && (
        <div className="absolute z-20 mt-1 w-full rounded-md border border-gray-200 bg-white shadow-lg">
          {(multi && showSelectAll) && (
            <div className="px-3 py-2 flex items-center justify-between text-sm border-b border-gray-200">
              <span className="text-gray-700">
                {isAllSelected ? clearAllText : selectAllText}
              </span>
              <button
                type="button"
                className="px-2 py-0.5 text-xs rounded border border-gray-300 hover:bg-gray-50"
                onClick={() => {
                  if (isAllSelected) commitSelectionValue([], null)
                  else
                    commitSelectionValue(
                      selectableOptionList.map((optionItem) => String(optionItem.value)),
                      null,
                    )
                }}
              >
                {isAllSelected ? COMMON_COMPONENT_LANG_KO.combobox.toggleClear : COMMON_COMPONENT_LANG_KO.combobox.toggleAll}
              </button>
            </div>
          )}
          {filterable && (
            <div className="p-2 border-b border-gray-200">
              <input
                autoFocus
                className="w-full px-2 py-1 text-sm rounded border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder={COMMON_COMPONENT_LANG_KO.combobox.searchPlaceholder}
                value={query}
                onChange={(changeEvent) => setQuery(changeEvent.target.value)}
              />
            </div>
          )}
          <ul
            id={listboxId}
            role="listbox"
            className="max-h-60 overflow-auto py-1"
            aria-multiselectable={multi || undefined}
          >
            {filteredOptionList.length === 0 && (
              <li className="px-3 py-2 text-sm text-gray-500 select-none">
                {noResultsText}
              </li>
            )}
            {filteredOptionList.map((optionItem) => {
              let isSelected = selectedValueSet.has(String(optionItem.value))
              if (multi) {
                if (Array.isArray(currentValue)) {
                  isSelected = selectedValueSet.has(String(optionItem.value))
                }
              }
              return (
                <li
                  key={optionItem.value}
                  role="option"
                  aria-selected={isSelected}
                  className={`cursor-pointer px-3 py-2 text-sm hover:bg-blue-50 ${
                    isSelected ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-900'
                  }`}
                  onClick={() => handleSelect(optionItem)}
                >
                  {optionItem.label}
                </li>
              )
            })}
          </ul>
        </div>
      )}

      {messageId && (
        <p
          id={messageId}
          className={`mt-1 text-xs ${
            messageText ? statusMeta.messageClassName : 'sr-only'
          }`}
          aria-live={statusMeta.ariaLive || 'polite'}
        >
          {messageText || assistiveText}
          {messageText && assistiveText && (
            <span className="sr-only">{assistiveText}</span>
          )}
        </p>
      )}
    </div>
  )
})

Combobox.displayName = 'Combobox'

export default Combobox
