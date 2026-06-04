/**
 * 파일명: Dropdown.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 경량 Dropdown 컴포넌트 (EasyList 지원, 접근성 포함)
 */
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { COMMON_COMPONENT_LANG_KO } from '@/app/common/i18n/lang.ko';
import Icon from './Icon';

/**
 * @description 전달된 목록을 순회 가능한 배열로 정규화. 입력/출력 계약을 함께 명시
 * 처리 규칙: EasyList(forAll), 배열, iterable 순으로 변환을 시도하고 실패 시 빈 배열을 반환한다.
 * @updated 2026-02-27
 */
const readOptionList = (dataList) => {
  if (!dataList) return [];
  if (Array.isArray(dataList)) return dataList;
  if (typeof dataList.forAll === 'function') {
    const resultList = [];
    dataList.forAll((optionItemObj) => resultList.push(optionItemObj));
    return resultList;
  }
  try {
    return Array.from(dataList);
  } catch {
    return [];
  }
};

/**
 * @description 단일/다중 선택 Dropdown UI를 렌더링. 입력/출력 계약을 함께 명시
 * @param {Object} props
 * @returns {JSX.Element}
 */
const Dropdown = ({
  dataList,
  open: openProp,
  defaultOpen = false,
  onOpenChange,
  onSelect,
  trigger,
  labelKey = 'label',
  valueKey = 'value',
  placeholder = COMMON_COMPONENT_LANG_KO.dropdown.placeholder,
  variant = 'outlined',
  size = 'md',
  rounded = 'rounded-lg',
  elevation = 'shadow-md',
  buttonClassName = '',
  iconClassName = '',
  selectedItemClassName = 'text-blue-700',
  showCheck = true,
  side = 'bottom',
  align = 'start',
  className = '',
  menuClassName = '',
  itemClassName = '',
  activeClassName = 'bg-gray-100',
  closeOnSelect = true,
  multiSelect = false,
  disabled = false,
}) => {

  const [openState, setOpenState] = useState(defaultOpen);
  const isOpen = typeof openProp === 'boolean' ? openProp : openState;

  /**
   * @description controlled 여부에 맞춰 open 상태를 갱신
   * 처리 규칙: open prop이 있으면 onOpenChange 콜백만 호출하고, 아니면 내부 state를 변경한다.
   * @updated 2026-02-27
   */
  const setOpen = useCallback((nextOpen) => {
    if (typeof openProp === 'boolean') {
      onOpenChange?.(nextOpen);
      return;
    }
    setOpenState(nextOpen);
  }, [onOpenChange, openProp]);

  const optionList = readOptionList(dataList);
  const [activeIndex, setActiveIndex] = useState(-1);
  const rootRef = useRef(null);
  const effectiveCloseOnSelect = multiSelect ? false : closeOnSelect;

  /**
   * @description 항목 선택을 반영하고 목록 모델(selected)과 외부 콜백을 동기화
   * 부작용: dataList 각 항목의 selected 값, onSelect 호출, closeOnSelect 동작에 영향을 준다.
   * @updated 2026-02-27
  */
  const handleItemActivate = useCallback((optionItemObj) => {
    if (!optionItemObj) return;
    const optionValue = optionItemObj?.get ? optionItemObj.get(valueKey) : optionItemObj?.[valueKey];
    if (dataList?.forAll) {
      dataList.forAll((optionNodeObj) => {
        const nodeValue = optionNodeObj?.get ? optionNodeObj.get(valueKey) : optionNodeObj?.[valueKey];
        const isTarget = String(nodeValue) === String(optionValue);
        if (optionNodeObj?.set) {
          if (multiSelect) {
            optionNodeObj.set('selected', isTarget ? !optionNodeObj.get('selected') : Boolean(optionNodeObj.get('selected')));
          } else {
            optionNodeObj.set('selected', isTarget);
          }
        } else if (optionNodeObj) {
          if (multiSelect) {
            optionNodeObj.selected = isTarget ? !optionNodeObj.selected : Boolean(optionNodeObj.selected);
          } else {
            optionNodeObj.selected = isTarget;
          }
        }
        return optionNodeObj;
      });
    } else if (Array.isArray(dataList)) {
      dataList.forEach((optionNodeObj) => {
        if (!optionNodeObj) return;
        const isTarget = String(optionNodeObj?.[valueKey]) === String(optionValue);
        if (multiSelect) {
          optionNodeObj.selected = isTarget ? !optionNodeObj.selected : Boolean(optionNodeObj.selected);
        } else {
          optionNodeObj.selected = isTarget;
        }
      });
    }
    onSelect?.(optionItemObj);
    if (effectiveCloseOnSelect) setOpen(false);
  }, [dataList, effectiveCloseOnSelect, multiSelect, onSelect, setOpen, valueKey]);

  /**
   * @description isOpen일 때 document keydown으로 Escape·화살표·Enter 내비게이션 처리
   * 처리 규칙: cleanup에서 keydown 리스너를 제거한다.
   */
  useEffect(() => {
    if (!isOpen) return undefined;

    /**
     * @description 열려 있는 메뉴에서 키보드 내비게이션 동작을 반영
     * 처리 규칙: Escape 닫기, ArrowUp/Down 포커스 이동, Enter 선택을 적용한다.
     * @updated 2026-02-27
     */
    const handleDocKeyDown = (event) => {
      if (event.key === 'Escape') {
        setOpen(false);
        return;
      }
      if (!optionList.length) return;
      if (event.key === 'ArrowDown') {
        event.preventDefault();
        setActiveIndex((prevIndex) => (prevIndex + 1) % optionList.length);
      }
      if (event.key === 'ArrowUp') {
        event.preventDefault();
        setActiveIndex((prevIndex) => (prevIndex - 1 + optionList.length) % optionList.length);
      }
      if (event.key === 'Enter' && activeIndex >= 0) {
        handleItemActivate(optionList[activeIndex]);
      }
    };

    /**
     * @description 드롭다운 바깥 영역 클릭 시 메뉴 닫기
     * 처리 규칙: rootRef 외부 mousedown 이벤트에서만 open=false를 반영한다.
     * @updated 2026-02-27
     */
    const handleDocMouseDown = (event) => {
      if (rootRef.current && !rootRef.current.contains(event.target)) setOpen(false);
    };

    document.addEventListener('keydown', handleDocKeyDown);
    document.addEventListener('mousedown', handleDocMouseDown);

    return () => {
      document.removeEventListener('keydown', handleDocKeyDown);
      document.removeEventListener('mousedown', handleDocMouseDown);
    };
  }, [isOpen, optionList, activeIndex, handleItemActivate, setOpen]);

  const sideClassName = {
    bottom: 'top-full mt-2',
    top: 'bottom-full mb-2',
  }[side] ?? '';
  const alignClassName = {
    center: 'left-1/2 -translate-x-1/2',
    end: 'right-0',
    start: 'left-0',
  }[align] ?? 'left-1/2 -translate-x-1/2';
  const positionClassName = `${sideClassName} ${alignClassName}`.trim();

  const selectedItemList = [];
  for (const optionItemObj of optionList) {
    const isSelected = optionItemObj?.get ? optionItemObj.get('selected') : optionItemObj?.selected;
    if (isSelected) selectedItemList.push(optionItemObj);
  }
  const selectedItemObj = selectedItemList.length > 0 ? selectedItemList[0] : null;
  let selectedLabel = null;
  if (!multiSelect) {
    if (selectedItemObj) {
      selectedLabel = selectedItemObj?.get ? selectedItemObj.get(labelKey) : selectedItemObj?.[labelKey];
    }
  } else if (selectedItemList.length === 1) {
    selectedLabel = selectedItemList[0]?.get ? selectedItemList[0].get(labelKey) : selectedItemList[0]?.[labelKey];
  } else if (selectedItemList.length > 1) {
    selectedLabel = `${selectedItemList.length}${COMMON_COMPONENT_LANG_KO.dropdown.multiSelectedSuffix}`;
  }
  let triggerContent = selectedLabel ?? trigger ?? placeholder;
  if (typeof trigger === 'function') {
    triggerContent = trigger({
      selectedItem: selectedItemObj,
      selectedItems: selectedItemList,
      selectedLabel,
    });
  }

  const sizeClassName = {
    lg: 'min-w-[200px] px-4 py-2.5 text-base',
    md: 'min-w-[170px] px-3 py-2 text-sm',
    sm: 'min-w-[140px] px-2.5 py-1.5 text-sm',
  }[size] ?? 'min-w-[170px] px-3 py-2 text-sm';
  const variantClassKey = variant === 'text' ? 'textVariant' : variant;
  const variantClassName = {
    filled: 'bg-gray-50 border border-transparent hover:bg-gray-100 shadow-inner',
    outline: 'bg-white border border-gray-300 hover:bg-gray-50 shadow-sm',
    textVariant: 'bg-transparent border border-transparent hover:bg-gray-50 shadow-none',
  }[variantClassKey] ?? 'bg-white border border-gray-300 hover:bg-gray-50 shadow-sm';
  const triggerClassName = `inline-flex items-center justify-between gap-2 ${sizeClassName} ${rounded} ${variantClassName} focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 ${buttonClassName}`.trim();
  const arrowIconClassName = `text-gray-500 ${iconClassName}`.trim();

  return (
    <div ref={rootRef} className={`relative inline-block ${className}`.trim()}>
      <button
        type="button"
        aria-haspopup="menu"
        aria-expanded={isOpen ? 'true' : 'false'}
        disabled={disabled}
        onClick={() => {
          if (disabled) return;
          setOpen(!isOpen);
        }}
        className={triggerClassName}
      >
        {triggerContent}
        <Icon
          icon="hi:HiChevronDown"
          size="16px"
          className={`${isOpen ? 'rotate-180' : ''} transition-transform ${arrowIconClassName}`}
        />
      </button>

      {isOpen && (
        <ul role="menu" className={`absolute z-30 min-w-56 bg-white border border-gray-200 ${rounded} ${elevation} ${positionClassName} ${menuClassName} transition ease-out duration-150 transform origin-top-left opacity-100 scale-100`.trim()}>
          {optionList.map((optionItemObj, itemIndex) => {
            const label = optionItemObj?.get ? optionItemObj.get(labelKey) : optionItemObj?.[labelKey];
            const optionValue = optionItemObj?.get ? optionItemObj.get(valueKey) : optionItemObj?.[valueKey];
            const isSelected = optionItemObj?.get ? Boolean(optionItemObj.get('selected')) : Boolean(optionItemObj?.selected);
            const disabledItem = optionItemObj?.get ? optionItemObj.get('disabled') : optionItemObj?.disabled;
            const isActive = itemIndex === activeIndex;
            let itemLabelStateKey = 'default';
            if (disabledItem) {
              itemLabelStateKey = 'disabled';
            } else if (isSelected) {
              itemLabelStateKey = 'selected';
            }
            const itemLabelClassMapObj = {
              default: 'text-gray-800',
              disabled: 'text-gray-400',
              selected: selectedItemClassName,
            };
            return (
              <li key={optionValue ?? itemIndex} role="none">
                <button
                  type="button"
                  role={showCheck ? "menuitemcheckbox" : "menuitem"}
                  aria-disabled={disabledItem ? 'true' : 'false'}
                  aria-checked={isSelected ? 'true' : 'false'}
                  className={`w-full text-left px-3 py-2 flex items-center gap-2 text-sm ${isActive || isSelected ? activeClassName : ''} hover:bg-gray-50 disabled:opacity-50 ${itemClassName}`.trim()}
                  disabled={Boolean(disabledItem)}
                  onMouseEnter={() => setActiveIndex(itemIndex)}
                  onFocus={() => setActiveIndex(itemIndex)}
                  onClick={() => {
                    if (disabledItem) return;
                    handleItemActivate(optionItemObj);
                  }}
                >
                  {showCheck && (
                    <Icon
                      icon="md:MdCheck"
                      size="14px"
                      className={`${isSelected ? 'opacity-100 text-blue-600' : 'opacity-0'} transition-opacity`}
                    />
                  )}
                  <span className={itemLabelClassMapObj[itemLabelStateKey]}>{String(label ?? '')}</span>
                </button>
              </li>
            );
          })}
          {optionList.length === 0 && (
            <li role="none"><div className="px-3 py-2 text-sm text-gray-500">{COMMON_COMPONENT_LANG_KO.dropdown.emptyItem}</div></li>
          )}
        </ul>
      )}
    </div>
  );
};

export default Dropdown;
