<template>
  <GradientPage>
    <view class="hero">
      <view>
        <text class="eyebrow">我的数字人</text>
        <text class="title">幻梦数字人</text>
        <text class="slogan">上传剧本，唤醒你的角色</text>
      </view>
      <view class="top-actions">
        <button class="settings-button" @click="goUser">
          {{ currentUser?.nickname || '用户' }}
        </button>
        <button class="settings-button" @click="goSettings">设置</button>
      </view>
    </view>

    <view class="project-entry" @click="goProjects">
      <view>
        <text class="entry-title">剧本项目</text>
        <text class="entry-copy">按项目管理资料、角色和知识库，避免同名角色串资料。</text>
      </view>
      <text class="entry-arrow">进入</text>
    </view>

    <view class="section">
      <text class="section-title">最近陪伴</text>
      <view class="card-list" v-if="characters.length">
        <CharacterChatCard
          v-for="character in characters"
          :key="character.character_id"
          :character="character"
          @click="goDetail"
        />
      </view>
      <view v-else class="empty-state">
        <text>还没有数字人，先唤醒第一个角色吧。</text>
      </view>
    </view>

    <FloatingAddButton @click="goCreate" />
  </GradientPage>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { api } from '../../api'
import CharacterChatCard from '../../components/CharacterChatCard.vue'
import FloatingAddButton from '../../components/FloatingAddButton.vue'
import GradientPage from '../../components/GradientPage.vue'

const characters = ref([])
const currentUser = ref(null)

async function loadCharacters() {
  currentUser.value = await api.getCurrentUser()
  characters.value = await api.getCharacters()
}

function goCreate() {
  uni.navigateTo({ url: '/pages/create-character/index' })
}

function goProjects() {
  uni.navigateTo({ url: '/pages/projects/index' })
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

function goDetail(item) {
  const characterId = getCharacterId(item)
  if (!characterId) {
    showMissingCharacterIdToast()
    return
  }
  uni.navigateTo({
    url: `/pages/character-detail/index?character_id=${encodeURIComponent(characterId)}`,
  })
}

function goSettings() {
  uni.navigateTo({ url: '/pages/settings/index' })
}

function goUser() {
  uni.navigateTo({ url: '/pages/user/index' })
}

onShow(loadCharacters)
</script>

<style scoped lang="scss">
.hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20rpx;
  margin-top: 8rpx;
}

.hero text {
  display: block;
}

.eyebrow {
  color: #7ee7f6;
  font-size: 24rpx;
}

.title {
  margin-top: 8rpx;
  font-size: 48rpx;
  font-weight: 700;
}

.slogan {
  margin-top: 10rpx;
  color: rgba(248, 247, 255, 0.74);
  font-size: 26rpx;
}

.settings-button {
  min-width: 104rpx;
  height: 58rpx;
  margin: 0;
  padding: 0 18rpx;
  color: #f8f7ff;
  font-size: 24rpx;
  line-height: 58rpx;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.12);
}

.top-actions {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
  align-items: flex-end;
}

.project-entry {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
  margin-top: 28rpx;
  padding: 22rpx;
  border: 1rpx solid rgba(126, 231, 246, 0.24);
  border-radius: 8px;
  background: rgba(126, 231, 246, 0.1);
}

.project-entry text {
  display: block;
}

.entry-title {
  font-size: 30rpx;
  font-weight: 700;
}

.entry-copy {
  margin-top: 8rpx;
  color: rgba(248, 247, 255, 0.72);
  font-size: 24rpx;
  line-height: 1.6;
}

.entry-arrow {
  color: #7ee7f6;
  font-size: 24rpx;
  font-weight: 700;
}

.section {
  margin-top: 40rpx;
}

.section-title {
  display: block;
  margin-bottom: 18rpx;
  font-size: 28rpx;
  font-weight: 700;
}

.card-list {
  display: grid;
  gap: 18rpx;
}

.empty-state {
  padding: 28rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
  color: rgba(248, 247, 255, 0.74);
}
</style>
