<template>
  <view class="role-card">
    <image class="avatar" :src="avatarUrl" mode="aspectFill" />
    <view class="copy">
      <text class="name">{{ character.character_name }}</text>
      <text class="identity">{{ character.character_identity }}</text>
      <text class="personality">{{ character.personality }}</text>
      <text class="description">{{ character.description }}</text>
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

const avatarUrl = computed(() => resolveAssetUrl(props.character.avatar))
</script>

<style scoped lang="scss">
.role-card {
  display: grid;
  grid-template-columns: 128rpx minmax(0, 1fr);
  gap: 20rpx;
  padding: 24rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.11);
}

.avatar {
  width: 128rpx;
  height: 128rpx;
  border-radius: 8px;
}

.copy text {
  display: block;
}

.name {
  font-size: 34rpx;
  font-weight: 700;
}

.identity {
  margin-top: 4rpx;
  color: #7ee7f6;
  font-size: 24rpx;
}

.personality {
  margin-top: 12rpx;
  color: #ffd4e4;
  font-size: 24rpx;
}

.description {
  margin-top: 12rpx;
  color: rgba(248, 247, 255, 0.8);
  font-size: 26rpx;
  line-height: 1.6;
}
</style>
