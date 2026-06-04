"use client";

/**
 * 파일명: EasyEditor.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: EasyEditor UI 컴포넌트
 */

import { useRef, useState, useEffect } from 'react';
import { EditorContent } from '@tiptap/react';
import clsx from 'clsx';
import useEasyEditor from './useEditor';
import useEditorUpload from './useEditorUpload';
import { COMMON_COMPONENT_LANG_KO } from '@/app/common/i18n/lang.ko';

/**
 * @description 에디터 툴바 버튼의 활성/비활성 스타일과 접근성 속성을 일관되게 렌더링. 입력/출력 계약을 함께 명시
 * 처리 규칙: disabled=true면 클릭 핸들러를 연결하지 않고 aria-pressed/aria-disabled를 유지한다.
 * @param {Object} props
 * @returns {JSX.Element}
 * @updated 2026-02-27
 */
const ToolbarButton = ({ active, label, onClick, children, disabled }) => (

  <button
    type="button"
    aria-label={label}
    aria-pressed={active}
    aria-disabled={disabled || undefined}
    disabled={disabled}
    className={clsx(
      'px-2 py-1 text-sm rounded transition-colors',
      disabled && 'opacity-40 cursor-not-allowed',
      !disabled && (active
        ? 'bg-blue-100 text-blue-600 border border-blue-200'
        : 'text-gray-600 hover:bg-gray-100 border border-transparent'),
    )}
    onClick={disabled ? undefined : onClick}
  >
    {children}
  </button>
);

const editorRootClassName =
  'flex flex-col border rounded-lg bg-white shadow-sm focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500 transition';

const editorBodyClassName =
  'prose max-w-none min-h-[200px] p-4 outline-none text-gray-900';

const toolbarClassName =
  'flex flex-wrap items-center gap-2 border-b px-3 py-2 bg-gray-50';

const statusClassMap = {
  idle: '',
  loading: 'opacity-70 pointer-events-none',
  error: 'border-red-300 focus-within:ring-red-500',
  success: 'border-green-300 focus-within:ring-green-500',
};

const fontSizeOptionList = [
  { label: COMMON_COMPONENT_LANG_KO.easyEditor.fontSizeDefault, value: 'default' },
  { label: '12px', value: '12px' },
  { label: '14px', value: '14px' },
  { label: '16px', value: '16px' },
  { label: '20px', value: '20px' },
  { label: '24px', value: '24px' },
];

const alignmentList = [
  { label: COMMON_COMPONENT_LANG_KO.easyEditor.alignLeft, value: 'left', icon: 'L' },
  { label: COMMON_COMPONENT_LANG_KO.easyEditor.alignCenter, value: 'center', icon: 'C' },
  { label: COMMON_COMPONENT_LANG_KO.easyEditor.alignRight, value: 'right', icon: 'R' },
  { label: COMMON_COMPONENT_LANG_KO.easyEditor.alignJustify, value: 'justify', icon: 'J' },
];

const EMPTY_EXTENSION_LIST = [];

/**
 * @description Tiptap 기반 에디터 본문/툴바/업로드 동작을 통합해 렌더링. 입력/출력 계약을 함께 명시
 * 처리 규칙: readOnly/HTML 모드 상태에 따라 편집 가능 여부와 툴바 동작을 동기화한다.
 * 부작용: 이미지/파일 업로드 핸들러 호출과 dataObj(onChange/onValueChange) 반영이 발생할 수 있다.
 * @returns {JSX.Element}
 * @updated 2026-02-27
 */
const EasyEditor = ({
  dataObj,
  dataKey,
  value,
  onChange,
  onValueChange,
  placeholder = COMMON_COMPONENT_LANG_KO.easyEditor.placeholder,
  readOnly = false,
  className = '',
  status = 'idle',
  invalid = false,
  helperText,
  label,
  id,
  name,
  serialization = 'json',
  extensions,
  autofocus = false,
  onUploadImage,
  onUploadFile,
  imageUploadUrl,
  fileUploadUrl,
  toolbar = true,
  minHeight = '240px',
}) => {

  const fileInputRef = useRef(null);
  const attachmentInputRef = useRef(null);
  const extensionList = extensions ?? EMPTY_EXTENSION_LIST;

  const { uploadImage, uploadFile, alertElement } = useEditorUpload({ imageUploadUrl, fileUploadUrl });

  const { editor } = useEasyEditor({
    dataObj,
    dataKey,
    value,
    onChange,
    onValueChange,
    placeholder,
    readOnly,
    serialization,
    extensions: extensionList,
    autofocus,
  });

  const [mode, setMode] = useState('editor');
  const [htmlDraft, setHtmlDraft] = useState('');
  const [uploadErrorText, setUploadErrorText] = useState('');

  const isHtmlMode = mode === 'html';
  const toolbarDisabled = readOnly || isHtmlMode;

  /**
   * @description html 모드 전환 시 editor HTML을 htmlDraft 상태에 동기화
   * 처리 규칙: mode/editor 변경마다 setHtmlDraft(editor.getHTML())를 호출한다.
   */
  useEffect(() => {
    if (!editor) return;
    if (mode === 'html') {
      setHtmlDraft(editor.getHTML());
    }
  }, [mode, editor]);

  /**
   * @description readOnly 변경 시 TipTap editor editable 상태 동기화
   * 처리 규칙: editor.setEditable(!readOnly)를 readOnly 의존성마다 호출한다.
   */
  useEffect(() => {
    if (!editor) return;
    editor.setEditable(!readOnly);
  }, [editor, readOnly]);

  /**
   * @description htmlDraft 변경을 html 모드 editor 본문에 반영
   * 처리 규칙: mode=html일 때만 setContent(htmlDraft)로 사용자 편집을 동기화한다.
   */
  useEffect(() => {
    if (!editor || mode !== 'html') return;
    editor.commands.setContent(htmlDraft || '<p></p>', false);
  }, [htmlDraft, mode, editor]);

  /**
   * @description 툴바 토글 명령의 editor chain 전달
   * 처리 규칙: 에디터가 없거나 툴바가 잠겨 있으면 명령을 실행하지 않는다.
   */
  const handleToggle = (command) => {
    if (!editor || toolbarDisabled) return;
    editor.chain().focus()[command]().run();
  };

  /**
   * @description 링크 입력 프롬프트 결과의 editor link mark 반영
   * 처리 규칙: 빈 문자열은 링크 제거, 취소는 상태 유지로 처리한다.
   */
  const handleSetLink = () => {
    if (!editor || toolbarDisabled) return;
    const previousLinkUrl = editor.getAttributes('link')?.href;
    const linkUrl = window.prompt(COMMON_COMPONENT_LANG_KO.easyEditor.promptLinkUrl, previousLinkUrl || 'https://');
    if (linkUrl === null) return;
    if (linkUrl === '') {
      editor.chain().focus().unsetLink().run();
      return;
    }
    editor.chain().focus().extendMarkRange('link').setLink({ href: linkUrl }).run();
  };

  const imageUploadHandler = onUploadImage ?? uploadImage;
  const fileUploadHandler = onUploadFile ?? uploadFile;

  /**
   * @description 이미지 파일 선택 결과의 업로드와 editor image 노드 삽입
   * 처리 규칙: 처리 후 input 값을 비워 같은 파일을 다시 선택할 수 있게 한다.
   */
  const handleImageSelect = async (event) => {
    if (!editor || readOnly) return;
    const selectedFileList = Array.from(event.target.files || []);
    if (!selectedFileList.length) return;
    setUploadErrorText('');

    for (const file of selectedFileList) {
      try {
        const imageUrl = await imageUploadHandler(file);
        if (imageUrl) {
          editor.chain().focus().setImage({ src: imageUrl }).run();
        }
      } catch (error) {
        setUploadErrorText(error?.message || COMMON_COMPONENT_LANG_KO.easyEditor.imageUploadFailed);
      }
    }

    event.target.value = '';
  };

  /**
   * @description 첨부 파일 선택 결과의 업로드와 editor 링크 콘텐츠 삽입
   * 처리 규칙: 업로드 응답 문자열과 객체 응답을 모두 링크 descriptor로 맞춘다.
   */
  const handleFileSelect = async (event) => {
    if (!editor || readOnly) return;
    const selectedFileList = Array.from(event.target.files || []);
    if (!selectedFileList.length) return;
    setUploadErrorText('');

    for (const file of selectedFileList) {
      try {
        const uploadResultObj = await fileUploadHandler(file);
        if (!uploadResultObj) continue;
        const fileLinkObj = typeof uploadResultObj === 'string'
          ? { url: uploadResultObj, name: file.name }
          : { url: uploadResultObj.url, name: uploadResultObj.name ?? file.name };
        if (fileLinkObj?.url) {
          editor.chain().focus().insertContent(
            `<a href="${fileLinkObj.url}" target="_blank" rel="noopener noreferrer" class="text-blue-600 underline">${fileLinkObj.name}</a>`
          ).run();
        }
      } catch (error) {
        setUploadErrorText(error?.message || COMMON_COMPONENT_LANG_KO.easyEditor.fileUploadFailed);
      }
    }

    event.target.value = '';
  };

  /**
   * @description 숨겨진 이미지 업로드 input 파일 선택 창 열기
   * 처리 규칙: 툴바가 잠겨 있으면 input click을 실행하지 않는다.
   */
  const triggerImageDialog = () => {
    if (toolbarDisabled) return;
    fileInputRef.current?.click();
  };

  /**
   * @description 숨겨진 첨부 업로드 input 파일 선택 창 열기
   * 처리 규칙: 툴바가 잠겨 있으면 input click을 실행하지 않는다.
   */
  const triggerFileDialog = () => {
    if (toolbarDisabled) return;
    attachmentInputRef.current?.click();
  };

  const containerClassName = clsx(
    editorRootClassName,
    invalid ? 'border-red-300 focus-within:ring-red-500' : 'border-gray-200',
    statusClassMap[status] || statusClassMap.idle,
    className,
  );

  const currentFontSize = editor?.getAttributes('textStyle')?.fontSize || 'default';
  const fontSizeValue = fontSizeOptionList.some((option) => option.value === currentFontSize)
    ? currentFontSize
    : 'default';

  /**
   * @description 폰트 크기 select 값의 editor textStyle mark 반영
   * 처리 규칙: default 선택 시 fontSize mark를 제거한다.
   */
  const handleFontSizeChange = (event) => {
    if (!editor || toolbarDisabled) return;
    const nextFontSize = event.target.value;
    if (nextFontSize === 'default') {
      editor.chain().focus().setMark('textStyle', { fontSize: null }).removeEmptyTextStyle().run();
    } else {
      editor.chain().focus().setMark('textStyle', { fontSize: nextFontSize }).run();
    }
  };

  const currentColor = editor?.getAttributes('textStyle')?.color || '#000000';

  /**
   * @description color input 값의 editor text color mark 반영
   * 처리 규칙: 툴바가 잠겨 있으면 색상 변경을 실행하지 않는다.
   */
  const handleColorChange = (event) => {
    if (!editor || toolbarDisabled) return;
    editor.chain().focus().setColor(event.target.value).run();
  };

  /**
   * @description editor text color mark 기본값 복원
   * 처리 규칙: color 제거 후 빈 textStyle mark도 함께 정리한다.
   */
  const handleResetColor = () => {
    if (!editor || toolbarDisabled) return;
    editor.chain().focus().setColor(null).removeEmptyTextStyle().run();
  };

  /**
   * @description 정렬 버튼 값의 editor textAlign 명령 반영
   * 처리 규칙: 툴바가 잠겨 있으면 정렬 명령을 실행하지 않는다.
   */
  const handleTextAlign = (value) => {
    if (!editor || toolbarDisabled) return;
    editor.chain().focus().setTextAlign(value).run();
  };

  const minHeightClassMap = {
    "180px": "min-h-[180px]",
    "200px": "min-h-[200px]",
    "220px": "min-h-[220px]",
    "240px": "min-h-[240px]",
    "260px": "min-h-[260px]",
    "280px": "min-h-[280px]",
    "300px": "min-h-[300px]",
    "320px": "min-h-[320px]",
    "360px": "min-h-[360px]",
  };
  let minHeightKey = "";
  if (typeof minHeight === "number") {
    minHeightKey = `${Math.floor(minHeight)}px`;
  } else if (typeof minHeight === "string") {
    minHeightKey = minHeight.trim().toLowerCase();
  }
  const minHeightClassName = minHeightClassMap[minHeightKey] || minHeightClassMap["240px"];

  return (
    <div className="space-y-2">
      {label && (
        <label htmlFor={id} className="block text-sm font-medium text-gray-700">
          {label}
        </label>
      )}
      <div className={containerClassName}>
        {toolbar && editor && (
          <div className={toolbarClassName}>
            <div className="flex items-center gap-2">
              <ToolbarButton
                label={COMMON_COMPONENT_LANG_KO.easyEditor.toolbarBold}
                active={editor.isActive('bold')}
                onClick={() => handleToggle('toggleBold')}
                disabled={toolbarDisabled}
              >
                B
              </ToolbarButton>
              <ToolbarButton
                label={COMMON_COMPONENT_LANG_KO.easyEditor.toolbarItalic}
                active={editor.isActive('italic')}
                onClick={() => handleToggle('toggleItalic')}
                disabled={toolbarDisabled}
              >
                I
              </ToolbarButton>
              <ToolbarButton
                label={COMMON_COMPONENT_LANG_KO.easyEditor.toolbarUnderline}
                active={editor.isActive('underline')}
                onClick={() => handleToggle('toggleUnderline')}
                disabled={toolbarDisabled}
              >
                U
              </ToolbarButton>
              <ToolbarButton
                label={COMMON_COMPONENT_LANG_KO.easyEditor.toolbarLink}
                active={editor.isActive('link')}
                onClick={handleSetLink}
                disabled={toolbarDisabled}
              >
                🔗
              </ToolbarButton>
            </div>

            <div className="flex items-center gap-2">
              <select
                className="h-8 rounded border border-gray-300 px-2 text-sm"
                value={fontSizeValue}
                onChange={handleFontSizeChange}
                disabled={toolbarDisabled}
              >
                {fontSizeOptionList.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <div className="flex items-center gap-1">
                <input
                  type="color"
                  value={currentColor}
                  onChange={handleColorChange}
                  disabled={toolbarDisabled}
                  className="h-8 w-10 border border-gray-300 rounded"
                />
                <button
                  type="button"
                  onClick={handleResetColor}
                  disabled={toolbarDisabled}
                  className="text-xs text-gray-500 underline"
                >
                  {COMMON_COMPONENT_LANG_KO.easyEditor.colorReset}
                </button>
              </div>
            </div>

            <div className="flex items-center gap-1">
              {alignmentList.map((alignmentItem) => (
                <ToolbarButton
                  key={alignmentItem.value}
                  label={`${alignmentItem.label}${COMMON_COMPONENT_LANG_KO.easyEditor.alignSuffix}`}
                  active={editor.isActive({ textAlign: alignmentItem.value })}
                  onClick={() => handleTextAlign(alignmentItem.value)}
                  disabled={toolbarDisabled}
                >
                  {alignmentItem.icon}
                </ToolbarButton>
              ))}
            </div>

            <div className="flex items-center gap-2">
              <ToolbarButton
                label={COMMON_COMPONENT_LANG_KO.easyEditor.attachImage}
                active={false}
                onClick={triggerImageDialog}
                disabled={toolbarDisabled}
              >
                🖼️
              </ToolbarButton>
              <ToolbarButton
                label={COMMON_COMPONENT_LANG_KO.easyEditor.attachFile}
                active={false}
                onClick={triggerFileDialog}
                disabled={toolbarDisabled}
              >
                📎
              </ToolbarButton>
            </div>

            <div className="flex items-center gap-2 ml-auto">
              <ToolbarButton
                label={COMMON_COMPONENT_LANG_KO.easyEditor.modeEditor}
                active={mode === 'editor'}
                onClick={() => setMode('editor')}
                disabled={mode === 'editor'}
              >
                Editor
              </ToolbarButton>
              <ToolbarButton
                label={COMMON_COMPONENT_LANG_KO.easyEditor.modeHtml}
                active={mode === 'html'}
                onClick={() => setMode('html')}
                disabled={mode === 'html'}
              >
                HTML
              </ToolbarButton>
            </div>
          </div>
        )}
        <EditorContent
          id={id}
          editor={editor}
          role="textbox"
          aria-multiline="true"
          aria-invalid={invalid || undefined}
          aria-readonly={readOnly || undefined}
          aria-hidden={isHtmlMode ? 'true' : undefined}
          data-name={name}
          className={clsx(editorBodyClassName, minHeightClassName, isHtmlMode && 'hidden')}
        />
        {isHtmlMode && (
          <textarea
            className="font-mono text-sm w-full min-h-[200px] border-t border-gray-200 focus:outline-none p-3"
            value={htmlDraft}
            onChange={(event) => setHtmlDraft(event.target.value)}
            disabled={readOnly}
          />
        )}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          className="sr-only"
          tabIndex={-1}
          aria-hidden="true"
          onChange={handleImageSelect}
        />
        <input
          ref={attachmentInputRef}
          type="file"
          className="sr-only"
          tabIndex={-1}
          aria-hidden="true"
          onChange={handleFileSelect}
        />
      </div>
      {uploadErrorText && (
        <p role="alert" className="text-sm text-red-600">
          {uploadErrorText}
        </p>
      )}
      {helperText && (
        <p className={clsx('text-sm', invalid ? 'text-red-600' : 'text-gray-500')}>
          {helperText}
        </p>
      )}
      {alertElement}
    </div>
  );
};

export default EasyEditor;
