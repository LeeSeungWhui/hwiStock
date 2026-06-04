/**
 * 파일명: Icon.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Icon UI 컴포넌트 구현
 */
import { forwardRef } from 'react';
import * as AiIcons from 'react-icons/ai';
import * as BiIcons from 'react-icons/bi';
import * as BsIcons from 'react-icons/bs';
import * as FiIcons from 'react-icons/fi';
import * as HiIcons from 'react-icons/hi';
import * as IoIcons from 'react-icons/io5'; // Ionicons 5
import * as MdIcons from 'react-icons/md';
import * as RiIcons from 'react-icons/ri';

const iconSetMapObj = {
    ai: AiIcons,
    bi: BiIcons,
    bs: BsIcons,
    fi: FiIcons,
    hi: HiIcons,
    io: IoIcons,
    md: MdIcons,
    ri: RiIcons,
};

/**
 * @description 렌더링 및 상호작용 처리
 * 처리 규칙: 전달된 props와 바인딩 값을 기준으로 UI 상태를 계산하고 변경 이벤트를 상위로 전달한다.
 * @updated 2026-02-27
 */
const Icon = forwardRef(({
    icon,
    size = "1em",
    className = "",
    color,
    ariaLabel,
    decorative = true,
    ...props
}, ref) => {

    // icon 형식: "md:Home" 또는 "MdHome" 형식 지원
    const [prefix, name] = icon.includes(':') ? icon.split(':') : [icon.substring(0, 2).toLowerCase(), icon];
    if (!iconSetMapObj[prefix]) {
        return null;
    }

    // 아이콘 이름으로 컴포넌트 찾기
    const IconComponent =
      iconSetMapObj[prefix][name] || iconSetMapObj[prefix][`${prefix.toUpperCase()}${name}`];

    if (!IconComponent) {
        return null;
    }

    const a11y = decorative && !ariaLabel
        ? { 'aria-hidden': true }
        : { role: 'img', 'aria-label': ariaLabel };

    return (
        <IconComponent
            ref={ref}
            size={size}
            className={className}
            color={color}
            {...a11y}
            {...props}
        />
    );
});

Icon.displayName = 'Icon';

export default Icon;
