/**
 * 파일명: useEasyUpload.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 파일 업로드 유틸. BFF/백엔드 호스트를 자동 해석해 FormData 업로드를 수행
 */

import { getUiActionsSnap } from "@/app/common/store/SharedStore";
import { getBackendHost } from "@/app/common/config/getBackendHost.client";
import { COMMON_COMPONENT_LANG_KO } from "@/app/common/i18n/lang.ko";
import { apiRequest } from "@/app/lib/runtime/api";
import {
  parseJsonPayload,
  normalizeNestedJsonFields,
} from "@/app/lib/runtime/jsonPayload";

const DEFAULT_OPTIONS = {
  fileUploadUrl: "",
  singleFieldName: "file",
  multiFieldName: "files",
  credentials: "include",
  extraFormData: null,
  headers: {},
};

/**
 * @description File/FileList/ArrayLike 입력을 업로드 가능한 파일 배열로 변환. 입력/출력 계약을 함께 명시
 * 반환값: 유효 파일만 포함된 배열(입력이 비어 있으면 빈 배열).
 * @updated 2026-02-27
 */
const readFileList = (filesInput) => {
  if (!filesInput) return [];
  if (filesInput instanceof File || filesInput instanceof Blob)
    return [filesInput];
  const fileList = [];
  if (typeof filesInput.forEach === "function") {
    filesInput.forEach((fileInputObj) => {
      if (fileInputObj) fileList.push(fileInputObj);
    });
    return fileList;
  }
  if (typeof filesInput.length === "number") {
    for (let index = 0; index < filesInput.length; index += 1) {
      if (filesInput[index]) fileList.push(filesInput[index]);
    }
    return fileList;
  }
  return [];
};

/**
 * @description FormData 기반 파일 업로드를 수행하고 공통 응답 형식으로 정규화. 입력/출력 계약을 함께 명시
 * 처리 규칙: fetch 실패/비정상 응답 시 공통 Alert를 표시하고 Error를 던진다.
 * @param {File|Blob|File[]|FileList|ArrayLike<File>|null} filesInput
 * @param {Object} [options]
 * @returns {Promise<any>}
 */
const easyUploadRequest = async ({ filesInput, options = {} }) => {

  const uploadConfigObj = { ...DEFAULT_OPTIONS, ...options };
  if (!uploadConfigObj.fileUploadUrl) {
    throw new Error(COMMON_COMPONENT_LANG_KO.easyUpload.fileUploadUrlRequired);
  }
  const extraPayloadList = [];
  if (uploadConfigObj.extraFormData && typeof uploadConfigObj.extraFormData === "object") {
    extraPayloadList.push(uploadConfigObj.extraFormData);
  }
  if (uploadConfigObj.etc && typeof uploadConfigObj.etc === "object") {
    extraPayloadList.push(uploadConfigObj.etc);
  }

  const uploadFileList = readFileList(filesInput);
  if (!uploadFileList.length) return null;

  const { updateLoading, showAlert } = getUiActionsSnap();

  const formData = new FormData();
  const fieldName =
    uploadFileList.length === 1 ? uploadConfigObj.singleFieldName : uploadConfigObj.multiFieldName;
  uploadFileList.forEach((file) => {
    if (file) formData.append(fieldName, file);
  });

  extraPayloadList.forEach((extraPayloadObj) => {
    Object.entries(extraPayloadObj).forEach(([extraPayloadKey, extraPayloadValue]) => {
      if (extraPayloadValue == null) return;
      if (Array.isArray(extraPayloadValue)) {
        extraPayloadValue.forEach((payloadValue) => {
          if (payloadValue != null) formData.append(extraPayloadKey, payloadValue);
        });
        return;
      }
      formData.append(extraPayloadKey, extraPayloadValue);
    });
  });

  const shouldTrackLoading = Boolean(options.loading);
  if (shouldTrackLoading) {
    updateLoading(1);
  }
  try {
    let targetUrl = "";
    if (typeof uploadConfigObj.fileUploadUrl === "string") {
      targetUrl = uploadConfigObj.fileUploadUrl;
      if (!/^https?:\/\//i.test(uploadConfigObj.fileUploadUrl) && !uploadConfigObj.fileUploadUrl.startsWith("/api/bff/")) {
        const backendHost = getBackendHost();
        if (backendHost) {
          const normalizedBackend = backendHost.endsWith("/")
            ? backendHost.slice(0, -1)
            : backendHost;
          targetUrl = uploadConfigObj.fileUploadUrl.startsWith("/")
            ? `${normalizedBackend}${uploadConfigObj.fileUploadUrl}`
            : `${normalizedBackend}/${uploadConfigObj.fileUploadUrl}`;
        }
      }
    }
    const uploadResponse = await apiRequest(targetUrl, {
      method: "POST",
      body: formData,
      headers: uploadConfigObj.headers,
    });

    if (!uploadResponse.ok) {
      let uploadErrorText = "";
      try {
        uploadErrorText = await uploadResponse.text();
      } catch {
        uploadErrorText = "";
      }
      let uploadErrorMessage = `${uploadResponse.status}${COMMON_COMPONENT_LANG_KO.easyUpload.uploadFailedWithStatusSuffix}`;
      if (uploadErrorText) {
        const uploadErrorObj = parseJsonPayload(uploadErrorText, { context: "EasyUploadError" });
        if (uploadErrorObj && typeof uploadErrorObj === "object") {
          const parsedErrorMessage = uploadErrorObj?.message || uploadErrorObj?.result;
          const isParsedErrorMessage = typeof parsedErrorMessage === "string";
          if (isParsedErrorMessage) {
            uploadErrorMessage = parsedErrorMessage;
          }
        }
      }
      showAlert(uploadErrorMessage || COMMON_COMPONENT_LANG_KO.easyUpload.uploadFailedDescription, {
        title: COMMON_COMPONENT_LANG_KO.easyUpload.uploadFailedTitle,
        type: "error",
      });
      throw new Error(uploadErrorMessage || COMMON_COMPONENT_LANG_KO.easyUpload.uploadFailedDefault);
    }

    const contentType = (
      uploadResponse.headers.get("content-type") || ""
    ).toLowerCase();
    const rawText = await uploadResponse.text();

    if (!contentType.includes("application/json")) {
      return rawText || null;
    }

    const parsed = parseJsonPayload(rawText, { context: "EasyUpload" });
    return normalizeNestedJsonFields(parsed);
  } catch (error) {
    if (!error?.message) {
      showAlert(COMMON_COMPONENT_LANG_KO.easyUpload.uploadUnknownError, {
        title: COMMON_COMPONENT_LANG_KO.easyUpload.uploadFailedTitle,
        type: "error",
      });
    }
    throw error;
  } finally {
    if (shouldTrackLoading) {
      updateLoading(-1);
    }
  }
}

export default easyUploadRequest;
