<template>
  <view class="gradient-page">
    <slot />
  </view>
</template>

<style scoped lang="scss">
.gradient-page {
  min-height: 100vh;
  padding: 28rpx 28rpx 40rpx;
  background:
    radial-gradient(circle at top right, rgba(255, 141, 180, 0.2), transparent 32%),
    radial-gradient(circle at 12% 18%, rgba(126, 231, 246, 0.16), transparent 26%),
    linear-gradient(145deg, #120923 0%, #1c1450 48%, #163d67 100%);
}
</style>
