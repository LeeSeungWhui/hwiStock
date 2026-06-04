/**
 * 파일명: Stat.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Stat UI 컴포넌트 구현
 */
import React from 'react';
import { COMMON_COMPONENT_LANG_KO } from '@/app/common/i18n/lang.ko';

/**
 * @description KPI 라벨/값/증감 정보를 카드 형태로 렌더링해 지표 변화를 빠르게 전달
 * 처리 규칙: deltaType(up/down/neutral)에 따라 증감 prefix와 색상을 분기한다.
 * 반환값: 단일 지표를 보여주는 Stat 카드 UI.
 * @param {Object} props
 * @returns {JSX.Element}
 * @updated 2026-02-28
 */
const Stat = ({
  label,
  value,
  delta,
  deltaType = 'neutral',
  icon,
  helpText,
  className = '',
}) => {

  const deltaMetaObj = {
    down: { className: 'text-red-600', prefix: '▼ ' },
    neutral: { className: 'text-gray-500', prefix: '' },
    up: { className: 'text-green-600', prefix: '▲ ' },
  }[deltaType] ?? { className: 'text-gray-500', prefix: '' };
  return (
    <div className={`border rounded-lg p-4 bg-white shadow-sm ${className}`.trim()}>
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-500">{label}</div>
        {icon ? <div aria-hidden>{icon}</div> : null}
      </div>
      <div className="mt-1 flex items-end gap-2">
        <div className="text-2xl font-bold" aria-label={COMMON_COMPONENT_LANG_KO.stat.valueAriaLabel}>{value}</div>
        {delta != null && (
          <div className={`${deltaMetaObj.className} text-sm`} aria-label={COMMON_COMPONENT_LANG_KO.stat.deltaAriaLabel}>{deltaMetaObj.prefix}{delta}</div>
        )}
      </div>
      {helpText && <div className="mt-1 text-xs text-gray-500">{helpText}</div>}
    </div>
  );
};

export default Stat;
