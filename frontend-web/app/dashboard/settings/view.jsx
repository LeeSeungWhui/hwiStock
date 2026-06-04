"use client";

/**
 * 파일명: dashboard/settings/view.jsx
 * 설명: hwiStock 읽기 전용 운영 정책 뷰(정책/연결 탭)
 */

import { useEffect } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { normalizePageConfig } from "@/app/lib/runtime/pageData";
import { usePageData } from "@/app/lib/hooks/usePageData";
import Badge from "@/app/lib/component/Badge";
import Card from "@/app/lib/component/Card";
import Input from "@/app/lib/component/Input";
import Switch from "@/app/lib/component/Switch";
import Tab from "@/app/lib/component/Tab";
import { PAGE_CONFIG } from "./initData";
import LANG_KO from "./lang.ko";
import EasyObj from "@/app/lib/dataset/EasyObj";

const SettingsView = ({ initialDataObj, initialErrorObj }) => {

  /* 1. 상수 ======================================================================================================================= */
  const settingsTabObj = {
    POLICY: "policy",
    CONNECTION: "connection",
  };
  const connectionDisplaySeedObj = {
    ...LANG_KO.initData.connectionDefault,
  };
  const defaultProfileObj = {
    userId: "",
    userNm: "",
    userEml: "",
    roleCd: "user",
    notifyEmail: false,
    notifySms: false,
    notifyPush: false,
  };

  /* 2. 데이터 ======================================================================================================================= */
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const searchParamText = searchParams?.toString() || "";
  const pageApi = PAGE_CONFIG.API || {};
  const hasProfileEndpoint = Boolean(pageApi.profileMe);
  const profileMeObj = EasyObj({ ...defaultProfileObj });
  const ui = EasyObj({
    connectionDisplay: { ...connectionDisplaySeedObj },
    activeTabIndex: 0,
    isLoadingProfile: true,
    error: null,
  });
  const pageMode = normalizePageConfig(PAGE_CONFIG).MODE;
  const { dataObj, errorObj, isLoading: pageLoading } = usePageData({
    pageConfig: PAGE_CONFIG,
    initialDataObj,
    initialErrorObj,
  });

  /* 3. UI ========================================================================================================================= */

  /* 7. 함수 ======================================================================================================================= */
  const syncTabQuery = (nextTabIndex) => {
    if (!pathname) return;
    const nextQueryValue = Number(nextTabIndex) === 1 ? settingsTabObj.CONNECTION : "";
    const nextParams = new URLSearchParams(searchParams?.toString() || "");
    if (nextQueryValue) {
      nextParams.set("tab", nextQueryValue);
    } else {
      nextParams.delete("tab");
    }
    const nextQuery = nextParams.toString();
    const href = nextQuery ? `${pathname}?${nextQuery}` : pathname;
    router.replace(href, { scroll: false });
  };

  const handleTabChange = (nextValue) => {
    const nextTabIndex = Number(nextValue) === 1 ? 1 : 0;
    ui.activeTabIndex = nextTabIndex;
    syncTabQuery(nextTabIndex);
  };

  /* 4. 팝업 ======================================================================================================================= */

  // 없음

  /* 5. 기타 ======================================================================================================================= */

  // 없음

  /* 6. 커스텀 훅 =================================================================================================================== */

  // 없음

  /* 8. useEffect ================================================================================================================== */
  useEffect(() => {
    const queryTab = String(searchParams?.get("tab") || "").trim().toLowerCase();
    const nextTabIndex = queryTab === settingsTabObj.CONNECTION ? 1 : 0;
    if (ui.activeTabIndex !== nextTabIndex) {
      ui.activeTabIndex = nextTabIndex;
    }
  }, [searchParams, searchParamText, settingsTabObj.CONNECTION, ui]);

  useEffect(() => {
    ui.isLoadingProfile = Boolean(pageLoading);
    if (!hasProfileEndpoint) {
      ui.error = { message: LANG_KO.view.error.profileEndpointMissing };
      ui.isLoadingProfile = false;
      return;
    }
    if (errorObj?.profileMe) {
      ui.error = {
        message: errorObj.profileMe?.message || LANG_KO.view.error.profileLoadFailed,
        requestId: errorObj.profileMe?.requestId,
      };
      ui.isLoadingProfile = false;
      return;
    }
    if (dataObj?.profileMe?.result) {
      profileMeObj.copy(dataObj.profileMe.result);
      ui.error = null;
    }
  }, [dataObj?.profileMe?.result, errorObj?.profileMe, hasProfileEndpoint, pageLoading, profileMeObj, ui]);

  /* 9. 내부 컴포넌트 ============================================================================================================== */

  // 없음

  /* 10. 렌더링 ==================================================================================================================== */
  return (
    <div className="space-y-3" data-page-mode={pageMode} data-readonly="true">
      {ui.error?.message && (
        <section aria-label={LANG_KO.view.error.profileLoadFailed}>
          <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">
            <div>{ui.error.message}</div>
            {ui.error.requestId && (
              <div className="mt-1 text-xs text-red-700/80">
                {LANG_KO.view.error.requestIdLabel}: {ui.error.requestId}
              </div>
            )}
          </div>
        </section>
      )}

      <Card title={LANG_KO.view.card.title}>
        <p className="mb-3 text-sm text-gray-500">{LANG_KO.view.card.subtitle}</p>
        <Tab
          key={`settings-tab-${ui.activeTabIndex}`}
          tabIndex={ui.activeTabIndex}
          onValueChange={handleTabChange}
        >
          <Tab.Item title={LANG_KO.view.tab.policy}>
            <div className="space-y-3">
              {ui.isLoadingProfile ? (
                <div className="rounded-md border border-gray-200 bg-gray-50 px-4 py-6 text-sm text-gray-600">
                  {LANG_KO.view.policy.loading}
                </div>
              ) : (
                <>
                  <label className="block space-y-1">
                    <span className="text-sm font-medium text-gray-700">{LANG_KO.view.policy.nameLabel}</span>
                    <Input dataObj={profileMeObj} dataKey="userNm" readOnly />
                  </label>

                  <label className="block space-y-1">
                    <span className="text-sm font-medium text-gray-700">{LANG_KO.view.policy.emailLabel}</span>
                    <Input dataObj={profileMeObj} dataKey="userEml" readOnly />
                  </label>

                  <div className="space-y-1">
                    <span className="text-sm font-medium text-gray-700">{LANG_KO.view.policy.roleLabel}</span>
                    <div>
                      <Badge variant={LANG_KO.view.roleBadge[profileMeObj.roleCd] || "neutral"} pill>
                        {profileMeObj.roleCd || "user"}
                      </Badge>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <span className="text-sm font-medium text-gray-700">{LANG_KO.view.policy.notifyLabel}</span>
                    <div className="flex flex-wrap gap-4">
                      <Switch
                        label={LANG_KO.view.policy.notifyEmailLabel}
                        dataObj={profileMeObj}
                        dataKey="notifyEmail"
                        disabled
                      />
                      <Switch
                        label={LANG_KO.view.policy.notifySmsLabel}
                        dataObj={profileMeObj}
                        dataKey="notifySms"
                        disabled
                      />
                      <Switch
                        label={LANG_KO.view.policy.notifyPushLabel}
                        dataObj={profileMeObj}
                        dataKey="notifyPush"
                        disabled
                      />
                    </div>
                  </div>
                </>
              )}
            </div>
          </Tab.Item>

          <Tab.Item title={LANG_KO.view.tab.connection}>
            <div className="space-y-3">
              <label className="block space-y-1">
                <span className="text-sm font-medium text-gray-700">{LANG_KO.view.connection.serviceLabel}</span>
                <Input dataObj={ui} dataKey="connectionDisplay.serviceName" readOnly />
              </label>

              <div className="space-y-1">
                <span className="text-sm font-medium text-gray-700">{LANG_KO.view.connection.maintenanceLabel}</span>
                <Switch
                  label={
                    ui.connectionDisplay.maintenanceMode
                      ? LANG_KO.view.connection.maintenanceActive
                      : LANG_KO.view.connection.maintenanceInactive
                  }
                  dataObj={ui}
                  dataKey="connectionDisplay.maintenanceMode"
                  disabled
                />
              </div>

              <label className="block space-y-1">
                <span className="text-sm font-medium text-gray-700">{LANG_KO.view.connection.sessionTimeoutLabel}</span>
                <Input
                  dataObj={ui}
                  dataKey="connectionDisplay.sessionTimeoutMinutes"
                  readOnly
                />
              </label>

              <label className="block space-y-1">
                <span className="text-sm font-medium text-gray-700">{LANG_KO.view.connection.dataFeedLabel}</span>
                <Input dataObj={ui} dataKey="connectionDisplay.dataFeedStatus" readOnly />
              </label>
            </div>
          </Tab.Item>
        </Tab>
      </Card>
    </div>
  );
};

export default SettingsView;
