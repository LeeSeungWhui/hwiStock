"use client";

/**
 * 파일명: useEditorUpload.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: EasyEditor 이미지 업로드 훅
 */

import easyUploadRequest from '@/app/lib/hooks/useEasyUpload.jsx';

const DEFAULT_IMAGE_FIELD = 'image';
const DEFAULT_FILE_FIELD = 'file';

/**
 * @description 업로드 응답 래퍼(result/data) 재귀 언래핑 기반 실제 payload 획득
 * 반환값: 더 이상 래핑 키가 없는 원본 payload 객체/값.
 * @updated 2026-02-27
 */
const unwrapPayload = (uploadPayload) => {
  if (!uploadPayload || typeof uploadPayload !== 'object') return uploadPayload;
  if ('result' in uploadPayload) return unwrapPayload(uploadPayload.result);
  if ('data' in uploadPayload) return unwrapPayload(uploadPayload.data);
  return uploadPayload;
};

/**
 * @description uploadFileInfo 구조에서 URL 후보 필드를 우선순위대로 추출
 * 처리 규칙: 배열이면 첫 요소를 재귀 처리하고, 객체면 known URL 키를 순차 탐색한다.
 * @updated 2026-02-27
 */
const extractFromUploadInfo = (info) => {
  if (!info) return null;
  if (Array.isArray(info) && info.length > 0) {
    return extractFromUploadInfo(info[0]);
  }
  if (typeof info === 'object') {
    const uploadUrlValue =
      info.fileUrl
      ?? info.file_url
      ?? info.url
      ?? info.previewUrl
      ?? info.preview_url
      ?? info.httpUrl
      ?? info.http_url
      ?? info.cdnUrl
      ?? info.cdn_url
      ?? info.path
      ?? info.filePath
      ?? info.file_path;
    if (typeof uploadUrlValue === 'string' && uploadUrlValue.trim() !== '') {
      return uploadUrlValue.trim();
    }
  }
  if (typeof info === 'string' && info.trim() !== '') {
    return info.trim();
  }
  return null;
};

/**
 * @description 다양한 업로드 응답 형태에서 최종 파일 URL을 추출
 * 반환값: 찾은 URL 문자열 또는 null.
 * @updated 2026-02-27
 */
const extractUrl = (uploadPayload) => {
  if (typeof uploadPayload === 'string' && uploadPayload.trim() !== '') {
    return uploadPayload.trim();
  }
  const uploadValue = unwrapPayload(uploadPayload);
  if (typeof uploadValue === 'string' && uploadValue.trim() !== '') {
    return uploadValue.trim();
  }
  if (!uploadValue || typeof uploadValue !== 'object') return null;

  const directKeyList = [
    'url',
    'fileUrl',
    'file_url',
    'imageUrl',
    'image_url',
    'previewUrl',
    'preview_url',
    'httpUrl',
    'http_url',
    'cdnUrl',
    'cdn_url',
    'path',
    'filePath',
    'file_path',
  ];
  for (const uploadUrlKey of directKeyList) {
    if (
      typeof uploadValue[uploadUrlKey] === 'string'
      && uploadValue[uploadUrlKey].trim() !== ''
    ) {
      return uploadValue[uploadUrlKey].trim();
    }
  }

  const infoUrl = extractFromUploadInfo(uploadValue.uploadFileInfo ?? uploadValue.file);
  if (infoUrl) return infoUrl;

  return null;
};

/**
 * @description 파일 첨부 payload를 `{url, name}` 형태로 변환
 * 실패 동작: URL을 찾지 못하면 null을 반환한다.
 * @updated 2026-02-27
 */
const toAttachmentDescriptor = (uploadPayload, defaultAttachmentName) => {
  if (typeof uploadPayload === 'string' && uploadPayload.trim() !== '') {
    return { url: uploadPayload.trim(), name: defaultAttachmentName || '' };
  }
  const uploadValue = unwrapPayload(uploadPayload);
  if (typeof uploadValue === 'string' && uploadValue.trim() !== '') {
    return { url: uploadValue.trim(), name: defaultAttachmentName || '' };
  }
  if (!uploadValue || typeof uploadValue !== 'object') return null;

  const attachmentUrl = extractUrl(uploadValue);
  if (!attachmentUrl) return null;

  const attachmentName =
    uploadValue.name
    ?? uploadValue.fileName
    ?? uploadValue.file_name
    ?? uploadValue.originalName
    ?? uploadValue.originalFileName
    ?? uploadValue.originalFilename
    ?? uploadValue.original_filename
    ?? defaultAttachmentName
    ?? '';

  return { url: attachmentUrl, name: attachmentName };
};

/**
 * @description useEditorUpload 구성 데이터를 반환. 입력/출력 계약을 함께 명시
 * 반환값: EasyEditor에서 사용하는 uploadImage/uploadFile/alertElement API 집합.
 * @updated 2026-02-24
 */
const useEditorUpload = ({ imageUploadUrl = '', fileUploadUrl = '' }) => {

  /**
   * @description 이미지 파일을 업로드하고 응답에서 최종 URL을 추출
   * 실패 동작: 업로드 URL이 없거나 file이 비어 있으면 null을 반환한다.
   * @updated 2026-04-22
   */
  const uploadImage = async (file) => {
    if (!imageUploadUrl || !file) return null;
    const uploadResponse = await easyUploadRequest({
      filesInput: file,
      options: {
        fileUploadUrl: imageUploadUrl,
        singleFieldName: DEFAULT_IMAGE_FIELD,
        loading: true,
      },
    });
    return extractUrl(uploadResponse);
  };

  /**
   * @description 일반 첨부 파일을 업로드하고 `{url, name}` descriptor로 변환
   * 실패 동작: 업로드 URL이 없거나 file이 비어 있으면 null을 반환한다.
   * @updated 2026-04-22
   */
  const uploadFile = async (file) => {
    if (!fileUploadUrl || !file) return null;
    const uploadResponse = await easyUploadRequest({
      filesInput: file,
      options: {
        fileUploadUrl,
        singleFieldName: DEFAULT_FILE_FIELD,
        loading: true,
      },
    });
    return toAttachmentDescriptor(uploadResponse, file?.name);
  };

  return {
    uploadImage,
    uploadFile,
    alertElement: null,
  };
};

export default useEditorUpload;
