import { uploadScriptFile } from '../api'
import { APP_PLATFORM, UPLOAD_MODE } from '../config/env'

const DEFAULT_EXTENSIONS = ['pdf', 'docx', 'txt', 'png', 'jpg', 'jpeg']

export async function chooseAndUploadFile(options = {}) {
  const uploadedFiles = await chooseAndUploadFiles({ ...options, multiple: false })
  return uploadedFiles[0]
}

export async function chooseAndUploadFiles(options = {}) {
  const projectId = options.projectId || ''
  const extensions = options.extensions || DEFAULT_EXTENSIONS
  const selectedFiles = await chooseCompatibleFiles(extensions, options.multiple !== false)
  const uploadedFiles = []
  for (const selected of selectedFiles) {
    uploadedFiles.push(await uploadScriptFile(selected.path, projectId))
  }
  return uploadedFiles
}

async function chooseCompatibleFiles(extensions, multiple = true) {
  if (APP_PLATFORM === 'mp-weixin') {
    return chooseMiniProgramFiles(extensions, multiple)
  }
  return chooseH5Files(extensions, multiple)
}

function chooseH5Files(extensions, multiple) {
  return new Promise((resolve, reject) => {
    if (typeof uni.chooseFile !== 'function') {
      reject(new Error('当前 H5 环境不支持文件选择'))
      return
    }
    uni.chooseFile({
      count: multiple ? 20 : 1,
      extension: extensions,
      success: (result) => {
        const files = (result.tempFiles || []).filter((file) => file?.path)
        if (!files.length) {
          reject(new Error('没有选择文件'))
          return
        }
        resolve(files)
      },
      fail: reject,
    })
  })
}

function chooseMiniProgramFiles(extensions, multiple) {
  return new Promise((resolve, reject) => {
    if (typeof uni.chooseMessageFile === 'function') {
      uni.chooseMessageFile({
        count: multiple ? 20 : 1,
        type: 'all',
        extension: extensions,
        success: (result) => {
          const files = (result.tempFiles || [])
            .map((file) => ({ ...file, path: file?.path || file?.tempFilePath }))
            .filter((file) => file.path)
          if (!files.length) {
            reject(new Error('没有选择文件'))
            return
          }
          resolve(files)
        },
        fail: (error) => {
          if (isCancel(error)) {
            reject(error)
            return
          }
          chooseMiniProgramImages(resolve, reject, multiple)
        },
      })
      return
    }
    chooseMiniProgramImages(resolve, reject, multiple)
  })
}

function chooseMiniProgramImages(resolve, reject, multiple) {
  if (typeof uni.chooseImage !== 'function') {
    reject(new Error('当前小程序环境不支持文件选择'))
    return
  }
  uni.chooseImage({
    count: multiple ? 9 : 1,
    sizeType: ['original', 'compressed'],
    sourceType: ['album', 'camera'],
    success: (result) => {
      const files = (result.tempFilePaths || []).map((path, index) => ({
        path,
        name: `image_upload_${index + 1}`,
      }))
      if (!files.length) {
        reject(new Error('没有选择图片'))
        return
      }
      resolve(files)
    },
    fail: reject,
  })
}

function isCancel(error) {
  return String(error?.errMsg || '').toLowerCase().includes('cancel')
}

export const uploadRuntimeInfo = {
  platform: APP_PLATFORM,
  uploadMode: UPLOAD_MODE,
  supportedExtensions: DEFAULT_EXTENSIONS,
}
