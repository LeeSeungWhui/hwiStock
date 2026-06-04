/**
 * 파일명: Select.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: EasyObj/EasyList 바운드 및 컨트롤드 모드를 모두 지원하는 Select 컴포넌트
 */
import { forwardRef, useEffect, useId, useState } from 'react'
import { buildCtx, fireValueHandlers } from '../binding'
import { useModelValue } from '../hooks/useModelValue'
import Icon from './Icon'
import { COMMON_COMPONENT_LANG_KO } from '@/app/common/i18n/lang.ko'

const STATUS_PRESETS = {
  default: {
    selectClassName: 'border border-gray-300 focus:ring-blue-500 focus:border-blue-500',
    messageClassName: 'text-gray-600',
    ariaLive: 'polite',
  },
  success: {
    selectClassName:
      'border border-green-400 focus:ring-green-500 focus:border-green-500',
    messageClassName: 'text-green-600',
    defaultMessage: COMMON_COMPONENT_LANG_KO.select.saved,
    ariaLive: 'polite',
  },
  warning: {
    selectClassName:
      'border border-yellow-400 focus:ring-yellow-500 focus:border-yellow-500',
    messageClassName: 'text-yellow-700',
    defaultMessage: COMMON_COMPONENT_LANG_KO.select.needsConfirm,
    ariaLive: 'polite',
  },
  error: {
    selectClassName: 'border border-red-400 focus:ring-red-500 focus:border-red-500',
    messageClassName: 'text-red-600',
    defaultMessage: COMMON_COMPONENT_LANG_KO.select.invalidValue,
    ariaLive: 'assertive',
  },
  info: {
    selectClassName: 'border border-blue-300 focus:ring-blue-400 focus:border-blue-400',
    messageClassName: 'text-blue-600',
    ariaLive: 'polite',
  },
  loading: {
    selectClassName:
      'border border-blue-300 focus:ring-blue-500 focus:border-blue-500 pr-9',
    messageClassName: 'text-blue-600',
    defaultMessage: COMMON_COMPONENT_LANG_KO.select.loading,
    ariaLive: 'polite',
  },
  empty: {
    selectClassName:
      'border border-gray-300 bg-white text-gray-500 focus:ring-blue-400 focus:border-blue-400',
    messageClassName: 'text-gray-500',
    defaultMessage: COMMON_COMPONENT_LANG_KO.select.noItems,
    ariaLive: 'assertive',
  },
  disabled: {
    selectClassName:
      'bg-gray-100 text-gray-500 border border-gray-300 cursor-not-allowed',
    messageClassName: 'text-gray-500',
    ariaLive: 'polite',
  },
}

/**
 * @description 입력 옵션 목록을 Select 내부 표준 구조로 정규화. 입력/출력 계약을 함께 명시
 * 반환값: `{key,value,label,placeholder,selected}` 형태의 옵션 배열.
 * @updated 2026-02-27
 */
const normalizeOptions = (dataList = [], valueKey, textKey) => {
  if (!Array.isArray(dataList) && typeof dataList?.[Symbol.iterator] !== 'function') {
    return []
  }
  return Array.from(dataList).map((optionItemObj, index) => ({
    key: Object.prototype.hasOwnProperty.call(optionItemObj, valueKey) ? optionItemObj[valueKey] : index,
    value: String(optionItemObj?.[valueKey] ?? ''),
    label: String(optionItemObj?.[textKey] ?? ''),
    placeholder: Boolean(optionItemObj?.placeholder),
    selected: Boolean(optionItemObj?.selected),
  }))
}

/**
 * @description 렌더링 및 상호작용 처리
 * 처리 규칙: 전달된 props와 바인딩 값을 기준으로 UI 상태를 계산하고 변경 이벤트를 상위로 전달한다.
 * @updated 2026-02-27
 */
const Select = forwardRef(({
    dataList = [],
    valueKey = 'value',
    textKey = 'text',
    dataObj = null,
    dataKey = null,
    value: valueProp,
    defaultValue = '',
    placeholder,
    status: statusProp,
    statusMessage,
    assistiveText,
    disabled = false,
    className = '',
    id,
    onChange,
    onValueChange,
    error,
    'aria-describedby': ariaDescribedByProp,
    ...rest
  }, ref) => {

  const isControlled = valueProp !== undefined
  const reactId = useId()
  const selectId = id || `select-${reactId}`
  const [boundValue, setBoundModelValue] = useModelValue({
    model: dataObj,
    path: dataKey,
  })

  const optionList = normalizeOptions(dataList, valueKey, textKey)
  const placeholderOption = optionList.find((optionItem) => optionItem.placeholder)

  const selectedOption =
    optionList.find((optionItem) => optionItem.selected)
  const hasBoundModelValue =
    dataObj && dataKey && boundValue !== undefined && boundValue !== null
  let sourceValue = ''
  if (isControlled) {
    sourceValue = String(valueProp ?? '')
  } else if (hasBoundModelValue) {
    sourceValue = String(boundValue)
  } else if (selectedOption) {
    sourceValue = selectedOption.value
  } else if (defaultValue !== undefined && defaultValue !== null) {
    sourceValue = String(defaultValue)
  } else if (placeholderOption) {
    sourceValue = placeholderOption.value
  }

  const [innerValue, setInnerValue] = useState(sourceValue)
  const currentValue = isControlled ? sourceValue : innerValue

  /**
   * @description currentValue 변경 시 option selected 플래그 재계산
   * 처리 규칙: dataList.forAll/forEach로 valueKey 일치 항목만 selected=true로 맞춘다.
   */
  useEffect(() => {
    const selectedValue = String(currentValue ?? '')

    /**
     * @description 현재 값과 일치하는 항목의 selected 플래그를 재계산. 입력/출력 계약을 함께 명시
     * 부작용: optionItemObj.selected 값을 직접 갱신한다.
     * @updated 2026-02-27
     */
    const syncOptionSelected = (optionItemObj) => {
      const isNextSelected = String(optionItemObj?.[valueKey] ?? '') === selectedValue
      if (optionItemObj.selected !== isNextSelected) optionItemObj.selected = isNextSelected
      return optionItemObj
    }

    if (typeof dataList?.forAll === 'function') {
      dataList.forAll(syncOptionSelected)
    } else if (Array.isArray(dataList)) {
      dataList.forEach(syncOptionSelected)
    }
  }, [dataList, valueKey, currentValue])

  /**
   * @description 비제어 모드에서 sourceValue 변경을 innerValue에 동기화
   * 처리 규칙: isControlled=false일 때만 setInnerValue로 외부 값을 반영한다.
   */
  useEffect(() => {
    if (isControlled) return
    setInnerValue((prev) => (prev === sourceValue ? prev : sourceValue))
  }, [isControlled, sourceValue])

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
      const pickedOption =
        currentOptionList.find((optionItem) => optionItem.selected)
      const hasBoundValueNow =
        dataObj && dataKey && boundValue !== undefined && boundValue !== null
      let nextValue = ''
      if (hasBoundValueNow) {
        nextValue = String(boundValue)
      } else if (pickedOption) {
        nextValue = pickedOption.value
      } else if (defaultValue !== undefined && defaultValue !== null) {
        nextValue = String(defaultValue)
      } else if (pickedPlaceholder) {
        nextValue = pickedPlaceholder.value
      }
      setInnerValue((prev) => (prev === nextValue ? prev : nextValue))
    })
    return () => unsubscribe?.()
  }, [boundValue, dataKey, dataList, dataObj, defaultValue, isControlled, textKey, valueKey])

  const normalizedStatus = disabled
    ? 'disabled'
    : statusProp || (error ? 'error' : 'default')
  const statusMeta =
    STATUS_PRESETS[normalizedStatus] || STATUS_PRESETS.default
  const messageText =
    statusMessage ??
    statusMeta.defaultMessage ??
    (normalizedStatus === 'disabled' ? COMMON_COMPONENT_LANG_KO.select.disabled : '')

  const isPlaceholderSelected =
    placeholderOption &&
    (!currentValue || currentValue === placeholderOption.value)

  const messageId =
    messageText || assistiveText
      ? `${selectId}-status`
      : undefined
  const ariaDescribedBy =
    [ariaDescribedByProp, messageId].filter(Boolean).join(' ') || undefined

  /**
   * @description 선택 변경 이벤트를 상태/바인딩/핸들러 규약으로 동기화
   * 처리 규칙: 내부 값 업데이트 후 dataList selected 플래그, dataObj[dataKey], fireValueHandlers 순서로 반영한다.
   * @updated 2026-02-27
   */
  const handleChange = (event) => {
    const nextValue = event.target.value
    if (!isControlled) setInnerValue(nextValue)
    if (typeof dataList?.forAll === 'function') {
      dataList.forAll((optionItemObj) => {
        const isSelected = String(optionItemObj?.[valueKey] ?? '') === String(nextValue)
        if (optionItemObj.selected !== isSelected) optionItemObj.selected = isSelected
        return optionItemObj
      })
    } else if (Array.isArray(dataList)) {
      dataList.forEach((optionItemObj) => {
        optionItemObj.selected = String(optionItemObj?.[valueKey] ?? '') === String(nextValue)
      })
    }
    if (dataObj && dataKey) {
      setBoundModelValue(nextValue)
    }
    const bindingCtx = buildCtx({
      dataKey,
      dataObj,
      source: 'user',
      valid: null,
      dirty: true,
    })
    const selectChangeEventObj = {
      ...event,
      target: { ...event.target, value: nextValue },
    }
    fireValueHandlers({
      onChange,
      onValueChange,
      value: nextValue,
      ctx: bindingCtx,
      event: selectChangeEventObj,
    })
  }

  const baseClassName =
    'block w-full px-3 py-2 text-sm rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-0 appearance-none bg-white transition-colors'
  const selectClassName = [
    baseClassName,
    statusMeta.selectClassName,
    isPlaceholderSelected ? 'text-gray-400' : 'text-gray-900',
    className,
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div className="relative">
      <select
        ref={ref}
        id={selectId}
        value={currentValue}
        onChange={handleChange}
        disabled={disabled || normalizedStatus === 'disabled'}
        className={selectClassName}
        aria-invalid={normalizedStatus === 'error' ? true : undefined}
        aria-busy={normalizedStatus === 'loading' ? true : undefined}
        aria-describedby={ariaDescribedBy}
        {...rest}
      >
        {placeholder &&
          !optionList.some((optionItem) => optionItem.placeholder) && (
            <option value="" className="text-gray-400">
              {placeholder}
            </option>
          )}
        {optionList.map((optionItem) => (
          <option
            key={optionItem.key}
            value={optionItem.value}
            className={optionItem.placeholder ? 'text-gray-400' : 'text-gray-900'}
          >
            {optionItem.label}
          </option>
        ))}
      </select>
      <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
        {normalizedStatus === 'loading' ? (
          <span
            className="h-4 w-4 animate-spin rounded-full border-2 border-blue-300 border-t-transparent"
            aria-hidden="true"
          />
        ) : (
          <Icon icon="hi:HiChevronDown" className="h-5 w-5 text-gray-400" size="1.25em" />
        )}
      </div>
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

Select.displayName = 'Select'

export default Select
