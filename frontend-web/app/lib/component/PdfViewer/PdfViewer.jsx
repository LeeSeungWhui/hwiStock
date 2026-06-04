"use client";

/**
 * 파일명: PdfViewer.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: PDF 렌더링 컴포넌트
 */

import React, { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import '@react-pdf-viewer/core/lib/styles/index.css';
import '@react-pdf-viewer/default-layout/lib/styles/index.css';
import { defaultLayoutPlugin } from '@react-pdf-viewer/default-layout';
import Empty from '../Empty.jsx';
import Icon from '../Icon';
import { COMMON_COMPONENT_LANG_KO } from '@/app/common/i18n/lang.ko';

// 한글설명: SSR 환경(node-canvas 충돌) 회피를 위해 Viewer/Worker는 클라이언트 전용으로 로드
const Viewer = dynamic(() => import('@react-pdf-viewer/core').then((moduleExports) => moduleExports.Viewer), { ssr: false });
const Worker = dynamic(() => import('@react-pdf-viewer/core').then((moduleExports) => moduleExports.Worker), { ssr: false });

/**
 * @description PDF 파일 소스 렌더링, 로딩 상태, 에러 패널을 통합 제공하는 뷰어 컴포넌트.
 * 처리 규칙: src/objectUrl/viewerError 상태 조합으로 Viewer/Empty/Loading UI를 배타적으로 노출한다.
 * @param {Object} props
 * @returns {JSX.Element}
 * @updated 2026-02-28
 */
const PdfViewer = ({
  src,
  workerSrc = 'https://unpkg.com/pdfjs-dist@3.11.174/build/pdf.worker.min.js',
  withToolbar = true,
  initialPage = 1,
  headers,
  className = '',
  onLoad,
  onError,
}) => {

  let normalizedInitialPage = 1;
  if (typeof initialPage === 'number' && !Number.isNaN(initialPage)) {
    normalizedInitialPage = initialPage < 1 ? 1 : Math.floor(initialPage);
  }
  const [objectUrl, setObjectUrl] = useState(null);
  const [viewerError, setViewerError] = useState(null);
  const [isLoading, setIsLoading] = useState(Boolean(src));
  const [documentState, setDocumentState] = useState(() => ({
    currentPage: normalizedInitialPage,
    totalPages: 0,
    zoom: 1,
  }));

  // 한글설명: 툴바 플러그인은 다른 훅 내부가 아닌 컴포넌트 최상위에서 초기화
  const defaultLayoutPluginInstance = Boolean(withToolbar)
    ? defaultLayoutPlugin({ renderToolbar: (Toolbar) => <Toolbar /> })
    : null;

  const plugins = defaultLayoutPluginInstance ? [defaultLayoutPluginInstance] : [];

  // 한글설명: 플러그인은 동적 import 없이 위에서 동기 생성

  /**
   * @description src 변경 시 objectUrl 생성 및 blob URL revoke
   * 처리 규칙: cleanup에서 blob: URL에 대해 revokeObjectURL을 시도한다.
   */
  useEffect(() => {
    let nextFileUrl = null;
    if (typeof src === 'string') {
      nextFileUrl = src;
    } else if (src instanceof ArrayBuffer) {
      nextFileUrl = URL.createObjectURL(new Blob([src], { type: 'application/pdf' }));
    } else if (src) {
      const isFileLikeSource =
        typeof src === 'object' && (src instanceof Blob || src instanceof File);
      if (isFileLikeSource) nextFileUrl = URL.createObjectURL(src);
    }
    setObjectUrl(nextFileUrl);
    return () => {
      if (nextFileUrl) {
        if (typeof nextFileUrl === 'string') {
          if (nextFileUrl.startsWith('blob:')) {
            try {
              URL.revokeObjectURL(nextFileUrl);
            } catch {

              // 한글설명: revoke 실패는 화면 동작에 영향 없으므로 무시
            }
          }
        }
      }
    };
  }, [src]);

  /**
   * @description objectUrl 변경 시 viewer 로딩·문서 상태 초기화
   * 처리 규칙: objectUrl이 없으면 isLoading=false, 있으면 documentState를 reset한다.
   */
  useEffect(() => {
    if (!objectUrl) {
      setIsLoading(false);
      return;
    }
    setViewerError(null);
    setIsLoading(true);
    setDocumentState({
      currentPage: normalizedInitialPage,
      totalPages: 0,
      zoom: 1,
    });
  }, [objectUrl, normalizedInitialPage]);

  /**
   * @description 문서 로드 성공 이벤트를 반영
   * 처리 규칙: loading을 해제하고 totalPages를 업데이트한 뒤 외부 onLoad 콜백을 호출한다.
   * @updated 2026-02-27
   */
  const handleDocumentLoad = (event) => {
    setIsLoading(false);
    setDocumentState((prev) => ({
      ...prev,
      totalPages: event?.doc?.numPages ?? prev.totalPages,
    }));
    onLoad?.(event);
  };

  /**
   * @description 페이지 변경 이벤트를 상태에 반영
   * 처리 규칙: currentPage를 1-based로 보정해 저장하고 totalPages도 함께 동기화한다.
   * @updated 2026-02-27
   */
  const handlePageChange = (event) => {
    setDocumentState((prev) => ({
      ...prev,
      currentPage: (event?.currentPage ?? 0) + 1,
      totalPages: event?.doc?.numPages ?? prev.totalPages,
    }));
  };

  /**
   * @description 확대/축소 이벤트를 상태에 반영
   * 처리 규칙: 유효한 scale 값이 있을 때만 zoom 상태를 갱신한다.
   * @updated 2026-02-27
   */
  const handleZoom = (event) => {
    if (!event?.scale) return;
    setDocumentState((prev) => ({
      ...prev,
      zoom: event.scale,
    }));
  };

  /**
   * @description 에러 객체에서 HTTP 상태코드를 추출
   * 처리 규칙: `status` 우선, 없으면 `statusCode`를 확인하고 둘 다 없으면 null을 반환한다.
  * @updated 2026-02-27
  */
  const viewerErrorObj = viewerError ?? {};
  let errorStatusCode = null;
  if (typeof viewerErrorObj.status === 'number') {
    errorStatusCode = viewerErrorObj.status;
  } else if (typeof viewerErrorObj.statusCode === 'number') {
    errorStatusCode = viewerErrorObj.statusCode;
  }

  /**
   * @description 에러 객체를 사용자 표시용 문자열로 직렬화하는 메시지 포매터.
   * 처리 규칙: string > message > name 순서로 fallback 하며 모두 없으면 기본 문구를 반환한다.
   * @updated 2026-02-27
   */
  let errorMessage = null;
  if (viewerError) {
    if (typeof viewerError === 'string') errorMessage = viewerError;
    else if (viewerError.message) errorMessage = viewerError.message;
    else if (viewerError.name) errorMessage = `${viewerError.name} error`;
    else errorMessage = COMMON_COMPONENT_LANG_KO.pdfViewer.loadFailedDescription;
  }

  const shouldRenderViewer = Boolean(objectUrl) && !viewerError;
  const showMissingSource = !viewerError && !objectUrl && !isLoading;
  let documentStatusText = COMMON_COMPONENT_LANG_KO.pdfViewer.readyStatus;
  if (viewerError) {
    documentStatusText = COMMON_COMPONENT_LANG_KO.pdfViewer.loadFailedStatus;
  } else if (!objectUrl) {
    documentStatusText = COMMON_COMPONENT_LANG_KO.pdfViewer.sourceUnavailableStatus;
  } else if (isLoading || documentState.totalPages === 0) {
    documentStatusText = COMMON_COMPONENT_LANG_KO.pdfViewer.loadingStatus;
  } else if (documentState.totalPages > 0) {
    const zoomPercent = Math.round(documentState.zoom * 100);
    documentStatusText = COMMON_COMPONENT_LANG_KO.pdfViewer.pageStatusTemplate
      .replace("{totalPages}", String(documentState.totalPages))
      .replace("{currentPage}", String(documentState.currentPage))
      .replace("{zoomPercent}", `${zoomPercent}%`);
  }

  return (
    <div
      className={`relative w-full h-[70vh] border rounded overflow-hidden bg-white ${className}`.trim()}
      role="document"
      aria-label={COMMON_COMPONENT_LANG_KO.pdfViewer.ariaLabel}
      aria-busy={isLoading ? 'true' : 'false'}
      data-page={documentState.currentPage}
      data-page-count={documentState.totalPages}
      data-zoom={documentState.zoom.toFixed(2)}
    >
      <span className="sr-only" aria-live="polite">
        {documentStatusText}
      </span>

      {isLoading && !viewerError && (
        <div className="absolute inset-0 z-10 flex items-center justify-center bg-white/75 backdrop-blur-sm" aria-hidden="true">
          <div className="flex flex-col items-center gap-3 text-gray-600">
            <Icon icon="ri:RiLoader4Line" className="h-6 w-6 animate-spin text-blue-500" size="1.5em" />
            <span className="text-sm font-medium">{COMMON_COMPONENT_LANG_KO.pdfViewer.loadingText}</span>
          </div>
        </div>
      )}

      {viewerError && (
        <div className="flex h-full w-full items-center justify-center bg-gray-50 px-6 py-8">
          <Empty
            className="max-w-sm"
            title={errorStatusCode
              ? `${COMMON_COMPONENT_LANG_KO.pdfViewer.loadFailedTitle} (HTTP ${errorStatusCode})`
              : COMMON_COMPONENT_LANG_KO.pdfViewer.loadFailedTitle}
            description={errorMessage ?? COMMON_COMPONENT_LANG_KO.pdfViewer.loadFailedDescription}
            data-status-code={errorStatusCode ?? undefined}
          />
        </div>
      )}

      {showMissingSource && (
        <div className="flex h-full w-full items-center justify-center bg-gray-50 px-6 py-8">
          <Empty
            className="max-w-sm"
            title={COMMON_COMPONENT_LANG_KO.pdfViewer.missingSourceTitle}
            description={COMMON_COMPONENT_LANG_KO.pdfViewer.missingSourceDescription}
          />
        </div>
      )}

      {shouldRenderViewer && (
        <Worker workerUrl={workerSrc}>
          <Viewer
            fileUrl={objectUrl}
            httpHeaders={headers}
            defaultScale={1}
            initialPage={normalizedInitialPage - 1}
            onDocumentLoad={handleDocumentLoad}
            onDocumentLoadFailed={(event) => {
              setIsLoading(false);
              setViewerError(event?.error ?? event);
              onError?.(event);
            }}
            onPageChange={handlePageChange}
            onZoom={handleZoom}
            plugins={plugins}
          />
        </Worker>
      )}
    </div>
  );
};

/**
 * @description PdfViewer 컴포넌트 엔트리를 외부에 노출
 * 처리 규칙: 상태/이벤트 핸들러가 연결된 PdfViewer 컴포넌트를 default export 한다.
 */
export default PdfViewer;
