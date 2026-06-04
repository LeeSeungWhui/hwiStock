/**
 * 파일명: Pagination.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 페이지 이동 내비게이션 컴포넌트 (접근성 포함)
 */
import React from 'react';
import { COMMON_COMPONENT_LANG_KO } from '@/app/common/i18n/lang.ko';
import Icon from './Icon';

const ARROW_ROTATE_CLASS_MAP = {
  down: 'rotate-90',
  left: 'rotate-180',
  right: '',
  up: '-rotate-90',
};

const DOUBLE_ARROW_ROTATE_CLASS_MAP = {
  left: 'rotate-180',
  right: '',
};

/**
 * @description 를 렌더링. 입력/출력 계약을 함께 명시
 * 반환값: 방향(dir)에 따라 회전이 적용된 단일 화살표 SVG.
 * @updated 2026-02-27
 */
const Arrow = ({ direction, className = '' }) => {

  const rotateClassName = ARROW_ROTATE_CLASS_MAP[direction] ?? '';
  return (
    <Icon icon="hi:HiChevronRight" size="16px" className={`${rotateClassName} ${className}`} />
  );
};

/**
 * @description 를 렌더링. 입력/출력 계약을 함께 명시
 * 반환값: 처음/마지막 페이지 이동 버튼에 쓰는 이중 화살표 SVG.
 * @updated 2026-02-27
 */
const DoubleArrow = ({ direction = 'right', className = '' }) => {

  const rotateClassName = DOUBLE_ARROW_ROTATE_CLASS_MAP[direction] ?? '';
  return (
    <Icon icon="hi:HiChevronDoubleRight" size="18px" className={`${rotateClassName} ${className}`} />
  );
};

/**
 * @description 페이지 번호/이동 버튼을 렌더링. 입력/출력 계약을 함께 명시
 * @param {Object} props
 * @returns {JSX.Element}
 */
const Pagination = ({
  page,
  pageCount,
  onChange,
  maxButtons = 7,
  className = '',
  showEdges = true,
}) => {

  const tokenList = [];

  if (pageCount <= maxButtons) {
    for (let pageNo = 1; pageNo <= pageCount; pageNo += 1) {
      tokenList.push(pageNo);
    }
  } else {
    const reservedEdgeCount = showEdges ? 2 : 0;
    const windowSize = Math.max(3, maxButtons - reservedEdgeCount);
    const startFloor = showEdges ? 2 : 1;
    const endCeil = showEdges ? pageCount - 1 : pageCount;

    let windowStartPage = Math.max(startFloor, page - Math.floor((windowSize - 1) / 2));
    let windowEndPage = Math.min(endCeil, windowStartPage + windowSize - 1);
    windowStartPage = Math.max(startFloor, Math.min(windowStartPage, windowEndPage - windowSize + 1));

    if (showEdges) tokenList.push(1);
    if (showEdges && windowStartPage > 2) tokenList.push('…');
    for (let pageNo = windowStartPage; pageNo <= windowEndPage; pageNo += 1) {
      tokenList.push(pageNo);
    }
    if (showEdges && windowEndPage < pageCount - 1) tokenList.push('…');
    if (showEdges) tokenList.push(pageCount);
  }

  const buttonClassName = 'rounded-full w-8 h-8 flex items-center justify-center text-sm transition-colors';
  const navClassName = 'rounded-full w-8 h-8 flex items-center justify-center text-gray-600 hover:text-gray-800 disabled:opacity-40 disabled:cursor-not-allowed';
  const selectedClassName = 'bg-blue-100 text-blue-700 font-semibold ring-1 ring-blue-300';
  const normalClassName = 'text-gray-700 hover:bg-gray-100';

  return (
    <div className={`inline-flex items-center gap-1 ${className}`} role="navigation" aria-label={COMMON_COMPONENT_LANG_KO.pagination.navigationAriaLabel}>
      <button type="button" className={navClassName} onClick={() => onChange?.(1)} disabled={page === 1} aria-label={COMMON_COMPONENT_LANG_KO.pagination.firstPageAriaLabel}>
        <DoubleArrow direction="left" />
      </button>
      <button type="button" className={navClassName} onClick={() => onChange?.(Math.max(1, page - 1))} disabled={page === 1} aria-label={COMMON_COMPONENT_LANG_KO.pagination.previousPageAriaLabel}>
        <Arrow direction="left" />
      </button>
      {tokenList.map((pageToken, pageTokenIndex) => {
        if (typeof pageToken === 'number') {
          return (
            <button
              type="button"
              key={pageToken}
              className={`${buttonClassName} ${pageToken === page ? selectedClassName : normalClassName}`}
              aria-current={pageToken === page ? 'page' : undefined}
              onClick={() => onChange?.(pageToken)}
            >
              {pageToken}
            </button>
          );
        }
        return <span key={`ellipsis-${pageTokenIndex}`} className="px-2 text-gray-400 select-none" aria-hidden>…</span>;
      })}
      <button type="button" className={navClassName} onClick={() => onChange?.(Math.min(pageCount, page + 1))} disabled={page === pageCount} aria-label={COMMON_COMPONENT_LANG_KO.pagination.nextPageAriaLabel}>
        <Arrow direction="right" />
      </button>
      <button type="button" className={navClassName} onClick={() => onChange?.(pageCount)} disabled={page === pageCount} aria-label={COMMON_COMPONENT_LANG_KO.pagination.lastPageAriaLabel}>
        <DoubleArrow direction="right" />
      </button>
    </div>
  );
};

/**
 * @description 접근성 라벨과 페이지 윈도우 계산을 포함한 Pagination 컴포넌트를 외부에 노출
 * 반환값: Pagination 컴포넌트 export.
 */
export default Pagination;
