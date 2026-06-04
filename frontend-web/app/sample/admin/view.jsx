"use client";

/**
 * 파일명: sample/admin/view.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 공개 관리자 화면 샘플 페이지 뷰(DB 사용자/설정 연동)
 */

import { useEffect, useMemo } from "react";
import { useGlobalUi } from "@/app/common/store/SharedStore";
import Badge from "@/app/lib/component/Badge";
import Button from "@/app/lib/component/Button";
import Card from "@/app/lib/component/Card";
import Checkbox from "@/app/lib/component/Checkbox";
import Drawer from "@/app/lib/component/Drawer";
import EasyTable from "@/app/lib/component/EasyTable";
import Input from "@/app/lib/component/Input";
import Pagination from "@/app/lib/component/Pagination";
import Select from "@/app/lib/component/Select";
import Switch from "@/app/lib/component/Switch";
import Tab from "@/app/lib/component/Tab";
import EasyObj from "@/app/lib/dataset/EasyObj";
import { useEasyList } from "@/app/lib/dataset/EasyList";
import { PAGE_CONFIG } from "./initData";
import { usePageData } from "@/app/lib/hooks/usePageData";
import { apiJSON } from "@/app/lib/runtime/api";
import LANG_KO from "./lang.ko";

/**
 * @description 공개 관리자 화면 샘플를 렌더링. 입력/출력 계약을 함께 명시
 * 처리 규칙: 사용자 생성/수정과 시스템 설정 저장은 sample 공개 API를 통해 DB에 반영한다.
 * @param {{ initialDataObj?: Object, initialErrorObj?: Object }} props
 */
const AdminDemoView = ({ initialDataObj, initialErrorObj }) => {

  /* 1. 상수 ======================================================================================================================= */
  const roleBadgeMapObj = {
    admin: "primary",
    editor: "warning",
    user: "neutral",
  };
  const statusBadgeMapObj = {
    active: "success",
    inactive: "neutral",
  };
  const rolePermissionList = LANG_KO.view.rolePermissionList;
  const tabList = LANG_KO.initData.tabList;
  const roleOptionList = LANG_KO.initData.roleOptions;
  const statusOptionList = LANG_KO.initData.statusOptions;
  const userFormSeedObj = {
    name: "",
    email: "",
    role: "user",
    status: "active",
    notifyEmail: false,
    notifySms: false,
    notifyPush: false,
    profileImageName: "",
  };

  /* 2. 데이터 ======================================================================================================================= */
  const { showToast } = useGlobalUi();
  const { mode: pageMode, dataObj, isLoading: pageLoading } = usePageData({
    pageConfig: PAGE_CONFIG,
    initialDataObj,
    initialErrorObj,
  });
  const pageApi = PAGE_CONFIG.API || {};
  const initialUserRowList = dataObj?.users?.result?.sampleAdminUserList || [];
  const initialUserListMetaObj = dataObj?.users?.result?.listMetaObj || {};
  const initialSettingResult = useMemo(
    () => dataObj?.settings?.result || {},
    [dataObj?.settings?.result],
  );
  const ui = EasyObj({
    tabIndex: 0,
    keyword: "",
    isLoadingUserList: false,
    isSavingUser: false,
    isSavingSetting: false,
    drawerState: {
      isOpen: false,
      mode: "create",
      editingId: null,
    },
    userForm: { ...userFormSeedObj },
    formError: "",
  });
  const adminUserList = useEasyList(initialUserRowList);
  const adminUserMetaObj = EasyObj({
    page: Number(initialUserListMetaObj.page || 1),
    size: Number(initialUserListMetaObj.size || 50),
    totalCount: Number(initialUserListMetaObj.totalCount || initialUserRowList.length || 0),
  });
  const savedAdminUserObj = EasyObj({});
  const adminSettingResultObj = EasyObj(initialSettingResult);
  const systemSettingObj = EasyObj(
    initialSettingResult.systemSetting || { ...LANG_KO.view.systemDefault },
  );
  const rolePermissionMapObj = EasyObj(initialSettingResult.rolePermissionMap || {});
  const adminUserPageCount = Math.max(
    1,
    Math.ceil(
      Number(adminUserMetaObj.totalCount || 0) / Math.max(1, Number(adminUserMetaObj.size || 50)),
    ),
  );
  const adminUserRangeStart = adminUserList.length > 0
    ? ((Number(adminUserMetaObj.page || 1) - 1) * Math.max(1, Number(adminUserMetaObj.size || 50))) + 1
    : 0;
  const adminUserRangeEnd = adminUserList.length > 0
    ? adminUserRangeStart + adminUserList.length - 1
    : 0;
  const adminUserTotalText = Number(adminUserMetaObj.totalCount || 0).toLocaleString("ko-KR");
  const adminUserRangeText = adminUserRangeStart > 0
    ? LANG_KO.view.users.totalRangeTemplate
      .replace("{total}", adminUserTotalText)
      .replace("{start}", adminUserRangeStart.toLocaleString("ko-KR"))
      .replace("{end}", adminUserRangeEnd.toLocaleString("ko-KR"))
    : LANG_KO.view.users.totalOnlyTemplate.replace("{total}", adminUserTotalText);

  /* 3. UI ========================================================================================================================= */
  const normalizedKeyword = String(ui.keyword || "").trim().toLowerCase();
  const filteredRows = !normalizedKeyword
    ? adminUserList
    : adminUserList.filter((rowItem) => {
      const targetText = `${rowItem.name} ${rowItem.email} ${LANG_KO.view.roleLabelMap[rowItem.role] || ""}`.toLowerCase();
      return targetText.includes(normalizedKeyword);
    });
  const tableColumnList = [
    {
      key: "profile",
      header: LANG_KO.view.table.profileHeader,
      width: 90,
      render: (rowItem) => (
        <div className="flex items-center justify-center">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-xs font-semibold text-blue-700">
            {String(rowItem?.name || "?").slice(0, 1)}
          </div>
        </div>
      ),
    },
    { key: "name", header: LANG_KO.view.table.nameHeader, width: 120 },
    { key: "email", header: LANG_KO.view.table.emailHeader, align: "left", width: "2fr" },
    {
      key: "role",
      header: LANG_KO.view.table.roleHeader,
      width: 130,
      render: (rowItem) => (
        <Badge variant={roleBadgeMapObj[rowItem?.role] || "neutral"} pill>
          {LANG_KO.view.roleLabelMap[rowItem?.role] || rowItem?.role}
        </Badge>
      ),
    },
    {
      key: "status",
      header: LANG_KO.view.table.statusHeader,
      width: 100,
      render: (rowItem) => (
        <Badge variant={statusBadgeMapObj[rowItem?.status] || "neutral"} pill>
          {LANG_KO.view.statusLabelMap[rowItem?.status] || rowItem?.status}
        </Badge>
      ),
    },
    { key: "createdAt", header: LANG_KO.view.table.createdAtHeader, width: 120 },
    {
      key: "actions",
      header: LANG_KO.view.table.actionsHeader,
      width: 120,
      render: (rowItem) => (
        <Button
          size="sm"
          variant="secondary"
          onClick={() => openEditDrawer(rowItem)}
        >
          {LANG_KO.view.users.editButton}
        </Button>
      ),
    },
  ];

  /* 4. 팝업 ======================================================================================================================= */

  // 없음

  /* 5. 기타 ======================================================================================================================= */

  // 없음

  /* 6. 커스텀 훅 =================================================================================================================== */

  // 없음

  /* 7. 함수 ======================================================================================================================= */

  /**
   * @description 사용자 생성 모드 드로어를 열고 폼을 초기화
   * 부작용: drawer/userForm/formError 상태가 생성 모드 기준으로 초기화된다.
   */
  const openCreateDrawer = () => {
    ui.drawerState = {
      isOpen: true,
      mode: "create",
      editingId: null,
    };
    ui.userForm = { ...userFormSeedObj };
    ui.formError = "";
  };

  /**
   * @description 사용자 수정 모드 드로어 열기와 기존 행 데이터 주입
   * 부작용: drawerState/userForm/formError가 선택한 사용자 기준으로 갱신된다.
   * @param {Object} rowItem
   */
  const openEditDrawer = (rowItem) => {
    ui.drawerState = {
      isOpen: true,
      mode: "edit",
      editingId: rowItem?.id || null,
    };
    ui.userForm = {
      name: rowItem?.name || "",
      email: rowItem?.email || "",
      role: rowItem?.role || "user",
      status: rowItem?.status || LANG_KO.view.misc.defaultStatusCode,
      notifyEmail: Boolean(rowItem?.notifyEmail),
      notifySms: Boolean(rowItem?.notifySms),
      notifyPush: Boolean(rowItem?.notifyPush),
      profileImageName: "",
    };
    ui.formError = "";
  };

  /**
   * @description 드로어 닫기와 입력 오류 상태 초기화
   * 부작용: drawerState를 생성 기본값으로 되돌리고 formError를 비운다.
   */
  const closeDrawer = () => {
    ui.drawerState = {
      isOpen: false,
      mode: "create",
      editingId: null,
    };
    ui.formError = "";
  };

  /**
   * @description 사용자 목록 재조회
   * 처리 규칙: GET 응답의 sampleAdminUserList를 adminUserList에 동기화한다.
   * @returns {Promise<void>}
   */
  const loadAdminUserList = async (nextPage = Number(adminUserMetaObj.page || 1)) => {
    ui.isLoadingUserList = true;
    try {
      const userListQueryParams = new URLSearchParams();
      userListQueryParams.set("page", String(Math.max(1, Number(nextPage || 1))));
      userListQueryParams.set("size", String(Math.max(1, Number(adminUserMetaObj.size || 50))));
      const listBasePath = typeof pageApi.usersList === "string"
        ? String(pageApi.usersList || "").split("?", 1)[0]
        : String(pageApi.usersList?.path || "").split("?", 1)[0];
      const usersListPath = `${listBasePath}?${userListQueryParams.toString()}`;
      const usersListSpec = !pageApi.usersList || typeof pageApi.usersList !== "object"
        ? usersListPath
        : {
            ...pageApi.usersList,
            path: usersListPath,
      };
      const userListResponse = await apiJSON(usersListSpec);
      const nextListMetaObj = userListResponse?.result?.listMetaObj || {};
      adminUserList.copy(userListResponse?.result?.sampleAdminUserList || []);
      adminUserMetaObj.copy({
        page: Number(nextListMetaObj.page || nextPage || 1),
        size: Number(nextListMetaObj.size || adminUserMetaObj.size || 50),
        totalCount: Number(nextListMetaObj.totalCount || 0),
      });
    } catch (err) {
      showToast(err?.message || LANG_KO.view.users.listLoadFailed, { type: "error" });
    } finally {
      ui.isLoadingUserList = false;
    }
  };

  /**
   * @description 사용자 폼 저장과 목록 재조회
   * 실패 동작: 이름/이메일 누락 또는 API 실패 시 formError와 토스트 갱신
  */
  const saveUser = async () => {
    const userName = String(ui.userForm.name || "").trim();
    const email = String(ui.userForm.email || "").trim();
    if (!userName) {
      ui.formError = LANG_KO.view.users.nameRequired;
      return;
    }
    if (!email) {
      ui.formError = LANG_KO.view.users.emailRequired;
      return;
    }
    ui.isSavingUser = true;
    ui.formError = "";
    try {
      const userBodyObj = {
        name: userName,
        email,
        role: ui.userForm.role,
        status: ui.userForm.status,
        notifyEmail: Boolean(ui.userForm.notifyEmail),
        notifySms: Boolean(ui.userForm.notifySms),
        notifyPush: Boolean(ui.userForm.notifyPush),
        profileImageUrl: String(ui.userForm.profileImageName || "").trim(),
      };
      const isCreate = ui.drawerState.mode === "create";
      const detailTemplatePath = typeof pageApi.userDetail === "string"
        ? pageApi.userDetail
        : String(pageApi.userDetail?.path || "");
      const userDetailPath = detailTemplatePath.replace(":id", String(ui.drawerState.editingId));
      let requestSpec = pageApi.userCreate;
      if (!isCreate) {
        requestSpec = !pageApi.userDetail || typeof pageApi.userDetail !== "object"
          ? userDetailPath
          : {
              ...pageApi.userDetail,
              path: userDetailPath,
            };
      }
      const userSaveResponse = await apiJSON(
        requestSpec,
        {
          method: isCreate ? "POST" : "PUT",
          body: userBodyObj,
        },
      );
      savedAdminUserObj.copy(userSaveResponse?.result || {});
      showToast(
        isCreate ? LANG_KO.view.users.saveCreatedToast : LANG_KO.view.users.saveUpdatedToast,
        { type: "success" },
      );
      closeDrawer();
      await loadAdminUserList();
    } catch (err) {
      ui.formError = err?.message || LANG_KO.view.users.saveFailed;
      showToast(ui.formError, { type: "error" });
    } finally {
      ui.isSavingUser = false;
    }
  };

  /**
   * @description 시스템 설정 저장과 최신 응답 상태 반영
   * 처리 규칙: 저장 성공 시 adminSettingResultObj/systemSettingObj/rolePermissionMapObj 순차 동기화
   */
  const saveSettings = async () => {
    ui.isSavingSetting = true;
    try {
      const settingsResponse = await apiJSON(
        pageApi.settingsUpdate,
        {
          method: "PUT",
          body: {
            siteName: String(systemSettingObj.siteName || "").trim(),
            adminEmail: String(systemSettingObj.adminEmail || "").trim(),
            maintenanceMode: Boolean(systemSettingObj.maintenanceMode),
            sessionTimeout: Number(systemSettingObj.sessionTimeout || 0),
            maxUploadMb: Number(systemSettingObj.maxUploadMb || 0),
          },
        },
      );
      adminSettingResultObj.copy(settingsResponse?.result || {});
      systemSettingObj.copy(adminSettingResultObj.systemSetting || {});
      rolePermissionMapObj.copy(adminSettingResultObj.rolePermissionMap || {});
      showToast(LANG_KO.view.settings.saveToast, { type: "success" });
    } catch (err) {
      showToast(err?.message || LANG_KO.view.settings.saveFailed, { type: "error" });
    } finally {
      ui.isSavingSetting = false;
    }
  };

  /* 8. useEffect ================================================================================================================== */
  /**
   * @description SSR 초기 적재 스냅샷 변경 시 사용자 목록/설정/권한 맵 반영
   * 처리 규칙: users는 EasyList.copy, settings는 EasyObj.copy로 각각 동기화
   */
  useEffect(() => {
    adminUserList.copy(dataObj?.users?.result?.sampleAdminUserList || []);
    adminUserMetaObj.copy({
      page: Number(dataObj?.users?.result?.listMetaObj?.page || 1),
      size: Number(dataObj?.users?.result?.listMetaObj?.size || 50),
      totalCount: Number(dataObj?.users?.result?.listMetaObj?.totalCount || 0),
    });
    adminSettingResultObj.copy(initialSettingResult);
    systemSettingObj.copy(initialSettingResult.systemSetting || { ...LANG_KO.view.systemDefault });
    rolePermissionMapObj.copy(initialSettingResult.rolePermissionMap || {});
  }, [adminSettingResultObj, adminUserList, adminUserMetaObj, dataObj?.users?.result?.listMetaObj?.page, dataObj?.users?.result?.listMetaObj?.size, dataObj?.users?.result?.listMetaObj?.totalCount, dataObj?.users?.result?.sampleAdminUserList, initialSettingResult, rolePermissionMapObj, systemSettingObj]);

  /* 9. 내부 컴포넌트 ============================================================================================================== */

  // 없음

  /* 10. 렌더링 ==================================================================================================================== */
  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6 lg:px-8" data-page-mode={pageMode}>
      <section className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">{LANG_KO.view.section.title}</h1>
        <p className="mt-2 text-sm text-gray-600">
          {LANG_KO.view.section.subtitle}
        </p>
      </section>

      <Card title={`${LANG_KO.view.card.panelTitle} · ${Number(adminUserMetaObj.totalCount || 0).toLocaleString("ko-KR")}${LANG_KO.view.card.userCountSuffix}`}>
        <Tab
          tabIndex={ui.tabIndex}
          onChange={(event) => {
            ui.tabIndex = Number(event?.target?.value || 0);
          }}
        >
          <Tab.Item title={tabList[0].label}>
            <div className="space-y-3">
              <div className="flex flex-col gap-2 md:flex-row md:items-center">
                <div className="flex-1">
                  <Input
                    dataObj={ui}
                    dataKey="keyword"
                    placeholder={LANG_KO.view.users.searchPlaceholder}
                  />
                </div>
                <Button
                  variant="secondary"
                  onClick={() => {
                    ui.keyword = "";
                  }}
                  className="w-full sm:w-auto"
                >
                  {LANG_KO.view.users.resetButton}
                </Button>
                <Button
                  variant="primary"
                  onClick={openCreateDrawer}
                  className="w-full sm:w-auto"
                >
                  {LANG_KO.view.users.addButton}
                </Button>
              </div>
              <EasyTable
                data={filteredRows}
                columns={tableColumnList}
                loading={Boolean(pageLoading || ui.isLoadingUserList)}
                pageSize={Math.max(1, filteredRows.length || adminUserList.length || 1)}
                preserveRowSpace={false}
                empty={LANG_KO.view.table.empty}
                rowKey={(rowItem, rowIndex) => rowItem?.id ?? rowIndex}
              />
              <div className="flex flex-col gap-3 text-sm text-gray-500 md:flex-row md:items-center md:justify-between">
                <p>{adminUserRangeText}</p>
                {adminUserPageCount > 1 ? (
                  <Pagination
                    page={Number(adminUserMetaObj.page || 1)}
                    pageCount={adminUserPageCount}
                    onChange={(nextPage) => {
                      loadAdminUserList(nextPage);
                    }}
                  />
                ) : null}
              </div>
            </div>
          </Tab.Item>

          <Tab.Item title={tabList[1].label}>
            <div className="grid gap-3 md:grid-cols-3">
              {roleOptionList.map((roleItem) => (
                <article
                  key={roleItem.value}
                  className="rounded-lg border border-gray-200 bg-gray-50 p-4"
                >
                  <h3 className="text-base font-semibold text-gray-900">
                    {roleItem.text}
                  </h3>
                  <div className="mt-3 space-y-2">
                    {rolePermissionList.map((permissionItem) => (
                      <div key={permissionItem.key} className="flex items-center">
                        <Checkbox
                          dataObj={rolePermissionMapObj}
                          dataKey={`${roleItem.value}.${permissionItem.key}`}
                          disabled
                          label={permissionItem.label}
                        />
                      </div>
                    ))}
                  </div>
                </article>
              ))}
            </div>
          </Tab.Item>

          <Tab.Item title={tabList[2].label}>
            <div className="grid gap-3 md:grid-cols-2">
              <label className="block space-y-1">
                <span className="text-sm font-medium text-gray-700">{LANG_KO.view.settings.siteNameLabel}</span>

                <Input
                  dataObj={systemSettingObj}
                  dataKey="siteName"
                />
              </label>

              <label className="block space-y-1">
                <span className="text-sm font-medium text-gray-700">{LANG_KO.view.settings.adminEmailLabel}</span>

                <Input
                  dataObj={systemSettingObj}
                  dataKey="adminEmail"
                  type="email"
                />
              </label>

              <label className="block space-y-1">
                <span className="text-sm font-medium text-gray-700">{LANG_KO.view.settings.sessionTimeoutLabel}</span>

                <Input
                  dataObj={systemSettingObj}
                  dataKey="sessionTimeout"
                  type="number"
                />
              </label>

              <label className="block space-y-1">
                <span className="text-sm font-medium text-gray-700">{LANG_KO.view.settings.maxUploadLabel}</span>

                <Input
                  dataObj={systemSettingObj}
                  dataKey="maxUploadMb"
                  type="number"
                />
              </label>

              <div className="md:col-span-2">
                <label className="flex items-center gap-2 text-sm text-gray-700">

                  <Switch
                    dataObj={systemSettingObj}
                    dataKey="maintenanceMode"
                  />
                  {LANG_KO.view.settings.maintenanceModeLabel}
                </label>
              </div>
            </div>
            <div className="mt-4">
              <Button
                variant="primary"
                className="w-full sm:w-auto"
                onClick={saveSettings}
                disabled={ui.isSavingSetting}
              >
                {LANG_KO.view.settings.saveButton}
              </Button>
            </div>
          </Tab.Item>
        </Tab>
      </Card>

      <Drawer
        isOpen={ui.drawerState.isOpen}
        onClose={closeDrawer}
        side="right"
        size="min-[1468px]:w-[500px]"
        collapseButton
      >
        <div className="space-y-4 p-5">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              {ui.drawerState.mode === "create" ? LANG_KO.view.drawer.createTitle : LANG_KO.view.drawer.editTitle}
            </h2>
            <p className="mt-1 text-sm text-gray-500">
              {ui.drawerState.mode === "create"
                ? LANG_KO.view.drawer.createSubtitle
                : `${LANG_KO.view.drawer.editSubtitlePrefix}${ui.drawerState.editingId || "-"}`}
            </p>
          </div>

          {ui.formError ? (
            <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {ui.formError}
            </div>
          ) : null}

          <label className="block space-y-1">
            <span className="text-sm font-medium text-gray-700">{LANG_KO.view.drawer.profileImageLabel}</span>

            {/* raw file input 예외 사유: 공용 lib/component에 파일 선택 전용 컴포넌트가 없어 브라우저 기본 picker 사용 */}
            <input
              type="file"
              className="block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700"
              onChange={(event) => {
                const nextFile = event?.target?.files?.[0];
                ui.userForm.profileImageName = nextFile?.name || "";
              }}
            />
            {ui.userForm.profileImageName ? (
              <p className="text-xs text-gray-500">{ui.userForm.profileImageName}</p>
            ) : null}
          </label>

          <label className="block space-y-1">
            <span className="text-sm font-medium text-gray-700">{LANG_KO.view.drawer.nameLabel}</span>
            <Input
              dataObj={ui}
              dataKey="userForm.name"
              placeholder={LANG_KO.view.drawer.namePlaceholder}
            />
          </label>

          <label className="block space-y-1">
            <span className="text-sm font-medium text-gray-700">{LANG_KO.view.drawer.emailLabel}</span>
            <Input
              dataObj={ui}
              dataKey="userForm.email"
              readOnly={ui.drawerState.mode === "edit"}
              placeholder={LANG_KO.view.drawer.emailPlaceholder}
              type="email"
            />
          </label>

          <label className="block space-y-1">
            <span className="text-sm font-medium text-gray-700">{LANG_KO.view.drawer.roleLabel}</span>
            <Select
              dataObj={ui}
              dataKey="userForm.role"
              dataList={roleOptionList}
            />
          </label>

          <label className="block space-y-1">
            <span className="text-sm font-medium text-gray-700">{LANG_KO.view.drawer.statusLabel}</span>
            <Select
              dataObj={ui}
              dataKey="userForm.status"
              dataList={statusOptionList}
            />
          </label>

          <div className="space-y-2">
            <span className="text-sm font-medium text-gray-700">{LANG_KO.view.drawer.notifyLabel}</span>
            <div className="flex flex-wrap gap-4">
              <Switch label={LANG_KO.view.drawer.notifyEmailLabel} dataObj={ui} dataKey="userForm.notifyEmail" />
              <Switch label={LANG_KO.view.drawer.notifySmsLabel} dataObj={ui} dataKey="userForm.notifySms" />
              <Switch label={LANG_KO.view.drawer.notifyPushLabel} dataObj={ui} dataKey="userForm.notifyPush" />
            </div>
          </div>

          <div className="flex flex-col-reverse gap-2 pt-2 sm:flex-row sm:items-center sm:justify-end">
            <Button variant="secondary" onClick={closeDrawer} className="w-full sm:w-auto">
              {LANG_KO.view.drawer.cancelButton}
            </Button>
            <Button onClick={saveUser} className="w-full sm:w-auto" disabled={ui.isSavingUser}>
              {LANG_KO.view.drawer.saveButton}
            </Button>
          </div>
        </div>
      </Drawer>
    </div>
  );
};

export default AdminDemoView;
