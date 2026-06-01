<template>
  <GradientPage>
    <view class="page-head">
      <text class="title">设置</text>
      <text class="subtitle">模型、OCR、图片生成、存储与部署状态均由后端环境变量控制。</text>
    </view>

    <view class="status-panel">
      <text class="section-title">当前用户</text>
      <view v-if="currentUser" class="status-grid">
        <view class="mode-card">
          <text class="mode-title">{{ currentUser.nickname }}</text>
          <text class="mode-copy">当前为开发 mock 用户，非正式登录。后续可接微信登录，请不要输入真实敏感信息。</text>
        </view>
        <StatusRow label="user_id" :value="currentUser.user_id" />
        <StatusRow label="auth_provider" :value="currentUser.auth_provider" />
      </view>
    </view>

    <view class="status-panel">
      <text class="section-title">系统健康</text>
      <view v-if="systemHealth" class="status-grid">
        <view class="mode-card">
          <text class="mode-title">{{ systemHealth.status }}</text>
          <text class="mode-copy">健康检查只检查数据库、存储和 Provider 配置状态，不会调用真实模型。</text>
        </view>
        <StatusRow label="database" :value="systemHealth.database" />
        <StatusRow label="storage" :value="systemHealth.storage" />
        <StatusRow label="llm_provider" :value="systemHealth.llm_provider" />
        <StatusRow label="ocr_provider" :value="systemHealth.ocr_provider" />
        <StatusRow label="image_provider" :value="systemHealth.image_provider" />
      </view>
      <text v-else class="status-loading">正在读取系统健康状态...</text>
    </view>

    <view class="status-panel">
      <text class="section-title">内容安全与隐私</text>
      <view v-if="safetyStatus" class="status-grid">
        <view class="mode-card">
          <text class="mode-title">{{ safetyStatus.safety_mode }}</text>
          <text class="mode-copy">当前是规则版内容安全骨架，不是真实内容审核服务；生产环境建议关闭调试输出。</text>
        </view>
        <StatusRow label="SAFETY_MODE" :value="safetyStatus.safety_mode" />
        <StatusRow label="SAFETY_STRICT_LEVEL" :value="safetyStatus.strict_level" />
        <StatusRow label="ENABLE_DEBUG_OUTPUT" :value="yesNo(safetyStatus.debug_output_enabled)" />
        <StatusRow label="用户数据导出" :value="yesNo(safetyStatus.user_data_export_enabled)" />
        <StatusRow label="用户数据删除" :value="yesNo(safetyStatus.user_data_delete_enabled)" />
        <StatusRow label="隐私联系邮箱" :value="safetyStatus.privacy_contact_email || '未配置'" />
      </view>
      <text v-else class="status-loading">正在读取安全状态...</text>
    </view>

    <view class="status-panel">
      <text class="section-title">存储状态</text>
      <view v-if="storageStatus" class="status-grid">
        <view class="mode-card">
          <text class="mode-title">{{ storageStatus.active_provider }}</text>
          <text class="mode-copy">{{ storageStatusText }}</text>
        </view>
        <StatusRow label="配置 provider" :value="storageStatus.storage_provider" />
        <StatusRow label="实际 active provider" :value="storageStatus.active_provider" />
        <StatusRow label="Bucket 已配置" :value="yesNo(storageStatus.bucket_configured)" />
        <StatusRow label="Endpoint 已配置" :value="yesNo(storageStatus.endpoint_configured)" />
        <StatusRow label="公开域名已配置" :value="yesNo(storageStatus.public_base_url_configured)" />
        <StatusRow label="上传大小限制" :value="`${storageStatus.max_upload_size_mb} MB`" />
        <StatusRow label="允许上传类型" :value="storageStatus.allowed_upload_types.join(', ')" />
      </view>
      <text v-else class="status-loading">正在读取存储状态...</text>
      <text class="note">生产环境建议使用对象存储和 HTTPS 域名，本地开发默认使用 local uploads。</text>
      <text class="note">CORS 由后端 CORS_ALLOW_ORIGINS 配置，上线时应填写真实 H5 或小程序后台域名。</text>
    </view>

    <view class="status-panel">
      <text class="section-title">LLM 状态</text>
      <view v-if="llmStatus" class="status-grid">
        <view class="mode-card">
          <text class="mode-title">当前模型状态</text>
          <text class="mode-copy">{{ modelStatusText }}</text>
        </view>
        <StatusRow label="配置 provider" :value="llmStatus.configured_provider" />
        <StatusRow label="实际 active provider" :value="llmStatus.active_provider" />
        <StatusRow label="API Key 已配置" :value="yesNo(llmStatus.api_key_configured)" />
        <StatusRow label="Base URL 已配置" :value="yesNo(llmStatus.base_url_configured)" />
        <StatusRow label="模型" :value="llmStatus.model" />
        <StatusRow label="API 风格" :value="llmStatus.api_style" />
        <StatusRow label="prompt_debug" :value="yesNo(llmStatus.prompt_debug_enabled)" />
        <StatusRow label="AI 剧本理解" :value="llmStatus.api_key_configured ? '可尝试真实 LLM 复核' : '未配置 Key，将使用规则 fallback'" />
      </view>
      <text v-else class="status-loading">正在读取模型状态...</text>
      <text class="note">API Key 不会在前端显示，只显示是否已配置。</text>
    </view>

    <view class="status-panel">
      <text class="section-title">OCR 状态</text>
      <view v-if="ocrStatus" class="status-grid">
        <view class="mode-card">
          <text class="mode-title">当前图片 OCR 状态</text>
          <text class="mode-copy">{{ ocrStatusText }}</text>
        </view>
        <StatusRow label="OCR provider" :value="ocrStatus.ocr_provider" />
        <StatusRow label="实际 active provider" :value="ocrStatus.active_provider" />
        <StatusRow label="PaddleOCR 可用" :value="yesNo(ocrStatus.paddleocr_available)" />
        <StatusRow label="OCR 语言" :value="ocrStatus.ocr_lang" />
        <StatusRow label="PDF 图片 OCR fallback" :value="yesNo(ocrStatus.pdf_image_fallback_enabled)" />
      </view>
      <text v-else class="status-loading">正在读取 OCR 状态...</text>
      <text class="note">OCR Provider 由后端环境变量配置，前端不显示任何敏感信息。</text>
    </view>

    <view class="status-panel">
      <text class="section-title">图片生成状态</text>
      <view v-if="imageStatus" class="status-grid">
        <view class="mode-card">
          <text class="mode-title">当前桌宠形象生成状态</text>
          <text class="mode-copy">{{ imageStatusText }}</text>
        </view>
        <StatusRow label="图片生成 provider" :value="imageStatus.image_provider" />
        <StatusRow label="实际 active provider" :value="imageStatus.active_provider" />
        <StatusRow label="API Key 已配置" :value="yesNo(imageStatus.api_key_configured)" />
        <StatusRow label="Base URL 已配置" :value="yesNo(imageStatus.base_url_configured)" />
        <StatusRow label="模型" :value="imageStatus.model" />
        <StatusRow label="超时时间" :value="`${imageStatus.timeout_seconds}s`" />
      </view>
      <text v-else class="status-loading">正在读取图片生成状态...</text>
      <text class="note">当前桌宠形象默认使用 mock 生成；配置图片生成服务后可接入真实 Q版形象生成。</text>
    </view>
  </GradientPage>
</template>

<script setup>
import { computed, defineComponent, h, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { api } from '../../api'
import GradientPage from '../../components/GradientPage.vue'

const StatusRow = defineComponent({
  props: {
    label: {
      type: String,
      required: true,
    },
    value: {
      type: [String, Number, Boolean],
      default: '',
    },
  },
  setup(props) {
    return () =>
      h('view', { class: 'status-row' }, [
        h('text', { class: 'status-label' }, props.label),
        h('text', { class: 'status-value' }, String(props.value ?? '-')),
      ])
  },
})

const currentUser = ref(null)
const llmStatus = ref(null)
const ocrStatus = ref(null)
const imageStatus = ref(null)
const storageStatus = ref(null)
const systemHealth = ref(null)
const safetyStatus = ref(null)

const storageStatusText = computed(() => {
  if (!storageStatus.value) {
    return ''
  }
  if (storageStatus.value.active_provider === 'local') {
    if (storageStatus.value.storage_provider !== 'local') {
      return '云存储配置不完整或当前骨架未启用真实上传，已回退到本地 uploads。'
    }
    return 'LocalStorageProvider：本地开发模式，文件保存到 backend/app/uploads。'
  }
  return '对象存储模式：生产环境可通过 storage_key 与 public_url 管理文件。'
})

const modelStatusText = computed(() => {
  if (!llmStatus.value) {
    return ''
  }
  if (llmStatus.value.active_provider === 'mock') {
    if (llmStatus.value.configured_provider !== 'mock') {
      return 'Fallback：真实模型不可用，当前已回退 mock。'
    }
    return 'Mock 模式：当前为测试回复，不是真实 AI 模型。'
  }
  if (llmStatus.value.configured_provider === 'openai_compatible') {
    return llmStatus.value.api_key_configured
      ? 'OpenAI-compatible 模式：已配置 API Key 后会尝试调用真实模型。'
      : 'OpenAI-compatible 模式：未配置 API Key，不会调用真实模型。'
  }
  return 'Custom HTTP 模式：需要完整配置 API Key、Base URL 和模型名后才会尝试调用。'
})

const ocrStatusText = computed(() => {
  if (!ocrStatus.value) {
    return ''
  }
  if (ocrStatus.value.active_provider === 'mock') {
    if (ocrStatus.value.ocr_provider === 'paddleocr') {
      return 'PaddleOCR 当前不可用，图片 OCR 已自动回退 mock。'
    }
    return 'Mock OCR 模式：当前为测试解析，不是真实图片文字识别。'
  }
  return 'PaddleOCR 模式：后端已启用真实 OCR Provider。'
})

const imageStatusText = computed(() => {
  if (!imageStatus.value) {
    return ''
  }
  if (imageStatus.value.active_provider === 'mock') {
    return 'Mock 图片生成：当前不会调用真实绘图模型，只返回测试桌宠图片。'
  }
  return 'Custom 图片生成：后端配置完整后可接入真实图片生成服务。'
})

onLoad(async () => {
  const [user, llm, ocr, image, storage, health, safety] = await Promise.all([
    api.getCurrentUser(),
    api.getLlmStatus(),
    api.getOcrStatus(),
    api.getImageGenerationStatus(),
    api.getStorageStatus(),
    api.getSystemHealth(),
    api.getSafetyStatus(),
  ])
  currentUser.value = user
  llmStatus.value = llm
  ocrStatus.value = ocr
  imageStatus.value = image
  storageStatus.value = storage
  systemHealth.value = health
  safetyStatus.value = safety
})

function yesNo(value) {
  return value ? '是' : '否'
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
  color: rgba(248, 247, 255, 0.72);
  font-size: 24rpx;
  line-height: 1.6;
}

.status-panel {
  margin-top: 28rpx;
  padding: 22rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
}

.section-title,
.status-loading,
.note {
  display: block;
}

.section-title {
  font-size: 28rpx;
  font-weight: 700;
}

.status-grid {
  display: grid;
  gap: 14rpx;
  margin-top: 18rpx;
}

.mode-card {
  padding: 18rpx;
  border-radius: 8px;
  background: rgba(126, 231, 246, 0.12);
}

.mode-card text {
  display: block;
}

.mode-title {
  color: #7ee7f6;
  font-size: 24rpx;
  font-weight: 700;
}

.mode-copy {
  margin-top: 8rpx;
  color: rgba(248, 247, 255, 0.82);
  font-size: 24rpx;
  line-height: 1.6;
}

.status-row {
  display: flex;
  justify-content: space-between;
  gap: 18rpx;
  font-size: 24rpx;
}

.status-label {
  color: rgba(248, 247, 255, 0.66);
}

.status-value {
  max-width: 430rpx;
  text-align: right;
  word-break: break-word;
}

.status-loading,
.note {
  color: rgba(248, 247, 255, 0.76);
  font-size: 24rpx;
  line-height: 1.7;
}

.status-loading {
  margin-top: 16rpx;
}

.note {
  margin-top: 14rpx;
}
</style>
