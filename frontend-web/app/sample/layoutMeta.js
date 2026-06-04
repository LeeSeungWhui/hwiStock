/**
 * 파일명: sample/layoutMeta.js
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 공개 샘플 레이아웃(헤더/사이드바) 메타 계산 유틸
 */

import LANG_KO from "./lang.ko";

const MENU_TEMPLATE_LIST = LANG_KO.layoutMeta.menuList.map((menuItemObj) => ({ ...menuItemObj }));

/**
 * @description 현재 공개 샘플 경로 기준으로 헤더/사이드바 메타를 계산. 입력/출력 계약을 함께 명시
 * @param {string} pathname 현재 pathname
 * @returns {{ title:string, subtitle:string, text:string, menuList:Array }}
 */
export const resolveDemoLayoutMeta = (pathname) => {
  const pathText = String(pathname || "");
  let routeKey = "demo";
  if (pathText.startsWith("/sample/dashboard")) routeKey = "dashboard";
  else if (pathText.startsWith("/sample/crud")) routeKey = "crud";
  else if (pathText.startsWith("/sample/form")) routeKey = "form";
  else if (pathText.startsWith("/sample/admin")) routeKey = "admin";

  const menuList = MENU_TEMPLATE_LIST.map((menuItemObj) => ({
    ...menuItemObj,
    active: menuItemObj.menuId === routeKey,
  }));
  let title = LANG_KO.layoutMeta.title.default;
  let subtitle = LANG_KO.layoutMeta.subtitle.default;
  if (routeKey === "demo") {
    title = LANG_KO.layoutMeta.title.demo;
    subtitle = LANG_KO.layoutMeta.subtitle.demo;
  } else if (routeKey === "dashboard") {
    title = LANG_KO.layoutMeta.title.dashboard;
    subtitle = LANG_KO.layoutMeta.subtitle.dashboard;
  } else if (routeKey === "form") {
    title = LANG_KO.layoutMeta.title.form;
    subtitle = LANG_KO.layoutMeta.subtitle.form;
  } else if (routeKey === "admin") {
    title = LANG_KO.layoutMeta.title.admin;
    subtitle = LANG_KO.layoutMeta.subtitle.admin;
  }

  return {
    title,
    subtitle,
    text: LANG_KO.layoutMeta.helperText,
    menuList,
  };
};
