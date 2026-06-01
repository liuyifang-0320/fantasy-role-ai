<template>
  <GradientPage>
    <view class="page-head">
      <text class="title">创建数字人</text>
      <text class="subtitle">先把角色从剧本里请出来，再让故事继续往前走。</text>
    </view>

    <view class="steps">
      <view
        v-for="(step, index) in steps"
        :key="step"
        class="step"
        :class="{ active: index <= currentStep }"
      >
        <text class="step-index">{{ index + 1 }}</text>
        <text class="step-label">{{ step }}</text>
      </view>
    </view>

    <view v-if="project" class="project-banner">
      <text class="project-label">当前剧本项目</text>
      <text class="project-title">{{ project.title }}</text>
      <text class="project-copy">上传资料和生成角色都会绑定到这个项目空间。</text>
    </view>

    <view class="panel">
      <text class="panel-title">上传资料</text>
      <button class="ghost-button" :disabled="uploading" @click="chooseFile">
        {{ uploading ? '上传中...' : '选择文件 / 资料包' }}
      </button>
      <view v-for="file in uploadedFiles" :key="file.file_id" class="file-meta">
        <view class="meta-row">
          <text class="meta-label">文件名</text>
          <text>{{ file.filename }}</text>
        </view>
        <view class="meta-row">
          <text class="meta-label">文件类型</text>
          <text>{{ file.file_type }}</text>
        </view>
        <view class="meta-row">
          <text class="meta-label">上传状态</text>
          <text>{{ file.upload_status }}</text>
        </view>
      </view>
      <text class="hint">支持 PDF / DOCX / TXT / PNG / JPG / JPEG</text>
    </view>

    <view v-if="uploadedFiles.length" class="panel parse-panel">
      <text class="panel-title">解析结果</text>
      <view v-if="parsing" class="parse-loading">
        <text>正在解析文件内容...</text>
      </view>
      <view v-else-if="parsedDocument">
        <view class="meta-row">
          <text class="meta-label">解析状态</text>
          <text>{{ parsedDocument.parse_status }}</text>
        </view>
        <view class="meta-row">
          <text class="meta-label">字数</text>
          <text>{{ parsedDocument.word_count }}</text>
        </view>
        <view v-if="isImageParsedDocument" class="ocr-box">
          <view class="meta-row">
            <text class="meta-label">OCR 状态</text>
            <text>{{ ocrStatusLabel }}</text>
          </view>
          <view class="meta-row">
            <text class="meta-label">OCR provider</text>
            <text>{{ parsedDocument.ocr_provider || '-' }}</text>
          </view>
          <view class="meta-row">
            <text class="meta-label">OCR 置信度</text>
            <text>{{ formatConfidence(parsedDocument.ocr_confidence) }}</text>
          </view>
          <view v-if="parsedDocument.ocr_error" class="ocr-error">
            <text>{{ parsedDocument.ocr_error }}</text>
          </view>
          <text v-if="parsedDocument.parse_status === 'mock_ocr'" class="ocr-note">
            当前图片 OCR 为测试模式，未真正识别图片文字。
          </text>
        </view>
        <text class="preview">{{ parsedDocument.text_preview || '暂无可展示摘要' }}</text>
        <view class="next-step">
          <text class="next-step-value">下一步：抽取角色设定</text>
        </view>
      </view>
      <view v-else class="parse-loading">
        <text>还没有解析结果。</text>
      </view>
    </view>

    <view class="panel form-panel">
      <label class="field">
        <text>目标数字人角色名</text>
        <input v-model="form.target_character_name" placeholder="例如：阿奇" />
      </label>
      <label class="field">
        <text>用户扮演身份</text>
        <input v-model="form.user_persona_name" placeholder="例如：戴丽拉" />
      </label>
      <label class="field">
        <text>关系提示</text>
        <input v-model="form.relationship_hint" placeholder="例如：情侣" />
      </label>
    </view>

    <button class="primary-button" :disabled="loading" @click="generateCharacter">
      {{ loading ? '生成中...' : '生成数字人' }}
    </button>
  </GradientPage>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { api } from '../../api'
import GradientPage from '../../components/GradientPage.vue'
import { chooseAndUploadFiles } from '../../utils/upload'

const steps = ['上传资料', '填写目标角色', '填写用户扮演身份', '生成数字人']
const currentStep = ref(0)
const uploading = ref(false)
const parsing = ref(false)
const loading = ref(false)
const projectId = ref('')
const project = ref(null)
const uploadedFile = ref(null)
const uploadedFiles = ref([])
const parsedDocument = ref(null)
const form = ref({
  target_character_name: '阿奇',
  user_persona_name: '戴丽拉',
  relationship_hint: '情侣',
})
const imageTypes = ['png', 'jpg', 'jpeg']
const isImageParsedDocument = computed(() =>
  imageTypes.includes(parsedDocument.value?.file_type)
)
const ocrStatusLabel = computed(() => {
  if (!parsedDocument.value) {
    return ''
  }
  if (parsedDocument.value.parse_status === 'mock_ocr') {
    return 'mock OCR'
  }
  if (parsedDocument.value.parse_status === 'success' && parsedDocument.value.ocr_provider) {
    return '真实 OCR'
  }
  if (parsedDocument.value.parse_status === 'failed' && parsedDocument.value.ocr_provider) {
    return 'OCR 失败'
  }
  return parsedDocument.value.parse_status || '-'
})

onLoad(async ({ project_id }) => {
  projectId.value = project_id || ''
  if (projectId.value) {
    project.value = await api.getProject(projectId.value)
  }
})

async function chooseFile() {
  try {
    uploading.value = true
    parsedDocument.value = null
    uploadedFiles.value = await chooseAndUploadFiles({ projectId: projectId.value })
    uploadedFile.value = uploadedFiles.value[0] || null
    currentStep.value = 1
    await parseUploadedFile()
  } catch (error) {
    if (error?.errMsg?.includes('cancel')) {
      return
    }
    uni.showToast({ title: error.message || '上传失败', icon: 'none' })
  } finally {
    uploading.value = false
  }
}

async function parseUploadedFile() {
  if (!uploadedFiles.value.length) {
    return
  }
  parsing.value = true
  try {
    parsedDocument.value = await api.parseFile(uploadedFile.value.file_id)
  } catch (error) {
    uni.showToast({ title: error.message || '解析失败', icon: 'none' })
  } finally {
    parsing.value = false
  }
}

async function generateCharacter() {
  if (!uploadedFile.value) {
    uni.showToast({ title: '请先上传资料', icon: 'none' })
    return
  }
  if (
    !form.value.target_character_name ||
    !form.value.user_persona_name ||
    !form.value.relationship_hint
  ) {
    uni.showToast({ title: '请填写完整信息', icon: 'none' })
    return
  }

  loading.value = true
  currentStep.value = 3
  try {
    const character = await api.generateCharacter({
      ...(projectId.value ? { project_id: projectId.value } : {}),
      uploaded_file_ids: uploadedFiles.value.map((file) => file.file_id),
      ...form.value,
    })
    uni.setStorageSync('latestGeneratedCharacter', character)
    uni.setStorageSync('latestParsedDocuments', character.parsed_documents || [])
    uni.setStorageSync('latestCharacterProfile', character.profile || null)
    const parsedIds = (character.parsed_document_ids || []).join(',')
    uni.navigateTo({
      url: `/pages/generate-result/index?character_id=${character.character_id}&parsed_ids=${parsedIds}`,
    })
  } catch (error) {
    uni.showToast({ title: error.message || '生成失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

function formatConfidence(value) {
  const numberValue = Number(value || 0)
  return numberValue > 0 ? numberValue.toFixed(2) : '0.00'
}
</script>

<style scoped lang="scss">
.page-head text {
  display: block;
}

.title {
  font-size: 42rpx;
  font-weight: 700;
}

.subtitle {
  margin-top: 10rpx;
  color: rgba(248, 247, 255, 0.74);
  font-size: 26rpx;
}

.steps {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12rpx;
  margin-top: 30rpx;
}

.step {
  min-height: 110rpx;
  padding: 16rpx 10rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.08);
  text-align: center;
}

.step.active {
  border-color: rgba(126, 231, 246, 0.4);
  background: rgba(126, 231, 246, 0.14);
}

.step text {
  display: block;
}

.step-index {
  font-size: 28rpx;
  font-weight: 700;
}

.step-label {
  margin-top: 6rpx;
  color: rgba(248, 247, 255, 0.76);
  font-size: 22rpx;
}

.panel {
  margin-top: 24rpx;
  padding: 24rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
}

.project-banner {
  margin-top: 24rpx;
  padding: 22rpx;
  border: 1rpx solid rgba(126, 231, 246, 0.24);
  border-radius: 8px;
  background: rgba(126, 231, 246, 0.1);
}

.project-banner text {
  display: block;
}

.project-label {
  color: #7ee7f6;
  font-size: 22rpx;
}

.project-title {
  margin-top: 6rpx;
  font-size: 30rpx;
  font-weight: 700;
}

.project-copy {
  margin-top: 8rpx;
  color: rgba(248, 247, 255, 0.72);
  font-size: 24rpx;
  line-height: 1.6;
}

.panel-title {
  display: block;
  margin-bottom: 18rpx;
  font-size: 28rpx;
  font-weight: 700;
}

.ghost-button,
.primary-button {
  border-radius: 8px;
}

.ghost-button {
  color: #f8f7ff;
  background: rgba(255, 255, 255, 0.14);
}

.file-meta,
.parse-panel {
  display: grid;
  gap: 12rpx;
}

.file-meta {
  margin-top: 18rpx;
}

.meta-row {
  display: flex;
  justify-content: space-between;
  gap: 16rpx;
  font-size: 24rpx;
}

.meta-label {
  color: rgba(248, 247, 255, 0.66);
}

.preview {
  display: block;
  margin-top: 6rpx;
  padding: 18rpx;
  border-radius: 8px;
  background: rgba(19, 12, 47, 0.46);
  color: rgba(248, 247, 255, 0.84);
  font-size: 24rpx;
  line-height: 1.7;
}

.ocr-box {
  display: grid;
  gap: 10rpx;
  margin-top: 8rpx;
  padding: 18rpx;
  border-radius: 8px;
  background: rgba(126, 231, 246, 0.1);
}

.ocr-note,
.ocr-error {
  display: block;
  font-size: 22rpx;
  line-height: 1.6;
}

.ocr-note {
  color: #7ee7f6;
}

.ocr-error {
  color: #ffd166;
}

.next-step {
  display: flex;
  justify-content: space-between;
  gap: 16rpx;
  margin-top: 8rpx;
  padding: 18rpx;
  border-radius: 8px;
  background: rgba(126, 231, 246, 0.14);
}

.next-step-value {
  color: #7ee7f6;
  font-size: 24rpx;
  font-weight: 700;
}

.parse-loading {
  color: rgba(248, 247, 255, 0.72);
  font-size: 24rpx;
}

.hint {
  display: block;
  margin-top: 14rpx;
  color: rgba(248, 247, 255, 0.62);
  font-size: 22rpx;
}

.form-panel {
  display: grid;
  gap: 18rpx;
}

.field text {
  display: block;
  margin-bottom: 10rpx;
  color: rgba(248, 247, 255, 0.76);
  font-size: 24rpx;
}

.field input {
  width: 100%;
  height: 76rpx;
  padding: 0 18rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  background: rgba(19, 12, 47, 0.46);
  color: #f8f7ff;
}

.primary-button {
  margin-top: 28rpx;
  color: #1b1036;
  font-weight: 700;
  background: linear-gradient(135deg, #ffd166, #ff8db4, #7ee7f6);
}
</style>
