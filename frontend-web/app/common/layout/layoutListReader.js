/**
 * 파일명: common/layout/layoutListReader.js
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 공용 레이아웃 메뉴 입력의 배열 렌더링 계약 변환
 */

/**
 * @description 메뉴 입력의 배열 렌더링 계약 변환
 * 처리 규칙: 배열은 그대로 반환하고 EasyList 계열은 size/get 계약으로 읽어 메뉴 배열을 만든다.
 * @updated 2026-05-02
 */
export const readMenuList = (menuList) => {
  if (Array.isArray(menuList)) return menuList;

  const hasMenuListShape =
    Boolean(menuList) &&
    (typeof menuList.size === "function" || Array.isArray(menuList));

  if (hasMenuListShape) {
    const menuCount = typeof menuList.size === "function" ? menuList.size() : 0;
    const resolvedMenuList = [];
    for (let menuIndex = 0; menuIndex < menuCount; menuIndex += 1) {
      resolvedMenuList.push(
        typeof menuList.get === "function" ? menuList.get(menuIndex) : undefined,
      );
    }
    return resolvedMenuList;
  }

  return [];
};

/**
 * @description 하위 메뉴 입력의 배열 렌더링 계약 변환
 * 처리 규칙: 배열은 그대로 반환하고 EasyList 계열은 size/get 계약으로 읽어 하위 메뉴 배열을 만든다.
 * @updated 2026-05-02
 */
export const readSubMenuList = (subMenuList) => {
  if (Array.isArray(subMenuList)) return subMenuList;

  const hasSubMenuListShape =
    Boolean(subMenuList) &&
    (typeof subMenuList.size === "function" || Array.isArray(subMenuList));

  if (hasSubMenuListShape) {
    const subMenuCount = typeof subMenuList.size === "function" ? subMenuList.size() : 0;
    const resolvedSubMenuList = [];
    for (let subMenuIndex = 0; subMenuIndex < subMenuCount; subMenuIndex += 1) {
      resolvedSubMenuList.push(
        typeof subMenuList.get === "function" ? subMenuList.get(subMenuIndex) : undefined,
      );
    }
    return resolvedSubMenuList;
  }

  return [];
};

/**
 * @description 푸터 링크 입력의 배열 렌더링 계약 변환
 * 처리 규칙: 배열은 그대로 반환하고 EasyList 계열은 size/get 계약으로 읽어 링크 배열을 만든다.
 * @updated 2026-05-02
 */
export const readFooterLinkList = (linkList) => {
  if (Array.isArray(linkList)) return linkList;

  const hasLinkListShape =
    Boolean(linkList) &&
    (typeof linkList.size === "function" || Array.isArray(linkList));

  if (hasLinkListShape) {
    const linkCount = typeof linkList.size === "function" ? linkList.size() : 0;
    const resolvedLinkList = [];
    for (let linkIndex = 0; linkIndex < linkCount; linkIndex += 1) {
      resolvedLinkList.push(
        typeof linkList.get === "function" ? linkList.get(linkIndex) : undefined,
      );
    }
    return resolvedLinkList;
  }

  return [];
};
