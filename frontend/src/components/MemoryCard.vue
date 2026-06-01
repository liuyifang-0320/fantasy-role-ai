<template>
  <view class="memory-card">
    <text>{{ content }}</text>
  </view>
</template>

<script setup>
defineProps({
  content: {
    type: String,
    required: true,
  },
})
</script>

<style scoped lang="scss">
.memory-card {
  padding: 18rpx 20rpx;
  border-left: 6rpx solid #7ee7f6;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
  color: rgba(248, 247, 255, 0.88);
  font-size: 26rpx;
  line-height: 1.6;
}
</style>
