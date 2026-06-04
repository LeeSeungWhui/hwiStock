'use client'

/**
 * 파일명: SharedHydrator.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 공유 스토어 하이드레이터
 */

import { useEffect } from 'react'
import { useSharedStore } from './SharedStore'

/**
 * @description SSR에서 주입된 user/shared/config 값을 공용 store에 1회 하이드레이션
 * @param {Object} props
 * @param {any} [props.userJson]
 * @param {object} [props.sharedPatch]
 * @param {object} [props.config]
 * @returns {null}
 */
const SharedHydrator = ({ userJson, sharedPatch, config }) => {
  const { setUserJson, setUser, setShared, setConfig } = useSharedStore()

  /**
   * @description SSR bootstrap userJson/sharedPatch/config를 SharedStore에 반영
   * 처리 규칙: props 변경 시 setUserJson/setUser/setShared/setConfig를 순서대로 호출한다.
   */
  useEffect(() => {
    if (typeof userJson !== 'undefined') {
      setUserJson(userJson || null)

      const hasUserIdentity = userJson && (userJson.userId || userJson.name)
      if (hasUserIdentity) {
        setUser({ userId: userJson.userId, name: userJson.name })
      } else {
        setUser(null)
      }
    }
    if (sharedPatch && typeof sharedPatch === 'object') {
      setShared(sharedPatch)
    }
    if (config && typeof config === 'object') {
      setConfig(config)
    }
  }, [userJson, sharedPatch, config, setUserJson, setUser, setShared, setConfig])
  return null
}

export default SharedHydrator
