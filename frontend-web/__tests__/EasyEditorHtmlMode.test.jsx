/**
 * 파일명: EasyEditorHtmlMode.test.jsx
 * 작성자: LSH
 * 갱신일: 2025-11-04
 * 설명: EasyEditor HTML 모드 전환 및 내용 동기화 시나리오 검증
 */

import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

let EasyEditor;
let editorStub;

const createEditorStub = (initialHtml = '<p>Hello</p>') => {
  const stub = {
    content: initialHtml,
    getHTML: vi.fn(() => stub.content),
    setEditable: vi.fn(),
    getAttributes: vi.fn(() => ({})),
    isActive: vi.fn(() => false),
    commands: {
      setContent: vi.fn((nextHtml) => {
        stub.content = nextHtml;
      }),
    },
  };

  const chainApi = {
    focus: () => chainApi,
    toggleBold: () => chainApi,
    toggleItalic: () => chainApi,
    toggleUnderline: () => chainApi,
    unsetLink: () => chainApi,
    extendMarkRange: () => chainApi,
    setLink: () => chainApi,
    setImage: () => chainApi,
    insertContent: () => chainApi,
    setMark: () => chainApi,
    removeEmptyTextStyle: () => chainApi,
    setColor: () => chainApi,
    setTextAlign: () => chainApi,
    run: () => true,
  };

  stub.chain = () => chainApi;

  return stub;
};

const mockUseEasyUpload = vi.fn(() => ({
  uploadImage: vi.fn(),
  uploadFile: vi.fn(),
  alertElement: null,
}));

const mockUseEasyEditor = vi.fn(() => {
  editorStub = createEditorStub();
  return { editor: editorStub };
});

vi.mock('../app/lib/component/EasyEditor/useEasyUpload', () => ({
  __esModule: true,
  default: mockUseEasyUpload,
}));

vi.mock('@tiptap/react', () => ({
  __esModule: true,
  EditorContent: ({ editor, ...props }) => <div data-testid="editor-content" data-editor={Boolean(editor)} {...props} />,
}));

vi.mock('../app/lib/component/EasyEditor/useEditor', () => ({
  __esModule: true,
  default: mockUseEasyEditor,
}));

beforeAll(async () => {
  ({ default: EasyEditor } = await import('../app/lib/component/EasyEditor/EasyEditor.jsx'));
});

describe('EasyEditor HTML mode', () => {
  beforeEach(() => {
    editorStub = null;
    mockUseEasyEditor.mockImplementation(() => {
      if (!editorStub) {
        editorStub = createEditorStub();
      }
      return { editor: editorStub };
    });
  });

  afterEach(() => {
    mockUseEasyEditor.mockReset();
    mockUseEasyUpload.mockClear();
  });

  it('syncs textarea edits back to the editor content', async () => {
    render(<EasyEditor value="<p>Hello</p>" serialization="html" />);

    const htmlButton = screen.getByRole('button', { name: /HTML/i });
    fireEvent.click(htmlButton);

    const textarea = screen.getByRole('textbox');
    expect(textarea.value).toBe('<p>Hello</p>');

    fireEvent.change(textarea, { target: { value: '<p>Updated</p>' } });

    const editorButton = screen.getByRole('button', { name: /Editor|에디터/ });
    fireEvent.click(editorButton);

    expect(screen.queryByDisplayValue('<p>Updated</p>')).not.toBeInTheDocument();
    await waitFor(() => {
      expect(editorStub.getHTML()).toBe('<p>Updated</p>');
    });
  });
});
