/**
 * 파일명: Tab.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Tab UI 컴포넌트 구현
 */
import { useState } from 'react';
import { getBoundValue, setBoundValue, buildCtx, fireValueHandlers } from '../binding';

/**
 * @description Tab 자식 슬롯의 title 메타를 유지하면서 콘텐츠 노드만 반환. 입력/출력 계약을 함께 명시
 * @param {{ title: string, children: React.ReactNode }} props
 * @returns {React.ReactNode}
 * @updated 2026-02-27
 */
const TabItem = ({ title, children }) => {

    return children;
};

/**
 * @description 탭 목록 렌더링과 활성 탭 상태 전파를 담당. 입력/출력 계약을 함께 명시
 * 처리 규칙: dataObj/dataKey가 주어지면 controlled 모드로 동작하고, 없으면 내부 state를 사용한다.
 * 부작용: 탭 변경 시 setBoundValue/fireValueHandlers를 통해 외부 바인딩/콜백이 호출될 수 있다.
 * @param {Object} props
 * @returns {JSX.Element}
 * @updated 2026-02-28
 */
const Tab = ({
    dataObj,
    dataKey,
    tabIndex,
    onChange,
    onValueChange,
    className = '',
    children
}) => {

    // controlled/uncontrolled 처리
    const isControlled = dataObj && typeof dataKey !== 'undefined' && dataKey !== null;
    const [internalTab, setInternalTab] = useState(tabIndex || 0);
    const boundValue = isControlled ? getBoundValue(dataObj, dataKey) : undefined;
    let currentTab = internalTab;
    if (isControlled) {
        currentTab = typeof boundValue === 'number' ? boundValue : 0;
    }

    // children이 없거나 배열이 아닐 경우 처리
    const tabItemList = Array.isArray(children) ? children : [children].filter(Boolean);

    /**
     * @description 탭 인덱스를 변경하고 dataObj/콜백으로 변경 이벤트를 전파
     * @param {number} index
     * @param {React.MouseEvent<HTMLButtonElement> | undefined} event
     * @returns {void}
     * @updated 2026-02-27
     */
    const handleTabChange = (index, event) => {
        if (isControlled) {
            setBoundValue(dataObj, dataKey, index, { source: 'user' });
        } else {
            setInternalTab(index);
        }
        const bindingCtx = buildCtx({ dataKey, dataObj, source: 'user', dirty: true, valid: null });
        const emittedEvent = event ?? {
            type: 'tabchange',
            target: { value: index },
            preventDefault() {},
            stopPropagation() {},
        };
        if (event) {
            event.target.value = index;
        }
        fireValueHandlers({
            onChange,
            onValueChange,
            value: index,
            ctx: bindingCtx,
            event: emittedEvent,
        });
    };

    return (
        <div className={`flex flex-col ${className}`}>

            <div className="flex border-b border-gray-200">
                {tabItemList.map((tabItemObj, index) => (
                    <button
                        type="button"
                        key={index}
                        onClick={(event) => handleTabChange(index, event)}
                        className={`
                            px-4 py-2 -mb-px text-sm font-medium inline-flex items-center
                            ${currentTab === index
                                ? 'text-blue-600 border-b-2 border-blue-600'
                                : 'text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            }
                        `}
                    >
                        {tabItemObj.props.title}
                    </button>
                ))}
            </div>


            <div className="py-4">
                {tabItemList[currentTab]}
            </div>
        </div>
    );
};

Tab.Item = TabItem;

/**
 * @description Tab 컴포넌트 진입점 노출
 * 반환값: 탭 전환과 콘텐츠 분기 UI를 제공하는 Tab 컴포넌트.
 * @returns {React.ComponentType}
 */
export default Tab;
