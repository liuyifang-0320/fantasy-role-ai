<template>
  <GradientPage v-if="character">
    <RoleCard :character="character" />

    <view v-if="project" class="project-summary">
      <text class="section-title">所属剧本项目</text>
      <view class="panel">
        <text class="panel-title">{{ project.title }}</text>
        <text class="muted">project_id: {{ project.project_id }}</text>
      </view>
    </view>

    <view class="detail-grid">
      <view class="panel">
        <text class="panel-title">用户扮演身份</text>
        <text class="strong">{{ character.user_persona_name }}</text>
        <text class="muted">你将以这个身份继续进入剧情。</text>
      </view>

      <view class="panel">
        <text class="panel-title">关系与亲密度</text>
        <text class="strong">{{ character.relationship_with_user }}</text>
        <text class="muted">{{ character.relationship_stage }} · 亲密度 {{ character.intimacy_level }}</text>
      </view>
    </view>

    <view v-if="character.profile" class="profile-summary">
      <text class="section-title">角色设定摘要</text>
      <view class="panel">
        <text class="panel-title">说话风格</text>
        <text class="strong compact">{{ character.profile.speaking_style }}</text>
      </view>
      <view class="panel">
        <text class="panel-title">关系摘要</text>
        <text class="muted profile-copy">{{ character.profile.relationship_summary }}</text>
      </view>
      <view class="panel">
        <text class="panel-title">防剧透规则</text>
        <text
          v-for="rule in character.profile.spoiler_guardrails"
          :key="rule"
          class="muted profile-copy"
        >
          {{ rule }}
        </text>
      </view>
    </view>

    <view class="knowledge-summary">
      <text class="section-title">知识库摘要</text>
      <view class="panel">
        <text class="panel-title">已有知识片段</text>
        <text class="strong">{{ character.knowledge_chunk_count || 0 }}</text>
      </view>
      <view
        v-for="chunk in character.knowledge_chunks_preview || []"
        :key="chunk.chunk_id"
        class="panel"
      >
        <text class="panel-title">{{ chunk.chunk_id }} · {{ chunk.visibility }}</text>
        <text class="muted profile-copy">{{ chunk.content_preview }}</text>
      </view>
    </view>

    <view class="memory-summary">
      <text class="section-title">长期记忆摘要</text>
      <view class="panel">
        <text class="panel-title">有效长期记忆</text>
        <text class="strong">{{ activeMemoryCount }}</text>
      </view>
      <view
        v-for="memory in importantMemories"
        :key="memory.memory_id"
        class="panel"
      >
        <text class="panel-title">{{ memoryTypeLabel(memory.memory_type) }} · 重要度 {{ memory.importance }}</text>
        <text class="muted profile-copy">{{ memory.memory_content }}</text>
      </view>
      <button class="ghost memory-button" @click="goMemory">查看全部记忆</button>
    </view>

    <view v-if="settings" class="settings-summary">
      <text class="section-title">角色调教摘要</text>
      <view class="panel summary-grid">
        <view>
          <text class="panel-title">语气风格</text>
          <text class="strong compact">{{ toneLabel(settings.tone_style) }}</text>
        </view>
        <view>
          <text class="panel-title">回复长度</text>
          <text class="strong compact">{{ replyLengthLabel(settings.reply_length) }}</text>
        </view>
        <view>
          <text class="panel-title">亲密模式</text>
          <text class="strong compact">{{ intimacyLabel(settings.intimacy_mode) }}</text>
        </view>
        <view>
          <text class="panel-title">剧透保护</text>
          <text class="strong compact">{{ settings.spoiler_protection ? '开启' : '关闭' }}</text>
        </view>
        <view>
          <text class="panel-title">Q版桌宠</text>
          <text class="strong compact">{{ settings.pet_enabled ? '开启' : '关闭' }}</text>
        </view>
      </view>
    </view>

    <view class="pet-zone">
      <text class="section-title">Q版桌宠</text>
      <PetWidget
        :pet-avatar="petAvatarUrl"
        :pet-name="character.pet.pet_name"
        :status="character.pet.pet_status"
        :intimacy-level="character.intimacy_level"
      />
      <view v-if="activePetAsset" class="panel pet-asset-card">
        <text class="panel-title">当前 active 桌宠资产</text>
        <text class="strong compact">{{ activePetAsset.style }}</text>
        <text class="muted">provider: {{ activePetAsset.generation_provider }} · status: {{ activePetAsset.generation_status }}</text>
      </view>
      <button class="ghost memory-button" @click="goPetAssets">管理桌宠形象</button>
    </view>

    <view class="actions">
      <button class="primary" @click="continueChat">继续上次对话</button>
      <button class="ghost" @click="startNewChat">开始新对话</button>
      <button class="ghost" @click="goMemory">查看记忆</button>
      <button class="ghost" @click="goSettings">自定义角色</button>
      <button v-if="character.project_id" class="ghost" @click="goProject">返回项目详情</button>
    </view>
  </GradientPage>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { api, resolveAssetUrl } from '../../api'
import GradientPage from '../../components/GradientPage.vue'
import PetWidget from '../../components/PetWidget.vue'
import RoleCard from '../../components/RoleCard.vue'

const character = ref(null)
const project = ref(null)
const settings = ref(null)
const latestSessionId = ref('')
const memories = ref({
  user_preference_memory: [],
  relationship_memory: [],
  story_interaction_memory: [],
  emotional_state_memory: [],
  custom_memory: [],
})
const memoryTypeMap = {
  user_preference: '用户偏好',
  relationship: '关系记忆',
  story_interaction: '剧情互动',
  emotional_state: '情绪状态',
  custom: '自定义',
}
const toneMap = {
  original: '遵循原角色',
  gentle: '温柔',
  cold: '清冷',
  playful: '俏皮',
  mature: '成熟姐姐',
  yandere_light: '轻病娇',
  poetic: '诗意克制',
}
const replyLengthMap = {
  short: '短',
  medium: '中等',
  long: '长',
}
const intimacyMap = {
  low: '低',
  normal: '正常',
  high: '高',
}
const allMemories = computed(() =>
  Object.values(memories.value).flat()
)
const activeMemoryCount = computed(() => allMemories.value.length)
const importantMemories = computed(() =>
  [...allMemories.value]
    .sort((a, b) => b.importance - a.importance)
    .slice(0, 3)
)
const activePetAsset = computed(() => character.value?.active_pet_asset || null)
const petAvatarUrl = computed(() =>
  resolveAssetUrl(activePetAsset.value?.image_url || character.value?.pet?.pet_avatar)
)

onLoad(async ({ character_id }) => {
  const characterId = getCharacterId(character_id)
  if (!characterId) {
    showMissingCharacterIdToast()
    return
  }
  character.value = await api.getCharacter(characterId)
  if (character.value.project_id) {
    project.value = await api.getProject(character.value.project_id)
  }
  settings.value = await api.getCharacterSettings(characterId)
  memories.value = {
    ...memories.value,
    ...(await api.getMemory(characterId)),
  }
  const sessions = await api.getCharacterSessions(characterId)
  latestSessionId.value = sessions[0]?.session_id || ''
})

function getCharacterId(item) {
  if (typeof item === 'string') return item
  if (item && item.character_id) return item.character_id
  if (item && item.id) return item.id
  return ''
}

function showMissingCharacterIdToast() {
  uni.showToast({ title: '角色 ID 缺失，无法进入详情页。', icon: 'none' })
}

function continueChat() {
  const characterId = getCharacterId(character.value)
  if (!characterId) {
    showMissingCharacterIdToast()
    return
  }
  const sessionQuery = latestSessionId.value
    ? `&session_id=${encodeURIComponent(latestSessionId.value)}`
    : ''
  uni.navigateTo({
    url: `/pages/chat/index?character_id=${encodeURIComponent(characterId)}${sessionQuery}`,
  })
}

function startNewChat() {
  const characterId = getCharacterId(character.value)
  if (!characterId) {
    showMissingCharacterIdToast()
    return
  }
  uni.navigateTo({
    url: `/pages/chat/index?character_id=${encodeURIComponent(characterId)}`,
  })
}

function goMemory() {
  const characterId = getCharacterId(character.value)
  if (!characterId) {
    showMissingCharacterIdToast()
    return
  }
  uni.navigateTo({
    url: `/pages/memory/index?character_id=${encodeURIComponent(characterId)}`,
  })
}

function goSettings() {
  const characterId = getCharacterId(character.value)
  if (!characterId) {
    showMissingCharacterIdToast()
    return
  }
  uni.navigateTo({
    url: `/pages/character-settings/index?character_id=${encodeURIComponent(characterId)}`,
  })
}

function goPetAssets() {
  const characterId = getCharacterId(character.value)
  if (!characterId) {
    showMissingCharacterIdToast()
    return
  }
  uni.navigateTo({
    url: `/pages/pet-assets/index?character_id=${encodeURIComponent(characterId)}`,
  })
}

function goProject() {
  uni.navigateTo({
    url: `/pages/project-detail/index?project_id=${character.value.project_id}`,
  })
}

function memoryTypeLabel(memoryType) {
  return memoryTypeMap[memoryType] || memoryType
}

function toneLabel(value) {
  return toneMap[value] || value
}

function replyLengthLabel(value) {
  return replyLengthMap[value] || value
}

function intimacyLabel(value) {
  return intimacyMap[value] || value
}
</script>

<style scoped lang="scss">
.detail-grid {
  display: grid;
  gap: 18rpx;
  margin-top: 22rpx;
}

.panel {
  padding: 22rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
}

.panel text {
  display: block;
}

.panel-title,
.section-title {
  color: rgba(248, 247, 255, 0.68);
  font-size: 24rpx;
}

.strong {
  margin-top: 10rpx;
  font-size: 32rpx;
  font-weight: 700;
}

.muted {
  margin-top: 8rpx;
  color: rgba(248, 247, 255, 0.76);
  font-size: 24rpx;
}

.pet-zone {
  margin-top: 24rpx;
}

.pet-asset-card {
  margin-top: 16rpx;
}

.profile-summary {
  display: grid;
  gap: 16rpx;
  margin-top: 24rpx;
}

.project-summary {
  display: grid;
  gap: 16rpx;
  margin-top: 24rpx;
}

.knowledge-summary {
  display: grid;
  gap: 16rpx;
  margin-top: 24rpx;
}

.memory-summary {
  display: grid;
  gap: 16rpx;
  margin-top: 24rpx;
}

.settings-summary {
  display: grid;
  gap: 16rpx;
  margin-top: 24rpx;
}

.knowledge-summary .section-title {
  display: block;
}

.memory-summary .section-title {
  display: block;
}

.settings-summary .section-title {
  display: block;
}

.profile-summary .section-title {
  display: block;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18rpx;
}

.compact {
  font-size: 28rpx;
}

.profile-copy {
  line-height: 1.7;
}

.pet-zone .section-title {
  display: block;
  margin-bottom: 16rpx;
}

.actions {
  display: grid;
  gap: 16rpx;
  margin-top: 28rpx;
}

.memory-button {
  min-height: 76rpx;
}

.primary,
.ghost {
  border-radius: 8px;
}

.primary {
  color: #1b1036;
  font-weight: 700;
  background: linear-gradient(135deg, #ffd166, #ff8db4, #7ee7f6);
}

.ghost {
  color: #f8f7ff;
  background: rgba(255, 255, 255, 0.12);
}
</style>
