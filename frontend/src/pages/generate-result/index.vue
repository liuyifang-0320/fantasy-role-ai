<template>
  <GradientPage v-if="character">
    <view class="page-head">
      <text class="title">数字人已生成</text>
      <text class="subtitle">角色生成仍为 mock，但已接入真实文件解析结果。</text>
      <text class="source-note">当前角色设定来源于：用户填写信息 + 上传文本规则抽取。未上传正式剧本时，生成结果仅为测试/占位内容。</text>
    </view>

    <RoleCard :character="character" />

    <view v-if="project" class="project-section">
      <text class="section-title">所属剧本项目</text>
      <view class="profile-block">
        <text class="profile-label">{{ project.title }}</text>
        <text class="profile-copy">project_id: {{ project.project_id }}</text>
      </view>
    </view>

    <view class="result-grid">
      <view class="summary">
        <text class="label">用户扮演身份</text>
        <text class="value">{{ character.user_persona_name }}</text>
        <text class="label">两人关系</text>
        <text class="value">{{ character.relationship_with_user }}</text>
      </view>
      <PetWidget
        :pet-avatar="petAvatarUrl"
        :pet-name="character.pet.pet_name"
        :status="character.pet.pet_status"
        :intimacy-level="character.intimacy_level"
      />
    </view>

    <view v-if="activePetAsset" class="pet-asset-section">
      <text class="section-title">当前桌宠资产</text>
      <view class="profile-block">
        <image class="asset-preview" :src="petAvatarUrl" mode="aspectFit" />
        <text class="profile-label">风格：{{ activePetAsset.style }}</text>
        <text class="profile-copy">provider: {{ activePetAsset.generation_provider }} · status: {{ activePetAsset.generation_status }}</text>
      </view>
    </view>

    <view v-if="parsedDocuments.length" class="parsed-section">
      <text class="section-title">使用的解析文档</text>
      <view class="parsed-list">
        <view
          v-for="document in parsedDocuments"
          :key="document.parsed_id"
          class="parsed-card"
        >
          <view class="parsed-head">
            <text class="parsed-name">{{ document.filename }}</text>
            <text class="parsed-status">{{ document.parse_status }}</text>
          </view>
          <text class="parsed-meta">字数 {{ document.word_count }}</text>
          <text class="parsed-preview">{{ document.text_preview || '暂无可展示摘要' }}</text>
        </view>
      </view>
    </view>

    <view v-if="profile" class="profile-section">
      <text class="section-title">角色设定档案</text>

      <view class="profile-grid">
        <view class="profile-card">
          <text class="profile-label">角色身份</text>
          <text class="profile-value">{{ profile.extracted_identity }}</text>
        </view>
        <view class="profile-card">
          <text class="profile-label">性格</text>
          <text class="profile-value">{{ profile.extracted_personality }}</text>
        </view>
        <view class="profile-card">
          <text class="profile-label">说话风格</text>
          <text class="profile-value">{{ profile.speaking_style }}</text>
        </view>
        <view class="profile-card">
          <text class="profile-label">剧情阶段</text>
          <text class="profile-value">{{ profile.story_stage }}</text>
        </view>
      </view>

      <view class="profile-block">
        <text class="profile-label">背景摘要</text>
        <text class="profile-copy">{{ profile.background_summary }}</text>
      </view>

      <view class="profile-block">
        <text class="profile-label">关系摘要</text>
        <text class="profile-copy">{{ profile.relationship_summary }}</text>
      </view>

      <view class="profile-block">
        <text class="profile-label">已知事实</text>
        <view class="fact-list">
          <text
            v-for="fact in profile.known_facts"
            :key="fact"
            class="fact-item"
          >
            {{ fact }}
          </text>
        </view>
      </view>

      <view class="profile-block">
        <text class="profile-label">防剧透规则</text>
        <view class="fact-list">
          <text
            v-for="rule in profile.spoiler_guardrails"
            :key="rule"
            class="fact-item"
          >
            {{ rule }}
          </text>
        </view>
      </view>
    </view>

    <view class="knowledge-section">
      <text class="section-title">剧本知识库</text>
      <view class="profile-block">
        <text class="profile-label">知识片段数</text>
        <text class="profile-value">{{ character.knowledge_chunk_count || 0 }}</text>
      </view>
      <view
        v-for="chunk in character.knowledge_chunks_preview || []"
        :key="chunk.chunk_id"
        class="knowledge-card"
      >
        <view class="parsed-head">
          <text class="parsed-name">{{ chunk.chunk_id }}</text>
          <text class="parsed-status">{{ chunk.visibility }}</text>
        </view>
        <text class="parsed-meta">{{ chunk.chapter }}</text>
        <text class="parsed-preview">{{ chunk.content_preview }}</text>
      </view>
    </view>

    <view class="actions">
      <button class="primary" @click="goChat">进入聊天</button>
      <button v-if="character.project_id" class="ghost" @click="goProject">返回项目详情</button>
      <button class="ghost" @click="goHome">回到我的数字人</button>
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
const parsedDocuments = ref([])
const profile = ref(null)
const project = ref(null)
const activePetAsset = computed(() => character.value?.active_pet_asset || null)
const petAvatarUrl = computed(() =>
  resolveAssetUrl(activePetAsset.value?.image_url || character.value?.pet?.pet_avatar)
)

onLoad(async ({ character_id, parsed_ids }) => {
  const cachedCharacter = uni.getStorageSync('latestGeneratedCharacter')
  character.value =
    cachedCharacter?.character_id === character_id
      ? cachedCharacter
      : await api.getCharacter(character_id)
  parsedDocuments.value = character.value.parsed_documents || uni.getStorageSync('latestParsedDocuments') || []
  profile.value = character.value.profile || uni.getStorageSync('latestCharacterProfile') || null
  if (character.value.project_id) {
    project.value = await api.getProject(character.value.project_id)
  }

  if (!parsedDocuments.value.length && parsed_ids) {
    parsedDocuments.value = await Promise.all(
      parsed_ids
        .split(',')
        .filter(Boolean)
        .map((parsedId) => api.getParsedDocument(parsedId))
    )
  }
})

function goChat() {
  const characterId = getCharacterId(character.value)
  if (!characterId) {
    showMissingCharacterIdToast()
    return
  }
  uni.navigateTo({
    url: `/pages/chat/index?character_id=${encodeURIComponent(characterId)}`,
  })
}

function getCharacterId(item) {
  if (typeof item === 'string') return item
  if (item && item.character_id) return item.character_id
  if (item && item.id) return item.id
  return ''
}

function showMissingCharacterIdToast() {
  uni.showToast({ title: '角色 ID 缺失，无法进入详情页。', icon: 'none' })
}

function goHome() {
  uni.reLaunch({ url: '/pages/index/index' })
}

function goProject() {
  if (character.value?.project_id) {
    uni.navigateTo({ url: `/pages/project-detail/index?project_id=${character.value.project_id}` })
  }
}
</script>

<style scoped lang="scss">
.page-head {
  margin-bottom: 24rpx;
}

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
}

.source-note {
  margin-top: 12rpx;
  color: rgba(248, 247, 255, 0.78);
  font-size: 24rpx;
  line-height: 1.7;
}

.result-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 18rpx;
  align-items: stretch;
  margin-top: 22rpx;
}

.summary {
  padding: 24rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
}

.summary text {
  display: block;
}

.label {
  color: rgba(248, 247, 255, 0.66);
  font-size: 22rpx;
}

.value {
  margin: 8rpx 0 18rpx;
  font-size: 30rpx;
  font-weight: 700;
}

.parsed-section {
  margin-top: 24rpx;
}

.project-section {
  margin-top: 24rpx;
}

.pet-asset-section {
  margin-top: 24rpx;
}

.asset-preview {
  width: 180rpx;
  height: 180rpx;
  margin-bottom: 14rpx;
}

.profile-section {
  margin-top: 24rpx;
}

.knowledge-section {
  margin-top: 24rpx;
}

.section-title {
  display: block;
  margin-bottom: 16rpx;
  font-size: 28rpx;
  font-weight: 700;
}

.parsed-list {
  display: grid;
  gap: 16rpx;
}

.parsed-card {
  padding: 22rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
}

.knowledge-card {
  margin-top: 16rpx;
  padding: 22rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
}

.parsed-head {
  display: flex;
  justify-content: space-between;
  gap: 16rpx;
}

.parsed-name {
  font-size: 26rpx;
  font-weight: 700;
}

.parsed-status,
.parsed-meta {
  color: #7ee7f6;
  font-size: 22rpx;
}

.parsed-meta,
.parsed-preview {
  display: block;
  margin-top: 10rpx;
}

.parsed-preview {
  color: rgba(248, 247, 255, 0.8);
  font-size: 24rpx;
  line-height: 1.7;
}

.profile-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
}

.profile-card,
.profile-block {
  padding: 22rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
}

.profile-block {
  margin-top: 16rpx;
}

.profile-label,
.profile-value,
.profile-copy,
.fact-item {
  display: block;
}

.profile-label {
  color: rgba(248, 247, 255, 0.66);
  font-size: 22rpx;
}

.profile-value {
  margin-top: 10rpx;
  font-size: 28rpx;
  font-weight: 700;
  line-height: 1.5;
}

.profile-copy,
.fact-item {
  margin-top: 10rpx;
  color: rgba(248, 247, 255, 0.82);
  font-size: 24rpx;
  line-height: 1.7;
}

.fact-list {
  display: grid;
  gap: 8rpx;
}

.actions {
  display: grid;
  gap: 16rpx;
  margin-top: 28rpx;
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
