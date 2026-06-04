"use client";

/**
 * 파일명: SharedStore.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Zustand 기반 전역 공유 스토어
 */

import { create } from 'zustand';
import { COMMON_COMPONENT_LANG_KO } from '@/app/common/i18n/lang.ko';

export const useSharedStore = create((set, get) => ({

  // 세션/사용자 메타
  user: null,
  setUser: (user) => set({ user }),
  userJson: null,
  setUserJson: (userJson) => set({ userJson }),
  config: {},
  setConfig: (config) => set({ config: config && typeof config === 'object' ? config : {} }),
  shared: {},
  setShared: (patch) => set((storeState) => ({ shared: { ...storeState.shared, ...(patch || {}) } })),

  // 로딩
  loadingCounter: 0,
  isLoading: false,
  updateLoading: (delta = 0) => set((storeState) => {
    const nextCounter = Math.max(0, (storeState.loadingCounter || 0) + delta);
    return { loadingCounter: nextCounter, isLoading: nextCounter > 0 };
  }),
  setLoading: (nextLoading) => set({ isLoading: Boolean(nextLoading), loadingCounter: nextLoading ? 1 : 0 }),

  // 알림
  alert: { show: false, title: '', message: '', type: 'info', onClick: undefined, onFocus: undefined },
  showAlert: (message, opts = {}) => set({
    alert: {
      show: true,
      title: opts.title || COMMON_COMPONENT_LANG_KO.alert.title,
      message,
      type: opts.type || 'info',
      onClick: typeof opts.onClick === 'function' ? opts.onClick : undefined,
      onFocus: typeof opts.onFocus === 'function' ? opts.onFocus : undefined,
    },
  }),
  hideAlert: () => set({ alert: { show: false, title: '', message: '', type: 'info', onClick: undefined, onFocus: undefined } }),

  // 확인(프라미스 기반)
  confirm: {
    show: false,
    title: '',
    message: '',
    type: 'info',
    confirmText: COMMON_COMPONENT_LANG_KO.confirm.confirmText,
    cancelText: COMMON_COMPONENT_LANG_KO.confirm.cancelText,
    onFocus: undefined,
  },
  confirmResolve: null,
  showConfirm: (message, opts = {}) =>
    new Promise((resolve) => {
      set({
        confirm: {
          show: true,
          title: opts.title || COMMON_COMPONENT_LANG_KO.confirm.title,
          message,
          type: opts.type || 'info',
          confirmText: opts.confirmText || COMMON_COMPONENT_LANG_KO.confirm.confirmText,
          cancelText: opts.cancelText || COMMON_COMPONENT_LANG_KO.confirm.cancelText,
          onConfirm: opts.onConfirm,
          onCancel: opts.onCancel,
          onFocus: typeof opts.onFocus === 'function' ? opts.onFocus : undefined,
        },
        confirmResolve: resolve,
      });
    }),
  hideConfirm: (confirmed) => {
    const { confirm, confirmResolve } = get();
    try {
      if (confirmed && typeof confirm.onConfirm === 'function') confirm.onConfirm();
      if (!confirmed && typeof confirm.onCancel === 'function') confirm.onCancel();
      if (typeof confirmResolve === 'function') confirmResolve(Boolean(confirmed));
    } finally {
      set({
        confirm: {
          show: false,
          title: '',
          message: '',
          type: 'info',
          confirmText: COMMON_COMPONENT_LANG_KO.confirm.confirmText,
          cancelText: COMMON_COMPONENT_LANG_KO.confirm.cancelText,
          onFocus: undefined,
        },
        confirmResolve: null,
      });
    }
  },

  // 토스트
  toast: { show: false, message: '', type: 'info', position: 'bottom-center', duration: 3000 },
  showToast: (message, opts = {}) => set({
    toast: {
      show: true,
      message,
      type: opts.type || 'info',
      position: opts.position || 'bottom-center',
      duration: typeof opts.duration === 'number' ? opts.duration : 3000,
    },
  }),
  hideToast: () => set({ toast: { show: false, message: '', type: 'info', position: 'bottom-center', duration: 3000 } }),
}));

// 편의 훅: 서버/SSR 경고 방지를 위해 개별 셀렉터로 안정값만 반환

/**
 * @description 사용자 캐시 상태(user)와 setter를 반환. 입력/출력 계약을 함께 명시
 * @returns {{ user: any, setUser: Function }}
 */
export const useUser = () => {
  const user = useSharedStore((storeState) => storeState.user);
  const setUser = useSharedStore((storeState) => storeState.setUser);
  return { user, setUser };
};

/**
 * @description React 훅 컨텍스트 밖에서 shared 스냅샷을 안전하게 조회
 * @returns {Object}
 */
export const getSharedSnapshot = () => {
  const storeState = useSharedStore.getState?.();
  if (storeState?.shared && typeof storeState.shared === 'object') return storeState.shared;
  return {};
};

/**
 * @description 공용 shared 상태와 patch setter를 반환. 입력/출력 계약을 함께 명시
 * @returns {{ shared: Object, setShared: Function }}
 */
export const useSharedData = () => {
  const shared = useSharedStore((storeState) => storeState.shared);
  const setShared = useSharedStore((storeState) => storeState.setShared);
  return { shared, setShared };
};

/**
 * @description 전역 UI 상태/액션(loading, alert, confirm, toast)을 반환
 * @returns {Object}
 */
export const useGlobalUi = () => {
  const isLoading = useSharedStore((storeState) => storeState.isLoading);
  const setLoading = useSharedStore((storeState) => storeState.setLoading);
  const updateLoading = useSharedStore((storeState) => storeState.updateLoading);

  const alert = useSharedStore((storeState) => storeState.alert);
  const showAlert = useSharedStore((storeState) => storeState.showAlert);
  const hideAlert = useSharedStore((storeState) => storeState.hideAlert);

  const confirm = useSharedStore((storeState) => storeState.confirm);
  const showConfirm = useSharedStore((storeState) => storeState.showConfirm);
  const hideConfirm = useSharedStore((storeState) => storeState.hideConfirm);

  const toast = useSharedStore((storeState) => storeState.toast);
  const showToast = useSharedStore((storeState) => storeState.showToast);
  const hideToast = useSharedStore((storeState) => storeState.hideToast);

  return {
    isLoading,
    setLoading,
    updateLoading,
    alert,
    showAlert,
    hideAlert,
    confirm,
    showConfirm,
    hideConfirm,
    toast,
    showToast,
    hideToast,
  };
};

/**
 * 설명: React 훅 컨텍스트 밖에서 안전하게 config 스냅샷 조회. 입력/출력 계약 명시
 * 갱신일: 2026-05-23
 */
export const getConfigSnapshot = () => {
  const storeState = useSharedStore.getState?.();
  if (storeState?.config && typeof storeState.config === 'object') return storeState.config;
  return {};
};

/**
 * 설명: React 훅 컨텍스트 밖에서 전역 UI 액션 스냅샷 조회. 입력/출력 계약 명시
 * 갱신일: 2026-05-23
 */
export const getUiActionsSnap = () => {
  const storeState = useSharedStore.getState?.() || {};
  return {
    updateLoading:
      typeof storeState.updateLoading === 'function' ? storeState.updateLoading : () => {},
    showAlert:
      typeof storeState.showAlert === 'function' ? storeState.showAlert : () => {},
  };
};
