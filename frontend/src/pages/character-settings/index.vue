<template>
  <GradientPage v-if="settings">
    <view class="page-head">
      <text class="title">角色调教配置</text>
      <text class="subtitle">当前是 Prompt 层角色配置，不是真正模型训练。没有 API Key 时仍使用 mock 回复，但配置会影响 mock 规则和 Prompt。</text>
      <text class="subtitle">角色调教不能用于色情、违法、自伤鼓励或诱导依赖；明显违规配置会被后端拒绝保存。</text>
    </view>

    <view class="section">
      <text class="section-title">基础身份</text>
      <view class="field">
        <text>角色显示名</text>
        <input v-model="form.display_name" placeholder="默认使用角色名" />
      </view>
      <view class="field">
        <text>用户扮演身份</text>
        <input v-model="form.user_persona_name" placeholder="例如：戴丽拉" />
      </view>
    </view>

    <view class="section">
      <text class="section-title">关系与称呼</text>
      <view class="field">
        <text>角色对用户称呼</text>
        <input v-model="form.nickname_for_user" placeholder="例如：戴丽拉、小笨蛋、姐姐" />
      </view>
      <view class="field">
        <text>关系设定</text>
        <input v-model="form.relationship_with_user" placeholder="情侣 / 暧昧 / 朋友 / 宿敌" />
      </view>
      <view class="field">
        <text>关系阶段</text>
        <input v-model="form.relationship_stage" placeholder="初识 / 暧昧期 / 热恋期 / 破镜重圆" />
      </view>
    </view>

    <view class="section">
      <text class="section-title">回复风格</text>
      <view class="field">
        <text>语气风格</text>
        <picker :range="toneOptions" range-key="label" @change="changeTone">
          <view class="picker">{{ optionLabel(toneOptions, form.tone_style) }}</view>
        </picker>
      </view>
      <view class="field">
        <text>回复长度</text>
        <picker :range="replyLengthOptions" range-key="label" @change="changeReplyLength">
          <view class="picker">{{ optionLabel(replyLengthOptions, form.reply_length) }}</view>
        </picker>
      </view>
      <view class="field">
        <text>亲密模式</text>
        <picker :range="intimacyOptions" range-key="label" @change="changeIntimacy">
          <view class="picker">{{ optionLabel(intimacyOptions, form.intimacy_mode) }}</view>
        </picker>
      </view>
      <view class="field">
        <text>性格微调</text>
        <textarea v-model="form.personality_override" placeholder="例如：更温柔一点，但不要过度甜腻" />
      </view>
      <view class="field">
        <text>说话风格微调</text>
        <textarea v-model="form.speaking_style_override" placeholder="例如：少说大道理，多安慰" />
      </view>
      <view class="field">
        <text>自定义补充设定</text>
        <textarea v-model="form.custom_prompt_notes" placeholder="写下你希望角色遵守的补充设定" />
      </view>
    </view>

    <view class="section">
      <text class="section-title">桌宠设置</text>
      <view class="switch-row">
        <text>Q版桌宠</text>
        <switch :checked="form.pet_enabled" color="#7ee7f6" @change="changePetEnabled" />
      </view>
      <view class="field">
        <text>桌宠位置</text>
        <picker :range="petPositionOptions" range-key="label" @change="changePetPosition">
          <view class="picker">{{ optionLabel(petPositionOptions, form.pet_position) }}</view>
        </picker>
      </view>
    </view>

    <view class="section">
      <text class="section-title">安全与边界</text>
      <view class="switch-row">
        <text>剧透保护</text>
        <switch :checked="form.spoiler_protection" color="#7ee7f6" @change="changeSpoilerProtection" />
      </view>
      <view class="field">
        <text>禁止话题</text>
        <textarea v-model="form.forbidden_topics" placeholder="多个话题可用换行或逗号分隔" />
      </view>
    </view>

    <view class="actions">
      <button class="primary" @click="saveSettings">保存配置</button>
      <button class="ghost" @click="resetSettings">重置默认配置</button>
    </view>

    <view class="section">
      <button class="debug-toggle" @click="showPreview = !showPreview">
        {{ showPreview ? '收起 Prompt 预览' : '展开 Prompt 预览' }}
      </button>
      <view v-if="showPreview" class="preview">
        <text>{{ promptPreview || '暂无预览' }}</text>
      </view>
    </view>
  </GradientPage>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { api } from '../../api'
import GradientPage from '../../components/GradientPage.vue'

const characterId = ref('')
const settings = ref(null)
const promptPreview = ref('')
const showPreview = ref(false)
const form = ref(defaultForm())

const toneOptions = [
  { label: '遵循原角色', value: 'original' },
  { label: '温柔', value: 'gentle' },
  { label: '清冷', value: 'cold' },
  { label: '俏皮', value: 'playful' },
  { label: '成熟姐姐', value: 'mature' },
  { label: '轻病娇', value: 'yandere_light' },
  { label: '诗意克制', value: 'poetic' },
]
const replyLengthOptions = [
  { label: '短', value: 'short' },
  { label: '中等', value: 'medium' },
  { label: '长', value: 'long' },
]
const intimacyOptions = [
  { label: '低', value: 'low' },
  { label: '正常', value: 'normal' },
  { label: '高', value: 'high' },
]
const petPositionOptions = [
  { label: '右下角', value: 'bottom_right' },
  { label: '左下角', value: 'bottom_left' },
  { label: '悬浮', value: 'floating' },
]

onLoad(async ({ character_id }) => {
  characterId.value = character_id
  await loadSettings()
})

function defaultForm() {
  return {
    display_name: '',
    user_persona_name: '',
    nickname_for_user: '',
    relationship_with_user: '',
    relationship_stage: '',
    tone_style: 'original',
    reply_length: 'medium',
    intimacy_mode: 'normal',
    spoiler_protection: true,
    pet_enabled: true,
    pet_position: 'bottom_right',
    personality_override: '',
    speaking_style_override: '',
    custom_prompt_notes: '',
    forbidden_topics: '',
  }
}

async function loadSettings() {
  settings.value = await api.getCharacterSettings(characterId.value)
  form.value = { ...defaultForm(), ...settings.value }
  await loadPromptPreview()
}

async function loadPromptPreview() {
  const response = await api.getCharacterSettingsPromptPreview(characterId.value)
  promptPreview.value = response.prompt_preview
}

async function saveSettings() {
  try {
    settings.value = await api.updateCharacterSettings(characterId.value, buildPayload())
    form.value = { ...defaultForm(), ...settings.value }
    await loadPromptPreview()
    uni.showToast({
      title: '配置已保存',
      icon: 'none',
    })
  } catch (error) {
    uni.showToast({
      title: error.message || '配置包含不适合保存的安全风险内容',
      icon: 'none',
    })
  }
}

async function resetSettings() {
  settings.value = await api.resetCharacterSettings(characterId.value)
  form.value = { ...defaultForm(), ...settings.value }
  await loadPromptPreview()
  uni.showToast({
    title: '已重置默认配置',
    icon: 'none',
  })
}

function buildPayload() {
  return {
    display_name: form.value.display_name,
    user_persona_name: form.value.user_persona_name,
    nickname_for_user: form.value.nickname_for_user,
    relationship_with_user: form.value.relationship_with_user,
    relationship_stage: form.value.relationship_stage,
    tone_style: form.value.tone_style,
    reply_length: form.value.reply_length,
    intimacy_mode: form.value.intimacy_mode,
    spoiler_protection: form.value.spoiler_protection,
    pet_enabled: form.value.pet_enabled,
    pet_position: form.value.pet_position,
    personality_override: form.value.personality_override,
    speaking_style_override: form.value.speaking_style_override,
    custom_prompt_notes: form.value.custom_prompt_notes,
    forbidden_topics: form.value.forbidden_topics,
  }
}

function optionLabel(options, value) {
  return options.find((option) => option.value === value)?.label || value
}

function changeTone(event) {
  form.value.tone_style = toneOptions[Number(event.detail.value)].value
}

function changeReplyLength(event) {
  form.value.reply_length = replyLengthOptions[Number(event.detail.value)].value
}

function changeIntimacy(event) {
  form.value.intimacy_mode = intimacyOptions[Number(event.detail.value)].value
}

function changePetPosition(event) {
  form.value.pet_position = petPositionOptions[Number(event.detail.value)].value
}

function changePetEnabled(event) {
  form.value.pet_enabled = event.detail.value
}

function changeSpoilerProtection(event) {
  form.value.spoiler_protection = event.detail.value
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

.section {
  display: grid;
  gap: 16rpx;
  margin-top: 24rpx;
}

.section-title {
  font-size: 28rpx;
  font-weight: 700;
}

.field,
.switch-row,
.preview {
  padding: 20rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
}

.field text,
.preview text {
  display: block;
}

.field > text,
.switch-row text {
  color: rgba(248, 247, 255, 0.72);
  font-size: 24rpx;
}

.field input,
.field textarea,
.picker {
  width: 100%;
  margin-top: 12rpx;
  padding: 0 16rpx;
  border-radius: 8px;
  border: 1rpx solid rgba(255, 255, 255, 0.12);
  background: rgba(19, 12, 47, 0.52);
  box-sizing: border-box;
}

.field input,
.picker {
  height: 76rpx;
  line-height: 76rpx;
}

.field textarea {
  min-height: 132rpx;
  padding-top: 14rpx;
  line-height: 1.6;
}

.switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
}

.actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14rpx;
  margin-top: 24rpx;
}

.primary,
.ghost,
.debug-toggle {
  border-radius: 8px;
}

.primary {
  color: #1b1036;
  font-weight: 700;
  background: linear-gradient(135deg, #ffd166, #7ee7f6);
}

.ghost,
.debug-toggle {
  color: #f8f7ff;
  background: rgba(255, 255, 255, 0.12);
}

.preview {
  color: rgba(248, 247, 255, 0.82);
  font-size: 24rpx;
  line-height: 1.7;
  white-space: pre-wrap;
}
</style>
