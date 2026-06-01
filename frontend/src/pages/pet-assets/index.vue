<template>
  <GradientPage v-if="character">
    <view class="page-head">
      <text class="title">桌宠资产</text>
      <text class="subtitle">当前默认是 mock 生成，不是真实 AI 绘图；配置 IMAGE_PROVIDER 后可接入真实图片生成服务。</text>
    </view>

    <view v-if="activeAsset" class="active-section">
      <text class="section-title">当前使用形象</text>
      <view class="asset-main">
        <image class="asset-image" :src="resolveAssetUrl(activeAsset.image_url)" mode="aspectFit" />
        <view class="asset-copy">
          <text class="asset-title">{{ styleLabel(activeAsset.style) }}</text>
          <text class="asset-meta">provider: {{ activeAsset.generation_provider }}</text>
          <text class="asset-meta">status: {{ activeAsset.generation_status }}</text>
        </view>
      </view>
    </view>

    <view class="generate-section">
      <text class="section-title">mock 重新生成桌宠</text>
      <view class="style-grid">
        <button
          v-for="style in styles"
          :key="style.value"
          class="style-button"
          :class="{ active: form.style === style.value }"
          @click="form.style = style.value"
        >
          {{ style.label }}
        </button>
      </view>
      <textarea
        v-model="form.prompt_override"
        class="prompt-input"
        placeholder="可选：补充形象提示，例如“更像神社少女，蓝紫色调”"
      />
      <button class="primary" :disabled="loading" @click="generateAsset">
        {{ loading ? '生成中...' : '生成 mock 桌宠资产' }}
      </button>
    </view>

    <view class="asset-list-section">
      <text class="section-title">历史桌宠资产</text>
      <view
        v-for="asset in assets"
        :key="asset.asset_id"
        class="asset-card"
      >
        <image class="thumb" :src="resolveAssetUrl(asset.image_url)" mode="aspectFit" />
        <view class="asset-info">
          <text class="asset-title">{{ styleLabel(asset.style) }}</text>
          <text class="asset-meta">asset_id: {{ asset.asset_id }}</text>
          <text class="asset-meta">provider: {{ asset.generation_provider }} · status: {{ asset.generation_status }}</text>
          <text class="asset-prompt">{{ trimPrompt(asset.prompt) }}</text>
        </view>
        <button
          class="ghost small"
          :disabled="asset.is_active"
          @click="setActive(asset.asset_id)"
        >
          {{ asset.is_active ? '当前使用' : '设为 active' }}
        </button>
      </view>
      <view v-if="!assets.length" class="empty">
        <text>暂无桌宠资产。</text>
      </view>
    </view>
  </GradientPage>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { api, resolveAssetUrl } from '../../api'
import GradientPage from '../../components/GradientPage.vue'

const styles = [
  { value: 'q_chibi', label: 'Q版小人' },
  { value: 'anime_chibi', label: '日系Q版' },
  { value: 'soft_dream', label: '柔和梦幻' },
  { value: 'mystery_dark', label: '悬疑暗色' },
  { value: 'cute_pet', label: '可爱桌宠' },
]

const character = ref(null)
const assets = ref([])
const loading = ref(false)
const form = reactive({
  style: 'q_chibi',
  prompt_override: '',
})

const activeAsset = computed(() =>
  assets.value.find((asset) => asset.is_active) || character.value?.active_pet_asset || null
)

onLoad(async ({ character_id }) => {
  character.value = await api.getCharacter(character_id)
  await refreshAssets()
})

async function refreshAssets() {
  assets.value = await api.listPetAssets(character.value.character_id)
}

async function generateAsset() {
  loading.value = true
  try {
    await api.generatePetAsset(character.value.character_id, {
      style: form.style,
      prompt_override: form.prompt_override.trim() || null,
    })
    form.prompt_override = ''
    await refreshAssets()
    character.value = await api.getCharacter(character.value.character_id)
    uni.showToast({ title: '已生成 mock 桌宠资产', icon: 'none' })
  } finally {
    loading.value = false
  }
}

async function setActive(assetId) {
  await api.setActivePetAsset(character.value.character_id, assetId)
  await refreshAssets()
  character.value = await api.getCharacter(character.value.character_id)
}

function styleLabel(value) {
  return styles.find((style) => style.value === value)?.label || value
}

function trimPrompt(prompt) {
  if (!prompt) {
    return '暂无 prompt 摘要'
  }
  return prompt.length > 90 ? `${prompt.slice(0, 90)}...` : prompt
}
</script>

<style scoped lang="scss">
.page-head text,
.asset-copy text,
.asset-info text,
.empty text {
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
  line-height: 1.7;
}

.section-title {
  display: block;
  margin-bottom: 16rpx;
  font-size: 28rpx;
  font-weight: 700;
}

.active-section,
.generate-section,
.asset-list-section {
  margin-top: 26rpx;
}

.asset-main,
.asset-card,
.empty {
  padding: 22rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
}

.asset-main {
  display: flex;
  gap: 22rpx;
  align-items: center;
}

.asset-image {
  width: 220rpx;
  height: 220rpx;
}

.asset-title {
  font-size: 30rpx;
  font-weight: 700;
}

.asset-meta,
.asset-prompt {
  margin-top: 8rpx;
  color: rgba(248, 247, 255, 0.76);
  font-size: 24rpx;
  line-height: 1.6;
}

.style-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14rpx;
}

.style-button,
.primary,
.ghost {
  border-radius: 8px;
}

.style-button {
  min-height: 76rpx;
  color: #f8f7ff;
  background: rgba(255, 255, 255, 0.12);
  font-size: 24rpx;
}

.style-button.active {
  color: #1b1036;
  background: linear-gradient(135deg, #ffd166, #7ee7f6);
}

.prompt-input {
  box-sizing: border-box;
  width: 100%;
  min-height: 150rpx;
  margin-top: 16rpx;
  padding: 18rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  background: rgba(19, 12, 47, 0.58);
  color: #f8f7ff;
  font-size: 24rpx;
  line-height: 1.6;
}

.primary {
  margin-top: 16rpx;
  color: #1b1036;
  font-weight: 700;
  background: linear-gradient(135deg, #ffd166, #ff8db4, #7ee7f6);
}

.asset-card {
  display: grid;
  grid-template-columns: 130rpx minmax(0, 1fr);
  gap: 18rpx;
  margin-bottom: 16rpx;
}

.thumb {
  width: 130rpx;
  height: 130rpx;
}

.small {
  grid-column: 1 / -1;
  min-height: 68rpx;
  font-size: 24rpx;
}

.ghost {
  color: #f8f7ff;
  background: rgba(255, 255, 255, 0.12);
}

.empty {
  color: rgba(248, 247, 255, 0.7);
  font-size: 24rpx;
}
</style>
