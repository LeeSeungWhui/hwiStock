/**
 * 파일명: TopButton.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 문서 상단 이동 버튼
 */
import { useState, useEffect } from 'react';
import * as Lib from '@/app/lib';
import LANG_KO from "../../lang.ko";

/**
 * @description 문서 페이지 우하단에 스크롤-투-탑 버튼을 표시하는 TopButton 컴포넌트를 렌더링. 입력/출력 계약을 함께 명시
 * 처리 규칙: 스크롤 위치가 300px를 넘을 때만 버튼을 노출한다.
 */
const TopButton = () => {
    const [isVisible, setIsVisible] = useState(false);

    /**
     * @description window scroll 이벤트로 300px 초과 시 버튼 표시 상태 갱신
     * 처리 규칙: cleanup에서 scroll 리스너를 제거한다.
     */
    useEffect(() => {

        /**
         * @description 현재 스크롤 위치 기준으로 버튼 표시 상태를 갱신
         * 처리 규칙: `window.scrollY > 300`이면 true, 아니면 false를 설정한다.
         * @updated 2026-02-27
         */
        const toggleVisibility = () => {
            if (window.scrollY > 300) {
                setIsVisible(true);
            } else {
                setIsVisible(false);
            }
        };

        window.addEventListener('scroll', toggleVisibility);
        return () => window.removeEventListener('scroll', toggleVisibility);
    }, []);

    /**
     * @description 클릭 시 페이지 부드러운 최상단 이동
     * 부작용: window.scrollTo({top:0, behavior:'smooth'})가 실행된다.
     * @updated 2026-02-27
     */
    const scrollToTop = () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    };

    return (
        <div
            className={`
                fixed bottom-8 right-8
                transition-opacity duration-200
                ${isVisible ? 'opacity-100' : 'opacity-0 pointer-events-none'}
            `}
        >
            <Lib.Button
                onClick={scrollToTop}
                className="rounded-full w-12 h-12 shadow-lg"
                aria-label={LANG_KO.view.scrollTopAriaLabel}
            >
                <Lib.Icon icon="ri:RiArrowUpLine" size="1.5em" />
            </Lib.Button>
        </div>
    );
};

export default TopButton;
