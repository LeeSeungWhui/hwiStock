/**
 * 파일명: CodeBlock.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 코드 블록 렌더러
 */
import { useEffect, useRef, useState } from 'react';
import LANG_KO from "../../lang.ko";

/**
 * @description 예시 코드 문자열을 하이라이트 블록으로 보여주고 클릭 복사를 지원
 * @param {{ code: string, language?: string }} props
 * @returns {JSX.Element} 코드 블록 UI
 */
const CodeBlock = ({ code, language = 'jsx' }) => {

    const [copied, setCopied] = useState(false);
    const copyResetTimerRef = useRef(null);

    /**
     * @description 현재 코드 문자열을 클립보드에 복사하고 2초간 복사 완료 배지를 표시
     * @returns {void}
     * @updated 2026-02-27
     */
    const handleCodeClick = () => {
        navigator.clipboard.writeText(code);
        setCopied(true);
        clearTimeout(copyResetTimerRef.current);
        copyResetTimerRef.current = setTimeout(() => setCopied(false), 2000);
    };

    /**
     * @description 코드 블록 해제 시 복사 배지 reset 타이머를 정리
     * 처리 규칙: unmount 뒤 copied 상태 업데이트를 방지한다.
     */
    useEffect(() => () => clearTimeout(copyResetTimerRef.current), []);

    return (
        <div className="relative w-full min-w-0">
            <pre
                className="max-w-full overflow-x-auto rounded bg-gray-50 p-2 text-xs font-mono cursor-pointer hover:bg-gray-100"
                onClick={handleCodeClick}
            >
                <code className={`language-${language}`}>
                    {code}
                </code>
            </pre>
            {copied && (
                <div className="absolute top-2 right-2 bg-green-100 text-green-800 px-2 py-1 rounded text-xs">
                    {LANG_KO.view.copyDoneLabel}
                </div>
            )}
        </div>
    );
};

export default CodeBlock;
