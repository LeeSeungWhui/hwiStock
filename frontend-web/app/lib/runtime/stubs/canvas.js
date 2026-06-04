/**
 * 파일명: canvas.js
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 서버 환경에서 canvas 네이티브 모듈 접근을 차단하는 런타임 스텁
 */

"use strict";

/**
 * 캔버스 생성 시도 차단
 * @returns {never}
 * @description createCanvas 호출 경로를 stub으로 연결
 * @updated 2026-05-02
 */
const createCanvas = () => {
  throw new Error('canvas stub: createCanvas is not available in this environment.');
};

/**
 * 이미지 로드 시도 차단
 * @returns {Promise<never>}
 * @description loadImage 호출 경로를 stub으로 연결
 * @updated 2026-05-02
 */
const loadImage = async () => {
  throw new Error('canvas stub: loadImage is not available in this environment.');
};

/**
 * 폰트 등록 시도 차단
 * @returns {never}
 * @description registerFont 호출 경로를 stub으로 연결
 * @updated 2026-05-02
 */
const registerFont = () => {
  throw new Error('canvas stub: registerFont is not available in this environment.');
};

module.exports = {
  createCanvas,
  loadImage,
  registerFont,
};

module.exports.default = module.exports;
