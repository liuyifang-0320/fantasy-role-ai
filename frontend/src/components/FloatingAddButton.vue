<template>
  <button class="floating-add" @click="$emit('click')" aria-label="创建数字人">
    <text>＋</text>
  </button>
</template>

<style scoped lang="scss">
.floating-add {
  position: fixed;
  right: 30rpx;
  bottom: 38rpx;
  z-index: 10;
  width: 108rpx;
  height: 108rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  color: #ffffff;
  font-size: 64rpx;
  line-height: 1;
  background: linear-gradient(135deg, #ff8db4, #8b7bff 58%, #7ee7f6);
  box-shadow: 0 18rpx 42rpx rgba(8, 8, 28, 0.32);
}
</style>
