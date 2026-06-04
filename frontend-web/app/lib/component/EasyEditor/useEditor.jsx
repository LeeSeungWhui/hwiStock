"use client";

/**
 * 파일명: useEditor.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: EasyEditor 전용 훅
 */

import { useEffect, useRef } from 'react';
import { useEditor as useTiptapEditor } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Placeholder from '@tiptap/extension-placeholder';
import Image from '@tiptap/extension-image';
import Underline from '@tiptap/extension-underline';
import { TextStyle } from '@tiptap/extension-text-style';
import Color from '@tiptap/extension-color';
import TextAlign from '@tiptap/extension-text-align';
import { Extension } from '@tiptap/core';
import { getBoundValue, setBoundValue, buildCtx, fireValueHandlers } from '../../binding';
import { deepCloneValue, safeJsonParse } from '@/app/lib/runtime/json';
import { COMMON_COMPONENT_LANG_KO } from '@/app/common/i18n/lang.ko';

const EMPTY_EXTENSION_LIST = [];

const FontSize = Extension.create({
  name: 'fontSize',
  addGlobalAttributes() {
    return [
      {
        types: ['textStyle'],
        attributes: {
          fontSize: {
            default: null,
            parseHTML: (element) => element.style.fontSize || null,
            renderHTML: (attributes) => {
              if (!attributes.fontSize) return {};
              return { style: `font-size: ${attributes.fontSize}` };
            },
          },
        },
      },
    ];
  },
  addCommands() {
    return {
      setFontSize:
        (size) => ({ chain }) => chain().setMark('textStyle', { fontSize: size }).run(),
      unsetFontSize:
        () => ({ chain }) => chain().setMark('textStyle', { fontSize: null }).removeEmptyTextStyle().run(),
    };
  },
});

/**
 * @description TipTap JSON 스키마의 기본 빈 문서 구조를 생성. 입력/출력 계약을 함께 명시
 * 반환값: paragraph 1개를 가진 최소 doc 객체.
 * @updated 2026-02-27
 */
const createEmptyDoc = () => ({
  type: 'doc',
  content: [
    {
      type: 'paragraph',
      content: [],
    },
  ],
});

/**
 * @description EasyObj 래퍼 값에서 raw object를 꺼내거나 원본 값을 그대로 반환. 입력/출력 계약을 함께 명시
 * 처리 규칙: `__rawObject` 필드가 있으면 해당 값을 우선 사용한다.
 * @updated 2026-02-27
 */
const unwrap = (value) => {
  const hasRawObjectValue = value && typeof value === 'object' && value.__rawObject;
  if (hasRawObjectValue) return value.__rawObject;
  return value;
};

/**
 * @description editor 내용을 지정된 serialization(html/text/json) 형태로 직렬화
 * 반환값: format에 따라 HTML 문자열, plain text, JSON doc 객체.
 * @updated 2026-02-27
 */
const serialise = (editor, format) => {
  if (format === 'html') return editor.getHTML();
  if (format === 'text') return editor.getText();
  return editor.getJSON();
};

/**
 * @description 외부 입력 값을 에디터 setContent 가능한 형태로 정규화. 입력/출력 계약을 함께 명시
 * 실패 동작: JSON 파싱/복제 실패 시 빈 문서(createEmptyDoc)로 대체한다.
 * @updated 2026-02-27
 */
const normaliseExternalValue = (value, format) => {
  const unwrappedValue = unwrap(value);

  if (format === 'html' || format === 'text') return unwrappedValue ? String(unwrappedValue) : '';

  if (!unwrappedValue) return createEmptyDoc();

  if (typeof unwrappedValue === 'string') {
    const parsedValue = safeJsonParse(unwrappedValue, null);
    if (parsedValue && typeof parsedValue === 'object') return parsedValue;
    return createEmptyDoc();
  }

  if (typeof unwrappedValue === 'object') {
    const clonedValue = deepCloneValue(unwrappedValue, null);
    if (clonedValue && typeof clonedValue === 'object') return clonedValue;
    return createEmptyDoc();
  }

  return createEmptyDoc();
};

/**
 * @description 값 변경 감지를 위해 직렬화 가능한 fingerprint 문자열을 생성. 입력/출력 계약을 함께 명시
 * 처리 규칙: html/text는 문자열화, json은 JSON.stringify 실패 시 빈 문서 기준 문자열을 사용한다.
 * @updated 2026-02-27
 */
const fingerprint = (value, format) => {
  const unwrappedValue = unwrap(value);
  if (format === 'html' || format === 'text') return String(unwrappedValue ?? '');
  try {
    return JSON.stringify(unwrappedValue ?? createEmptyDoc());
  } catch (error) {
    return JSON.stringify(createEmptyDoc());
  }
};

/**
 * @description 바인딩 저장 전에 값을 안전하게 복제/정규화. 입력/출력 계약을 함께 명시
 * 반환값: html/text는 문자열, json은 deep clone된 문서 객체.
 * @updated 2026-02-27
 */
const cloneForStorage = (value, format) => {
  const unwrappedValue = unwrap(value);
  if (format === 'html' || format === 'text') return String(unwrappedValue ?? '');
  return deepCloneValue(unwrappedValue ?? createEmptyDoc(), createEmptyDoc());
};

/**
 * @description EasyEditor 상태를 바인딩/동기화하는 훅을 반환. 입력/출력 계약을 함께 명시
 * 처리 규칙: bound 모드에서는 dataObj[dataKey]와 동기화하고, unbound 모드에서는 onChange/onValueChange 콜백으로 전달한다.
 * @updated 2026-02-24
 */
export const useEasyEditor = ({
  dataObj,
  dataKey,
  value,
  onChange,
  onValueChange,
  placeholder = COMMON_COMPONENT_LANG_KO.easyEditor.placeholder,
  readOnly = false,
  serialization = 'json',
  extensions,
  autofocus = false,
  onReady,
}) => {

  const isBound = Boolean(dataObj && dataKey);
  const contentPrintRef = useRef(null);
  const extensionList = extensions ?? EMPTY_EXTENSION_LIST;

  const defaultExtensionList = [
    StarterKit.configure({ history: true }),
    Underline,
    Placeholder.configure({ placeholder }),
    Image.configure({ inline: false }),
    TextStyle,
    Color.configure({ types: ['textStyle'] }),
    TextAlign.configure({ types: ['heading', 'paragraph'] }),
    FontSize,
  ];
  const editorExtensionList = [
    ...defaultExtensionList,
    ...extensionList,
  ];

  const initialContent = normaliseExternalValue(
    isBound ? getBoundValue(dataObj, dataKey) : value,
    serialization,
  );

  const editor = useTiptapEditor(
    {
      extensions: editorExtensionList,
      content: initialContent,
      autofocus,
      editable: !readOnly,
      immediatelyRender: false,
      onCreate: ({ editor }) => {
        const initialValue = serialise(editor, serialization);
        contentPrintRef.current = fingerprint(initialValue, serialization);
        onReady?.(editor);
      },
      onUpdate: ({ editor }) => {
        const nextValue = serialise(editor, serialization);
        const nextFingerprint = fingerprint(nextValue, serialization);
        if (nextFingerprint === contentPrintRef.current) {
          return;
        }

        if (isBound) {
          const bindingCtx = buildCtx({ dataObj, dataKey, source: 'user', dirty: true, valid: null });
          const storedValue = cloneForStorage(nextValue, serialization);
          const currentContent = normaliseExternalValue(getBoundValue(dataObj, dataKey), serialization);
          const currentFingerprint = fingerprint(currentContent, serialization);
          if (currentFingerprint !== nextFingerprint) {
            setBoundValue(dataObj, dataKey, storedValue, { source: 'user' });
          }
          contentPrintRef.current = nextFingerprint;
          const editorChangeEventObj = {
            type: 'easyeditor:update',
            target: { value: storedValue },
            detail: { value: storedValue, ctx: bindingCtx, editor },
            preventDefault() { },
            stopPropagation() { },
          };
          fireValueHandlers({
            onChange,
            onValueChange,
            value: storedValue,
            ctx: bindingCtx,
            event: editorChangeEventObj,
          });
        } else {
          contentPrintRef.current = nextFingerprint;
          const editorPayloadObj = { editor };
          onChange?.(nextValue, editorPayloadObj);
          onValueChange?.(nextValue, editorPayloadObj);
        }
      },
    },
    [placeholder, extensionList, autofocus, readOnly, serialization, isBound, dataObj, dataKey],
  );

  /**
   * @description readOnly 변경 시 TipTap editor editable 상태 동기화
   * 처리 규칙: editor.setEditable(!readOnly)를 readOnly 의존성마다 호출한다.
   */
  useEffect(() => {
    if (!editor) return;
    editor.setEditable(!readOnly);
  }, [editor, readOnly]);

  /**
   * @description 외부 value/dataKey 변경 시 editor 본문을 fingerprint 기준으로 동기화
   * 처리 규칙: fingerprint가 바뀔 때만 setContent로 외부 입력을 반영한다.
   */
  useEffect(() => {
    if (!editor) return;
    const externalValue = isBound ? getBoundValue(dataObj, dataKey) : value;
    const externalContent = normaliseExternalValue(externalValue, serialization);
    const nextFingerprint = fingerprint(externalContent, serialization);

    if (nextFingerprint === contentPrintRef.current) return;

    if (serialization === 'html' || serialization === 'text') {
      editor.commands.setContent(externalContent || '<p></p>', false);
    } else {
      editor.commands.setContent(externalContent || createEmptyDoc(), false);
    }
    contentPrintRef.current = nextFingerprint;
  }, [editor, isBound, dataObj, dataKey, value, serialization]);

  return { editor };
}

/**
 * @description useEasyEditor 훅을 default export로 노출
 * 반환값: useEasyEditor 함수 export.
 */
export default useEasyEditor;
