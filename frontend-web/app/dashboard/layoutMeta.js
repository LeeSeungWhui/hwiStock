/**
 * 파일명: dashboard/layoutMeta.js
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 대시보드 레이아웃(헤더/사이드바) 경로·쿼리 메타 계산 유틸
 */

import LANG_KO from "./lang.ko";
import TASKS_LANG_KO from "./tasks/lang.ko";

const DEFAULT_SORT = "at_desc";
const STATUS_FILTER_LIST = TASKS_LANG_KO.initData.statusFilterList.map((statusFilterObj) => ({
  ...statusFilterObj,
}));
const SORT_FILTER_LIST = TASKS_LANG_KO.initData.sortFilterList.map((sortFilterObj) => ({
  ...sortFilterObj,
}));
const MENU_TEMPLATE_LIST = LANG_KO.layoutMeta.menuList.map((menuItemObj) => ({ ...menuItemObj }));

const STATUS_LABEL_MAP = new Map(
  STATUS_FILTER_LIST.filter((statusFilterObj) => statusFilterObj.value).map((statusFilterObj) => [
    String(statusFilterObj.value),
    String(statusFilterObj.text),
  ])
);

const SORT_LABEL_MAP = new Map(
  SORT_FILTER_LIST.map((sortFilterObj) => [String(sortFilterObj.value), String(sortFilterObj.text)])
);

/**
 * @description 현재 대시보드 경로/쿼리 기준으로 헤더/사이드바 메타를 계산. 입력/출력 계약을 함께 명시
 * @param {Object} params
 * @param {string} params.pathname 현재 pathname
 * @param {URLSearchParams|Object} params.searchParams 현재 search params
 * @returns {{ title:string, subtitle:string, text:string, menuList:Array, subMenuList:Array }}
 */
export const resolveDashboardLayoutMeta = ({ pathname, searchParams }) => {

  const pathText = String(pathname || "");
  let routeKey = "dashboard";
  if (pathText.startsWith("/dashboard/tasks")) routeKey = "tasks";
  else if (pathText.startsWith("/dashboard/settings")) routeKey = "settings";
  let keyword = "";
  let status = "";
  let sort = DEFAULT_SORT;
  let page = 1;
  let tab = "";
  if (searchParams && typeof searchParams.get === "function") {
    keyword = String(searchParams.get("q") || "").trim();
    status = String(searchParams.get("status") || "").trim().toLowerCase();
    sort = String(searchParams.get("sort") || "").trim().toLowerCase() || DEFAULT_SORT;
    const parsedPage = Number.parseInt(String(searchParams.get("page") || ""), 10);
    page = Number.isFinite(parsedPage) && parsedPage > 0 ? parsedPage : 1;
    tab = String(searchParams.get("tab") || "").trim().toLowerCase();
  } else if (searchParams && typeof searchParams === "object") {
    const keywordValue = Array.isArray(searchParams.q) ? searchParams.q[0] : searchParams.q;
    const statusValue = Array.isArray(searchParams.status)
      ? searchParams.status[0]
      : searchParams.status;
    const sortValue = Array.isArray(searchParams.sort) ? searchParams.sort[0] : searchParams.sort;
    const pageValue = Array.isArray(searchParams.page) ? searchParams.page[0] : searchParams.page;
    const tabValue = Array.isArray(searchParams.tab) ? searchParams.tab[0] : searchParams.tab;
    keyword = String(keywordValue || "").trim();
    status = String(statusValue || "").trim().toLowerCase();
    sort = String(sortValue || "").trim().toLowerCase() || DEFAULT_SORT;
    const parsedPage = Number.parseInt(String(pageValue || ""), 10);
    page = Number.isFinite(parsedPage) && parsedPage > 0 ? parsedPage : 1;
    tab = String(tabValue || "").trim().toLowerCase();
  }

  const menuList = MENU_TEMPLATE_LIST.map((menuItemObj) => ({
    ...menuItemObj,
    active: menuItemObj.menuId === routeKey,
  }));

  let subMenuList = [];
  if (routeKey === "tasks") {
    subMenuList = STATUS_FILTER_LIST.map((statusFilterObj) => {
      const statusValue = String(statusFilterObj.value || "");
      const href = statusValue
        ? `/dashboard/tasks?status=${encodeURIComponent(statusValue)}`
        : "/dashboard/tasks";
      const isActive = statusValue ? status === statusValue : !status;
      return {
        menuId: "tasks",
        subMenuId: statusValue || "all",
        subMenuNm: statusValue ? statusFilterObj.text : LANG_KO.layoutMeta.tasksAllStatus,
        href,
        active: isActive,
      };
    });
  }

  let title = LANG_KO.layoutMeta.title.dashboard;
  let subtitle = LANG_KO.layoutMeta.subtitle.dashboard;
  if (routeKey === "tasks") {
    title = LANG_KO.layoutMeta.title.tasks;
    const taskSubtitlePartList = [LANG_KO.layoutMeta.subtitle.tasksPrefix];
    if (status) {
      const statusLabel = STATUS_LABEL_MAP.get(status);
      if (statusLabel) {
        taskSubtitlePartList.push(`${LANG_KO.layoutMeta.subtitle.statusPrefix}: ${statusLabel}`);
      }
    }
    if (sort) {
      const isDefaultSort = sort === DEFAULT_SORT;
      const sortLabel = SORT_LABEL_MAP.get(sort);
      if (!isDefaultSort && sortLabel) {
        taskSubtitlePartList.push(`${LANG_KO.layoutMeta.subtitle.sortPrefix}: ${sortLabel}`);
      }
    }
    if (keyword) taskSubtitlePartList.push(`${LANG_KO.layoutMeta.subtitle.keywordPrefix}: ${keyword}`);
    if (page > 1) taskSubtitlePartList.push(`${LANG_KO.layoutMeta.subtitle.pagePrefix}: ${page}`);
    subtitle = taskSubtitlePartList.join(" · ");
  } else if (routeKey === "settings") {
    title = LANG_KO.layoutMeta.title.settings;
    subtitle = tab === "connection"
      ? LANG_KO.layoutMeta.subtitle.settingsConnection
      : LANG_KO.layoutMeta.subtitle.settingsPolicy;
  }

  return {
    title,
    subtitle,
    text: LANG_KO.layoutMeta.welcomeText,
    menuList,
    subMenuList,
  };
};
