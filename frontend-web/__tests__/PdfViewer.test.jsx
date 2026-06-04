/**
 * 파일명: PdfViewer.test.jsx
 * 작성자: LSH
 * 갱신일: 2025-11-04
 * 설명: PdfViewer 컴포넌트의 렌더링 및 오류 처리 동작 검증
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import PdfViewer from '../app/lib/component/PdfViewer/PdfViewer.jsx';
import { COMMON_COMPONENT_LANG_KO } from '../app/common/i18n/lang.ko';

const defaultLayoutPluginMock = vi.hoisted(() => vi.fn(() => ({ name: 'default-layout-plugin' })));

vi.mock('next/dynamic', () => {
  const ReactLib = require('react');
  return {
    __esModule: true,
    default: (importer) => {
      const DynamicComponent = (props) => {
        const [Component, setComponent] = ReactLib.useState(null);

        ReactLib.useEffect(() => {
          let mounted = true;
          importer().then((loaded) => {
            if (!mounted) return;
            const Resolved = loaded?.default ?? loaded;
            setComponent(() => Resolved);
          });
          return () => {
            mounted = false;
          };
        }, []);

        if (!Component) return null;
        return <Component {...props} />;
      };
      return DynamicComponent;
    },
  };
});

vi.mock('@react-pdf-viewer/core', () => {
  const ReactLib = require('react');

  const Viewer = ({ fileUrl, onDocumentLoad, onDocumentLoadFailed, onPageChange, onZoom, plugins = [] }) => {
    ReactLib.useEffect(() => {
      if (!fileUrl) return;
      if (fileUrl.includes('error')) {
        onDocumentLoadFailed?.({ error: { message: '403 Forbidden', status: 403 } });
        return;
      }
      onDocumentLoad?.({ doc: { numPages: 3 } });
      onPageChange?.({ currentPage: 0, doc: { numPages: 3 } });
      onZoom?.({ scale: 1.25 });
    }, [fileUrl]);

    return (
      <div data-testid="mock-viewer" data-plugins={plugins.length}>
        mock-viewer
      </div>
    );
  };

  const Worker = ({ children }) => <div data-testid="mock-worker">{children}</div>;

  return {
    __esModule: true,
    Viewer,
    Worker,
  };
});

vi.mock('@react-pdf-viewer/default-layout', () => ({
  __esModule: true,
  defaultLayoutPlugin: defaultLayoutPluginMock,
}));

describe('PdfViewer', () => {
  beforeEach(() => {
    defaultLayoutPluginMock.mockClear();
  });

  it('renders viewer, updates page data, and clears loading state', async () => {
    render(<PdfViewer src="document.pdf" withToolbar={false} />);

    await waitFor(() => {
      const region = screen.getByRole('document', { name: COMMON_COMPONENT_LANG_KO.pdfViewer.ariaLabel });
      expect(region).toHaveAttribute('data-page', '1');
      expect(region).toHaveAttribute('data-page-count', '3');
      expect(region).toHaveAttribute('data-zoom', '1.25');
    });

    await waitFor(() => {
      expect(screen.queryByText(COMMON_COMPONENT_LANG_KO.pdfViewer.loadingText)).not.toBeInTheDocument();
    });
  });

  it('shows empty state with status when document fails to load', async () => {
    render(<PdfViewer src="error-document.pdf" withToolbar={false} />);

    const emptyState = await screen.findByText(new RegExp(COMMON_COMPONENT_LANG_KO.pdfViewer.loadFailedTitle));
    expect(emptyState).toBeInTheDocument();

    await waitFor(() => {
      const viewerRegion = screen.getByRole('document', { name: COMMON_COMPONENT_LANG_KO.pdfViewer.ariaLabel });
      expect(viewerRegion).toHaveAttribute('aria-busy', 'false');
    });

    expect(emptyState.closest('[data-status-code]')).toHaveAttribute('data-status-code', '403');
  });

  it('binds default-layout toolbar plugin when enabled', async () => {
    render(<PdfViewer src="toolbar.pdf" />);

    await waitFor(() => {
      expect(defaultLayoutPluginMock).toHaveBeenCalled();
    });

    const viewer = await waitFor(() => screen.getByTestId('mock-viewer'));
    expect(viewer.dataset.plugins).toBe('1');
  });
});
