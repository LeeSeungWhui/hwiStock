/**
 * 파일명: dashboard/components/MaskedValue.jsx
 * 설명: 계정·잔고 등 민감 값 마스킹 표시
 */

const DEFAULT_MASK_CHAR = "•";

const maskText = (rawValue, maskChar = DEFAULT_MASK_CHAR) => {
  const text = String(rawValue ?? "").trim();
  if (!text) return "—";
  if (text.length <= 4) {
    return maskChar.repeat(Math.max(text.length, 4));
  }
  const visibleTail = text.slice(-4);
  const hiddenLength = Math.min(text.length - 4, 12);
  return `${maskChar.repeat(hiddenLength)}${visibleTail}`;
};

/**
 * @description 민감 값을 마스킹해 표시
 * @param {{ value: string|number, label?: string, className?: string, title?: string }} props
 */
const MaskedValue = ({ value, label, className = "", title }) => {
  const maskedText = maskText(value);
  return (
    <span
      className={`font-mono text-sm tracking-tight text-slate-800 ${className}`.trim()}
      title={title || (label ? `${label} (masked)` : "masked value")}
      data-masked="true"
    >
      {maskedText}
    </span>
  );
};

export { maskText };
export default MaskedValue;
