const H5_API_BASE_URL = 'http://127.0.0.1:8000'
const MP_WEIXIN_API_BASE_URL = 'http://192.168.x.x:8000'
const API_BASE_URL_STORAGE_KEY = 'fantasy_role_ai_api_base_url'
const USER_STORAGE_KEY = 'fantasy_role_ai_user_id'

export const APP_PLATFORM = resolvePlatform()
export const API_BASE_URL = resolveApiBaseUrl()
export const UPLOAD_MODE = APP_PLATFORM === 'mp-weixin' ? 'miniapp' : 'h5'

export function getStoredUserId() {
  return uni.getStorageSync(USER_STORAGE_KEY) || 'dev_user'
}

export function setStoredUserId(userId) {
  uni.setStorageSync(USER_STORAGE_KEY, userId || 'dev_user')
}

export function getApiBaseUrl() {
  return API_BASE_URL
}

function resolvePlatform() {
  let platform = 'h5'
  // #ifdef MP-WEIXIN
  platform = 'mp-weixin'
  // #endif
  return platform
}

function resolveApiBaseUrl() {
  const stored = uni.getStorageSync(API_BASE_URL_STORAGE_KEY)
  if (stored) {
    return stored
  }

  let baseUrl = H5_API_BASE_URL
  // #ifdef MP-WEIXIN
  baseUrl = MP_WEIXIN_API_BASE_URL
  // #endif
  return baseUrl
}
