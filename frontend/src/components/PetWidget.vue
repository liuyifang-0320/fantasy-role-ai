<template>
  <view class="pet-widget" :class="actionClass">
    <view v-if="bubbleText" class="bubble">{{ bubbleText }}</view>
    <image class="pet-avatar" :src="resolvedAvatar" mode="aspectFill" />
    <view class="caption">
      <text class="pet-name">{{ petName }}</text>
      <text class="status-text">{{ statusText }}</text>
      <text class="intimacy">亲密度 {{ intimacyLevel }}</text>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import { resolveAssetUrl } from '../api'

const props = defineProps({
  petAvatar: {
    type: String,
    default: '',
  },
  petName: {
    type: String,
    default: '',
  },
  status: {
    type: String,
    default: 'idle',
  },
  action: {
    type: String,
    default: '',
  },
  intimacyLevel: {
    type: Number,
    default: 0,
  },
})

const action = computed(() => props.action || props.status || 'idle')
const actionClass = computed(() => `is-${action.value}`)
const resolvedAvatar = computed(() => resolveAssetUrl(props.petAvatar))

const statusMap = {
  idle: '静静陪着你',
  happy: '开心地晃了晃',
  shy: '有点害羞地低下头',
  thinking: '正在认真思考',
  talking: '正在和你说话',
  comfort: '轻轻靠近你',
  surprised: '惊讶地眨了眨眼',
}

const statusText = computed(() => statusMap[action.value] || statusMap.idle)
const bubbleText = computed(() => {
  if (action.value === 'thinking') {
    return '...'
  }
  if (action.value === 'talking') {
    return '在听你说'
  }
  return ''
})
</script>

<style scoped lang="scss">
.pet-widget {
  position: relative;
  width: 220rpx;
  padding: 18rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.12);
  text-align: center;
  transition: transform 0.28s ease, opacity 0.28s ease;
}

.pet-avatar {
  width: 140rpx;
  height: 140rpx;
  border-radius: 50%;
  box-shadow: 0 16rpx 32rpx rgba(8, 8, 28, 0.22);
}

.caption text {
  display: block;
}

.pet-name {
  margin-top: 10rpx;
  font-size: 26rpx;
  font-weight: 700;
}

.status-text {
  margin-top: 6rpx;
  color: rgba(248, 247, 255, 0.76);
  font-size: 22rpx;
}

.intimacy {
  margin-top: 8rpx;
  color: #ffd4e4;
  font-size: 22rpx;
}

.bubble {
  position: absolute;
  top: -18rpx;
  right: 10rpx;
  min-width: 56rpx;
  padding: 8rpx 12rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.94);
  color: #352350;
  font-size: 20rpx;
}

.is-idle {
  animation: idleFloat 2.8s ease-in-out infinite;
}

.is-happy {
  animation: happyBounce 0.8s ease-in-out infinite alternate;
}

.is-shy {
  opacity: 0.84;
  transform: scale(0.96);
}

.is-thinking {
  transform: translateY(-4rpx);
}

.is-talking {
  animation: talkPulse 1s ease-in-out infinite;
}

.is-comfort {
  transform: translateX(-18rpx) translateY(4rpx);
}

.is-surprised {
  animation: surprisedShake 0.45s ease-in-out 1;
}

@keyframes idleFloat {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-8rpx);
  }
}

@keyframes happyBounce {
  from {
    transform: scale(1);
  }
  to {
    transform: scale(1.05) translateY(-6rpx);
  }
}

@keyframes talkPulse {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.03);
  }
}

@keyframes surprisedShake {
  0%,
  100% {
    transform: translateX(0);
  }
  25% {
    transform: translateX(-8rpx);
  }
  75% {
    transform: translateX(8rpx);
  }
}
</style>
