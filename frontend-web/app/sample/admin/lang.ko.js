/**
 * 파일명: app/sample/admin/lang.ko.js
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: admin 경로 한국어 리소스
 */

export const LANG_KO = {
  page: {
    metadataTitle: "Admin Sample | MyWebTemplate",
    metadataDescription: "공개 관리자 화면 샘플",
  },
  initData: {
    tabList: [
      { key: "users", label: "사용자 목록" },
      { key: "roles", label: "역할 관리" },
      { key: "settings", label: "시스템 설정" },
    ],
    roleOptions: [
      { value: "admin", text: "관리자" },
      { value: "editor", text: "편집자" },
      { value: "user", text: "일반사용자" },
    ],
    statusOptions: [
      { value: "active", text: "활성" },
      { value: "inactive", text: "비활성" },
    ],
    userRows: [
      {
        id: 1,
        name: "김관리",
        email: "admin@demo.demo",
        role: "admin",
        status: "active",
        createdAt: "2026-01-15",
        notifyEmail: true,
        notifySms: false,
        notifyPush: true,
        profileImageUrl: "",
      },
      {
        id: 2,
        name: "박에디터",
        email: "editor@demo.demo",
        role: "editor",
        status: "active",
        createdAt: "2026-01-20",
        notifyEmail: true,
        notifySms: true,
        notifyPush: false,
        profileImageUrl: "",
      },
      {
        id: 3,
        name: "이사용자",
        email: "user@demo.demo",
        role: "user",
        status: "inactive",
        createdAt: "2026-02-03",
        notifyEmail: false,
        notifySms: false,
        notifyPush: false,
        profileImageUrl: "",
      },
    ],
  },
  view: {
    roleLabelMap: {
      admin: "관리자",
      editor: "편집자",
      user: "일반사용자",
    },
    statusLabelMap: {
      active: "활성",
      inactive: "비활성",
    },
    rolePermissionList: [
      { key: "manageUser", label: "사용자 관리" },
      { key: "editContent", label: "콘텐츠 편집" },
      { key: "changeSetting", label: "설정 변경" },
      { key: "viewLog", label: "로그 조회" },
      { key: "deleteData", label: "데이터 삭제" },
    ],
    systemDefault: {
      siteName: "MyWebTemplate",
      adminEmail: "admin@demo.demo",
      maintenanceMode: false,
      sessionTimeout: 60,
      maxUploadMb: 30,
    },
    section: {
      title: "관리자 화면 샘플",
      subtitle: "사용자/권한/설정 페이지 구성을 공개 샘플 형태로 보여줍니다.",
    },
    card: {
      loadingTitle: "로딩 중",
      loadingBody: "관리자 화면 데이터를 준비하는 중입니다...",
      panelTitle: "관리자 패널",
      userCountSuffix: "명",
    },
    table: {
      profileHeader: "프로필",
      nameHeader: "이름",
      emailHeader: "이메일",
      roleHeader: "역할",
      statusHeader: "상태",
      createdAtHeader: "가입일",
      actionsHeader: "관리",
      empty: "데이터가 없습니다.",
    },
    users: {
      searchPlaceholder: "이름/이메일/역할 검색",
      resetButton: "초기화",
      addButton: "사용자 추가",
      totalRangeTemplate: "총 {total}명 중 {start}-{end}명",
      totalOnlyTemplate: "총 {total}명",
      editButton: "수정",
      listLoadFailed: "사용자 목록을 불러오지 못했습니다.",
      saveCreatedToast: "사용자가 등록되었습니다.",
      saveUpdatedToast: "사용자 정보가 저장되었습니다.",
      nameRequired: "이름을 입력해주세요.",
      emailRequired: "이메일을 입력해주세요.",
      saveFailed: "사용자 저장에 실패했습니다.",
    },
    settings: {
      siteNameLabel: "사이트명",
      adminEmailLabel: "관리자 이메일",
      sessionTimeoutLabel: "세션 타임아웃(분)",
      maxUploadLabel: "최대 업로드 크기(MB)",
      maintenanceModeLabel: "점검 모드",
      saveButton: "저장",
      saveToast: "설정이 저장되었습니다",
      saveFailed: "설정 저장에 실패했습니다.",
    },
    misc: {
      defaultStatusCode: "active",
    },
    drawer: {
      createTitle: "사용자 추가",
      editTitle: "사용자 수정",
      createSubtitle: "신규 사용자를 등록합니다.",
      editSubtitlePrefix: "사용자 번호 #",
      profileImageLabel: "프로필 이미지",
      nameLabel: "이름",
      namePlaceholder: "이름을 입력해주세요",
      emailLabel: "이메일",
      emailPlaceholder: "이메일을 입력해주세요",
      roleLabel: "역할",
      statusLabel: "상태",
      notifyLabel: "알림 설정",
      notifyEmailLabel: "이메일 알림",
      notifySmsLabel: "SMS 알림",
      notifyPushLabel: "푸시 알림",
      cancelButton: "취소",
      saveButton: "저장",
    },
  },
};

export default LANG_KO;
