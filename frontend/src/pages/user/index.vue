<template>
  <GradientPage>
    <view class="page-head">
      <text class="title">用户中心</text>
      <text class="subtitle">当前是开发测试用户系统，后续可接微信登录。请不要输入真实敏感信息。</text>
    </view>

    <view v-if="currentUser" class="panel">
      <text class="panel-title">当前用户</text>
      <text class="strong">{{ currentUser.nickname }}</text>
      <text class="muted">user_id: {{ currentUser.user_id }}</text>
      <text class="muted">auth_provider: {{ currentUser.auth_provider }}</text>
    </view>

    <view class="panel">
      <text class="panel-title">微信登录（预留）</text>
      <text class="muted">当前 user_id 是开发测试身份。正式上线后将使用微信 openid 绑定用户。</text>
      <button class="ghost" @click="showWechatReserved">微信登录（预留）</button>
    </view>

    <view class="panel">
      <text class="panel-title">创建 / 切换开发用户</text>
      <input
        v-model="nickname"
        class="input"
        placeholder="输入测试昵称，例如 测试用户A"
      />
      <button class="primary" @click="devLogin">创建 mock 用户并切换</button>
    </view>

    <view class="panel">
      <text class="panel-title">按 user_id 切换</text>
      <input
        v-model="switchUserId"
        class="input"
        placeholder="输入 user_id，例如 user_001"
      />
      <button class="ghost" @click="switchUser">切换到该用户</button>
      <button class="ghost" @click="switchDefault">切换回 dev_user</button>
    </view>

    <view class="panel">
      <text class="panel-title">隐私与数据</text>
      <text class="muted">当前是开发版数据导出 / 删除骨架。正式上线前需要完整隐私政策、用户协议和更严格的数据删除流程。</text>
      <button class="ghost" @click="exportData">导出我的数据</button>
      <button class="danger" @click="confirmDeleteData">删除我的数据（开发版）</button>
    </view>
  </GradientPage>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { api, setStoredUserId } from '../../api'
import GradientPage from '../../components/GradientPage.vue'

const currentUser = ref(null)
const nickname = ref('')
const switchUserId = ref('')

onShow(loadCurrentUser)

async function loadCurrentUser() {
  currentUser.value = await api.getCurrentUser()
  setStoredUserId(currentUser.value.user_id)
}

async function devLogin() {
  const user = await api.devLogin({
    nickname: nickname.value.trim() || '开发测试用户',
  })
  setStoredUserId(user.user_id)
  currentUser.value = user
  nickname.value = ''
  uni.showToast({ title: '已切换开发用户', icon: 'none' })
}

async function switchUser() {
  const userId = switchUserId.value.trim()
  if (!userId) {
    return
  }
  const user = await api.switchDevUser({ user_id: userId })
  setStoredUserId(user.user_id)
  currentUser.value = user
  switchUserId.value = ''
}

async function switchDefault() {
  const user = await api.switchDevUser({ user_id: 'dev_user' })
  setStoredUserId(user.user_id)
  currentUser.value = user
}

function showWechatReserved() {
  uni.showToast({
    title: '微信登录将在正式小程序阶段接入，目前使用开发测试用户。',
    icon: 'none',
  })
}

async function exportData() {
  const data = await api.exportUserData()
  uni.setStorageSync('latestUserDataExport', data)
  uni.showModal({
    title: '数据导出摘要',
    content: `项目 ${data.summary.project_count} 个，角色 ${data.summary.character_count} 个，记忆 ${data.summary.memory_count} 条。完整摘要已保存到本地缓存 latestUserDataExport。`,
    showCancel: false,
  })
}

function confirmDeleteData() {
  uni.showModal({
    title: '确认删除',
    content: '这是开发版软删除 / 归档骨架，只会处理当前用户数据，不会影响其他用户。是否继续？',
    success: async (result) => {
      if (!result.confirm) {
        return
      }
      const response = await api.deleteUserData()
      uni.showToast({
        title: response.message || '已执行开发版数据删除',
        icon: 'none',
      })
      await loadCurrentUser()
    },
  })
}
</script>

<style scoped lang="scss">
.page-head text,
.panel text {
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
  line-height: 1.7;
}

.panel {
  margin-top: 22rpx;
  padding: 22rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
}

.panel-title {
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
  color: rgba(248, 247, 255, 0.74);
  font-size: 24rpx;
  line-height: 1.6;
}

.input {
  height: 82rpx;
  margin-top: 16rpx;
  padding: 0 18rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  background: rgba(19, 12, 47, 0.58);
  color: #f8f7ff;
}

.primary,
.ghost {
  margin-top: 16rpx;
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

.danger {
  margin-top: 16rpx;
  color: #fff;
  border-radius: 8px;
  background: rgba(255, 93, 115, 0.72);
}
</style>
