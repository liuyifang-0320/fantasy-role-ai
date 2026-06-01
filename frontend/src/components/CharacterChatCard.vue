<template>
  <view class="chat-card" @click="$emit('click', character.character_id)">
    <image class="avatar" :src="avatarUrl" mode="aspectFill" />
    <view class="content">
      <view class="title-row">
        <text class="name">{{ character.character_name }}</text>
        <text class="intimacy">亲密度 {{ character.intimacy_level }}</text>
      </view>
      <text class="meta">你是 {{ character.user_persona_name }} · {{ character.relationship_with_user }}</text>
      <text class="message">{{ character.last_message }}</text>
    </view>
    <view class="pet-wrap">
      <image class="pet" :src="petUrl" mode="aspectFill" />
      <text class="pet-name">{{ character.pet.pet_name }}</text>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import { resolveAssetUrl } from '../api'

const props = defineProps({
  character: {
    type: Object,
    required: true,
  },
})
defineEmits(['click'])

const avatarUrl = computed(() => resolveAssetUrl(props.character.avatar))
const petUrl = computed(() => resolveAssetUrl(props.character.pet.pet_avatar))
</script>

<style scoped lang="scss">
.chat-card {
  display: grid;
  grid-template-columns: 92rpx minmax(0, 1fr) 92rpx;
  gap: 18rpx;
  align-items: center;
  padding: 22rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
  box-shadow: 0 20rpx 44rpx rgba(8, 8, 28, 0.18);
}

.avatar,
.pet {
  width: 92rpx;
  height: 92rpx;
  border-radius: 8px;
}

.content {
  min-width: 0;
}

.title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
}

.name {
  font-size: 32rpx;
  font-weight: 700;
}

.intimacy {
  flex-shrink: 0;
  padding: 4rpx 10rpx;
  border-radius: 999rpx;
  background: rgba(255, 141, 180, 0.18);
  color: #ffd4e4;
  font-size: 22rpx;
}

.meta,
.message,
.pet-name {
  display: block;
}

.meta {
  margin-top: 6rpx;
  color: rgba(248, 247, 255, 0.74);
  font-size: 24rpx;
}

.message {
  margin-top: 10rpx;
  overflow: hidden;
  color: rgba(248, 247, 255, 0.92);
  font-size: 26rpx;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pet-wrap {
  text-align: center;
}

.pet-name {
  margin-top: 6rpx;
  color: rgba(248, 247, 255, 0.72);
  font-size: 20rpx;
}
</style>
