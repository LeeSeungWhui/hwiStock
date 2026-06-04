/**
 * 파일명: publicRoutes.js
 * 작성자: LSH
 * 갱신일: 2026-06-05
 * 설명: 인증 불필요(공개) 경로 목록과 판별 유틸
 */

// 공개 경로 패턴 목록
// 규칙:
// - 정확 경로: '/login'
// - 서브트리 포함: '/docs/:path*' (Next matcher 스타일 지원)
// - UNIT-007: 운영자 진입은 /login만 공개로 유지한다.
export const publicRoutes = ["/login"];

/**
 * 설명: Next matcher 스타일 패턴을 RegExp로 변환
 * 지원: '/path', '/path/:path*', '/path/:path+' (접미부 전용)
 */
const compileRoutePattern = (routePattern) => {
  if (routePattern === "/") return /^\/$/;

  const escapedPatternText = routePattern.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

  if (escapedPatternText.endsWith("\/:path\\*")) {
    const routePrefixText = escapedPatternText.slice(0, -"\/:path\\*".length);
    return new RegExp("^" + routePrefixText + "(?:\/.*)?$");
  }
  if (escapedPatternText.endsWith("\/:path\\+")) {
    const routePrefixText = escapedPatternText.slice(0, -"\/:path\\+".length);
    return new RegExp("^" + routePrefixText + "\/.+$");
  }
  return new RegExp("^" + escapedPatternText + "$");
};

const publicRouteRegexList = publicRoutes.map(compileRoutePattern);

/**
 * 설명: 주어진 pathname이 공개 경로인지 판별
 * 처리 규칙: 문자열이 아니면 false를 반환하고, 등록된 정규식 패턴 중 하나라도 일치하면 true를 반환한다.
 * 반환값: 공개 경로 여부(boolean)
 */
export const isPublicPath = (pathname) => {
  if (!pathname || typeof pathname !== "string") return false;
  for (const routeRegexObj of publicRouteRegexList) {
    if (routeRegexObj.test(pathname)) return true;
  }
  return false;
};
