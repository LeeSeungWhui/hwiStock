/**
 * 파일명: app/dashboard/settings/lang.ko.js
 * 설명: hwiStock 운영 정책 경로 한국어 리소스
 */

export const LANG_KO = {
  page: {
    metadataTitle: "hwiStock 운영 정책",
  },
  initData: {
    connectionDefault: {
      serviceName: "hwiStock",
      maintenanceMode: false,
      sessionTimeoutMinutes: 60,
      dataFeedStatus: "읽기 전용 스냅샷",
    },
  },
  view: {
    roleBadge: {
      admin: "primary",
      manager: "warning",
      user: "neutral",
    },
    error: {
      profileEndpointMissing: "운영자 프로필 API 경로가 설정되지 않았습니다.",
      profileLoadFailed: "운영 정책 정보를 불러오지 못했습니다.",
      requestIdLabel: "requestId",
    },
    card: {
      title: "운영 정책",
      subtitle: "읽기 전용 · 정책·연결 상태 조회만 지원합니다.",
    },
    tab: {
      policy: "운영 정책",
      connection: "연결 상태",
    },
    policy: {
      loading: "운영 정책을 불러오는 중...",
      nameLabel: "운영자",
      emailLabel: "연락 이메일",
      roleLabel: "역할",
      notifyLabel: "알림 정책(조회)",
      notifyEmailLabel: "이메일 알림",
      notifySmsLabel: "SMS 알림",
      notifyPushLabel: "푸시 알림",
    },
    connection: {
      serviceLabel: "서비스",
      maintenanceLabel: "점검 모드",
      maintenanceActive: "활성화",
      maintenanceInactive: "비활성화",
      sessionTimeoutLabel: "세션 타임아웃(분)",
      dataFeedLabel: "데이터 피드",
    },
  },
};

export default LANG_KO;
