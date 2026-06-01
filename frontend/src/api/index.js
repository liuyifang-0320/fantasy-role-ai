import { API_BASE_URL, getStoredUserId, setStoredUserId } from '../config/env'

export { API_BASE_URL, getStoredUserId, setStoredUserId }

function request({ url, method = 'GET', data }) {
  return new Promise((resolve, reject) => {
    uni.request({
      url: `${API_BASE_URL}${url}`,
      method,
      data,
      header: {
        'X-User-Id': getStoredUserId(),
      },
      success: ({ statusCode, data: responseData }) => {
        if (statusCode >= 200 && statusCode < 300) {
          resolve(responseData)
          return
        }
        reject(new Error(resolveErrorMessage(responseData, statusCode)))
      },
      fail: (error) => {
        reject(new Error(error?.errMsg || '网络请求失败，请检查后端地址和网络连接'))
      },
    })
  })
}

export function uploadScriptFile(filePath, projectId = '') {
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: `${API_BASE_URL}/api/files/upload`,
      filePath,
      name: 'file',
      formData: projectId ? { project_id: projectId } : {},
      header: {
        'X-User-Id': getStoredUserId(),
      },
      success: ({ statusCode, data }) => {
        if (statusCode >= 200 && statusCode < 300) {
          resolve(JSON.parse(data))
          return
        }
        reject(new Error(resolveUploadError(data, statusCode)))
      },
      fail: (error) => {
        reject(new Error(error?.errMsg || '上传失败，请检查文件和网络连接'))
      },
    })
  })
}

function resolveErrorMessage(responseData, statusCode) {
  if (responseData?.detail) {
    if (typeof responseData.detail === 'string') {
      return responseData.detail
    }
    return JSON.stringify(responseData.detail)
  }
  if (responseData?.message) {
    return responseData.message
  }
  return `请求失败（${statusCode}）`
}

function resolveUploadError(data, statusCode) {
  try {
    const parsed = JSON.parse(data || '{}')
    return resolveErrorMessage(parsed, statusCode)
  } catch (error) {
    return `上传失败（${statusCode}）`
  }
}

export const api = {
  getCurrentUser: () => request({ url: '/api/auth/me' }),
  devLogin: (data) =>
    request({
      url: '/api/auth/dev-login',
      method: 'POST',
      data,
    }),
  switchDevUser: (data) =>
    request({
      url: '/api/auth/switch-dev-user',
      method: 'POST',
      data,
    }),
  wechatLogin: (data) =>
    request({
      url: '/api/auth/wechat-login',
      method: 'POST',
      data,
    }),
  parseFile: (fileId) =>
    request({
      url: `/api/files/${fileId}/parse`,
      method: 'POST',
    }),
  getParsedFile: (fileId) => request({ url: `/api/files/${fileId}/parsed` }),
  getParsedDocument: (parsedId) => request({ url: `/api/parsed-documents/${parsedId}` }),
  extractProfile: (data) =>
    request({
      url: '/api/profiles/extract',
      method: 'POST',
      data,
    }),
  getProfiles: () => request({ url: '/api/profiles' }),
  getProfile: (profileId) => request({ url: `/api/profiles/${profileId}` }),
  getCharacters: () => request({ url: '/api/characters' }),
  getCharacter: (characterId) => request({ url: `/api/characters/${characterId}` }),
  getCharacterSettings: (characterId) =>
    request({ url: `/api/characters/${characterId}/settings` }),
  updateCharacterSettings: (characterId, data) =>
    request({
      url: `/api/characters/${characterId}/settings`,
      method: 'PATCH',
      data,
    }),
  resetCharacterSettings: (characterId) =>
    request({
      url: `/api/characters/${characterId}/settings/reset`,
      method: 'POST',
    }),
  getCharacterSettingsPromptPreview: (characterId) =>
    request({ url: `/api/characters/${characterId}/settings/prompt-preview` }),
  listPetAssets: (characterId) =>
    request({ url: `/api/characters/${characterId}/pet-assets` }),
  generatePetAsset: (characterId, data) =>
    request({
      url: `/api/characters/${characterId}/pet-assets/generate`,
      method: 'POST',
      data,
    }),
  setActivePetAsset: (characterId, assetId) =>
    request({
      url: `/api/characters/${characterId}/pet-assets/${assetId}/active`,
      method: 'PATCH',
    }),
  getPetAsset: (assetId) => request({ url: `/api/pet-assets/${assetId}` }),
  getImageGenerationStatus: () => request({ url: '/api/image-generation/status' }),
  createProject: (data) =>
    request({
      url: '/api/projects',
      method: 'POST',
      data,
    }),
  listProjects: () => request({ url: '/api/projects' }),
  getProject: (projectId) => request({ url: `/api/projects/${projectId}` }),
  updateProject: (projectId, data) =>
    request({
      url: `/api/projects/${projectId}`,
      method: 'PATCH',
      data,
    }),
  archiveProject: (projectId) =>
    request({
      url: `/api/projects/${projectId}`,
      method: 'DELETE',
    }),
  extractProjectCandidates: (projectId) =>
    request({
      url: `/api/projects/${projectId}/candidates/extract`,
      method: 'POST',
    }),
  listProjectCandidates: (projectId, status = '') =>
    request({
      url: `/api/projects/${projectId}/candidates${status ? `?status=${encodeURIComponent(status)}` : ''}`,
    }),
  getCharacterCandidate: (candidateId) =>
    request({ url: `/api/character-candidates/${candidateId}` }),
  updateCharacterCandidate: (candidateId, data) =>
    request({
      url: `/api/character-candidates/${candidateId}`,
      method: 'PATCH',
      data,
    }),
  ignoreCharacterCandidate: (candidateId) =>
    request({
      url: `/api/character-candidates/${candidateId}`,
      method: 'DELETE',
    }),
  batchGenerateProjectCharacters: (projectId, data) =>
    request({
      url: `/api/projects/${projectId}/characters/batch-generate`,
      method: 'POST',
      data,
    }),
  extractProjectRelationships: (projectId) =>
    request({
      url: `/api/projects/${projectId}/relationships/extract`,
      method: 'POST',
    }),
  listProjectRelationships: (projectId, status = '') =>
    request({
      url: `/api/projects/${projectId}/relationships${status ? `?status=${encodeURIComponent(status)}` : ''}`,
    }),
  getCharacterRelationship: (relationshipId) =>
    request({ url: `/api/character-relationships/${relationshipId}` }),
  updateCharacterRelationship: (relationshipId, data) =>
    request({
      url: `/api/character-relationships/${relationshipId}`,
      method: 'PATCH',
      data,
    }),
  ignoreCharacterRelationship: (relationshipId) =>
    request({
      url: `/api/character-relationships/${relationshipId}`,
      method: 'DELETE',
    }),
  getProjectRelationshipGraph: (projectId) =>
    request({ url: `/api/projects/${projectId}/relationships/graph` }),
  runLlmScriptAnalyze: (projectId, data = {}) =>
    request({
      url: `/api/projects/${projectId}/script-intelligence/llm-analyze`,
      method: 'POST',
      data,
    }),
  getScriptIntelligenceStatus: (projectId) =>
    request({ url: `/api/projects/${projectId}/script-intelligence/status` }),
  getScriptIntelligenceResult: (projectId) =>
    request({ url: `/api/projects/${projectId}/script-intelligence/result` }),
  confirmScriptIntelligence: (projectId, data = {}) =>
    request({
      url: `/api/projects/${projectId}/script-intelligence/confirm`,
      method: 'POST',
      data,
    }),
  generateCharacter: (data) =>
    request({
      url: '/api/characters/generate',
      method: 'POST',
      data,
    }),
  getChatMessages: (sessionId) =>
    request({
      url: `/api/chat/sessions/${sessionId}/messages`,
    }),
  getCharacterSessions: (characterId) =>
    request({
      url: `/api/chat/characters/${characterId}/sessions`,
    }),
  getLlmStatus: () => request({ url: '/api/llm/status' }),
  getOcrStatus: () => request({ url: '/api/ocr/status' }),
  getStorageStatus: () => request({ url: '/api/storage/status' }),
  getSystemHealth: () => request({ url: '/api/system/health' }),
  getSafetyStatus: () => request({ url: '/api/safety/status' }),
  exportUserData: () => request({ url: '/api/user-data/export' }),
  deleteUserData: () =>
    request({
      url: '/api/user-data/delete',
      method: 'DELETE',
    }),
  buildKnowledge: (data) =>
    request({
      url: '/api/knowledge/build',
      method: 'POST',
      data,
    }),
  getKnowledgeChunks: (params = {}) => {
    const query = Object.entries(params)
      .filter(([, value]) => value)
      .map(([key, value]) => `${key}=${encodeURIComponent(value)}`)
      .join('&')
    return request({ url: `/api/knowledge/chunks${query ? `?${query}` : ''}` })
  },
  getKnowledgeChunk: (chunkId) => request({ url: `/api/knowledge/chunks/${chunkId}` }),
  searchKnowledge: (data) =>
    request({
      url: '/api/knowledge/search',
      method: 'POST',
      data,
    }),
  chat: (data) =>
    request({
      url: '/api/chat',
      method: 'POST',
      data,
    }),
  getMemory: (characterId) => request({ url: `/api/memory/${characterId}` }),
  getMemoryDebug: (characterId) => request({ url: `/api/memory/${characterId}/debug` }),
  updateMemory: (data) =>
    request({
      url: '/api/memory/update',
      method: 'POST',
      data,
    }),
  patchMemory: (memoryId, data) =>
    request({
      url: `/api/memory/${memoryId}`,
      method: 'PATCH',
      data,
    }),
  deleteMemory: (memoryId) =>
    request({
      url: `/api/memory/${memoryId}`,
      method: 'DELETE',
    }),
  getPet: (characterId) => request({ url: `/api/pets/${characterId}` }),
  updatePetAction: (data) =>
    request({
      url: '/api/pets/action',
      method: 'POST',
      data,
    }),
}

export function resolveAssetUrl(path) {
  if (!path) {
    return ''
  }
  if (/^https?:\/\//.test(path)) {
    return path
  }
  return `${API_BASE_URL}${path}`
}
