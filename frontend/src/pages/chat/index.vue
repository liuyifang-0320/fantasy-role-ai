<template>
  <GradientPage v-if="character">
    <view class="chat-head">
      <image class="avatar" :src="avatarUrl" mode="aspectFill" />
      <view>
        <text class="name">{{ character.character_name }}</text>
        <text class="persona">你正在以{{ character.user_persona_name }}的身份和{{ character.character_name }}对话</text>
      </view>
    </view>

    <view v-if="providerDebug" class="provider-status">
      <text>{{ providerStatusText }}</text>
      <text class="provider-note">{{ providerModeNote }}</text>
    </view>

    <scroll-view class="message-list" scroll-y :scroll-into-view="scrollTarget">
      <view
        v-for="message in messages"
        :id="message.id"
        :key="message.id"
        class="message"
        :class="message.role"
      >
        <text>{{ message.content }}</text>
      </view>
    </scroll-view>

    <view class="debug-panel">
      <button class="debug-toggle" @click="showDebug = !showDebug">
        {{ showDebug ? '收起调试信息' : '展开调试信息' }}
      </button>
      <view v-if="showDebug" class="debug-content">
        <view class="debug-row">
          <text class="debug-label">configured_provider</text>
          <text>{{ providerDebug?.configured_provider || '-' }}</text>
        </view>
        <view class="debug-row">
          <text class="debug-label">provider</text>
          <text>{{ providerDebug?.provider || '-' }}</text>
        </view>
        <view class="debug-row">
          <text class="debug-label">model</text>
          <text>{{ providerDebug?.model || '-' }}</text>
        </view>
        <view class="debug-row">
          <text class="debug-label">base_url_configured</text>
          <text>{{ providerDebug?.base_url_configured ? '是' : '否' }}</text>
        </view>
        <view class="debug-row">
          <text class="debug-label">api_key_configured</text>
          <text>{{ providerDebug?.api_key_configured ? '是' : '否' }}</text>
        </view>
        <view class="debug-row">
          <text class="debug-label">fallback</text>
          <text>{{ providerDebug?.fallback ? '是' : '否' }}</text>
        </view>
        <view class="debug-copy">
          <text class="debug-label">fallback_reason</text>
          <text>{{ providerDebug?.fallback_reason || '无' }}</text>
        </view>
        <view class="debug-row">
          <text class="debug-label">使用 CharacterProfile</text>
          <text>{{ usesCharacterProfile ? '是' : '否' }}</text>
        </view>
        <view class="debug-row">
          <text class="debug-label">uses_character_settings</text>
          <text>{{ promptDebug?.uses_character_settings ? '是' : '否' }}</text>
        </view>
        <view class="debug-row">
          <text class="debug-label">uses_safety_prompt</text>
          <text>{{ promptDebug?.uses_safety_prompt ? '是' : '否' }}</text>
        </view>
        <view class="debug-row">
          <text class="debug-label">user_input_action</text>
          <text>{{ safetyDebug?.user_input_action || '-' }}</text>
        </view>
        <view class="debug-row">
          <text class="debug-label">assistant_output_action</text>
          <text>{{ safetyDebug?.assistant_output_action || '-' }}</text>
        </view>
        <view class="debug-copy">
          <text class="debug-label">safety matched_categories</text>
          <text>{{ safetyCategoriesText }}</text>
        </view>
        <view class="debug-copy">
          <text class="debug-label">settings_prompt_preview</text>
          <text>{{ promptDebug?.settings_prompt_preview || '暂无角色调教配置调试信息' }}</text>
        </view>
        <view class="debug-row">
          <text class="debug-label">retrieval_scope</text>
          <text>{{ retrievalScopeText }}</text>
        </view>
        <view class="debug-row">
          <text class="debug-label">上下文消息数</text>
          <text>{{ promptDebug?.context_message_count ?? 0 }}</text>
        </view>
        <view class="debug-row">
          <text class="debug-label">命中知识片段数</text>
          <text>{{ promptDebug?.retrieved_chunk_count ?? 0 }}</text>
        </view>
        <view class="debug-row">
          <text class="debug-label">active_memory_count</text>
          <text>{{ promptDebug?.active_memory_count ?? 0 }}</text>
        </view>
        <view class="debug-row">
          <text class="debug-label">active_relationship_count</text>
          <text>{{ promptDebug?.active_relationship_count ?? 0 }}</text>
        </view>
        <view class="debug-copy">
          <text class="debug-label">relationships_preview</text>
          <view
            v-if="promptDebug?.relationships_preview?.length"
            class="chunk-list"
          >
            <view
              v-for="relationship in promptDebug.relationships_preview"
              :key="relationship.relationship_id"
              class="chunk-item"
            >
              <text>{{ relationship.source_character_name }} · {{ relationship.relation_type }} · {{ relationship.target_character_name }}</text>
              <text>{{ relationship.relation_summary }}</text>
            </view>
          </view>
          <text v-else>暂无可注入角色关系。</text>
        </view>
        <view class="debug-copy">
          <text class="debug-label">active_memories_preview</text>
          <view
            v-if="promptDebug?.active_memories_preview?.length"
            class="chunk-list"
          >
            <view
              v-for="memory in promptDebug.active_memories_preview"
              :key="memory.memory_id"
              class="chunk-item"
            >
              <text>{{ memory.memory_type }} · 重要度 {{ memory.importance }}</text>
              <text>{{ memory.content }}</text>
            </view>
          </view>
          <text v-else>暂无可注入长期记忆。</text>
        </view>
        <view class="debug-copy">
          <text class="debug-label">retrieved_chunks_preview</text>
          <view
            v-if="promptDebug?.retrieved_chunks_preview?.length"
            class="chunk-list"
          >
            <view
              v-for="chunk in promptDebug.retrieved_chunks_preview"
              :key="chunk.chunk_id"
              class="chunk-item"
            >
              <text>{{ chunk.chunk_id }} · {{ chunk.visibility }}</text>
              <text>{{ chunk.content_preview }}</text>
            </view>
          </view>
          <text v-else>本轮未命中剧本知识片段。</text>
        </view>
        <view class="debug-copy">
          <text class="debug-label">system_prompt_preview</text>
          <text>{{ promptDebug?.system_prompt_preview || '暂无调试信息' }}</text>
        </view>
        <view class="debug-copy">
          <text class="debug-label">memory_debug candidates</text>
          <view
            v-if="memoryDebug?.candidates?.length"
            class="chunk-list"
          >
            <view
              v-for="candidate in memoryDebug.candidates"
              :key="`${candidate.memory_type}-${candidate.content}`"
              class="chunk-item"
            >
              <text>{{ candidate.memory_type }} · 重要度 {{ candidate.importance }} · {{ candidate.saved ? '已保存' : '未保存' }}</text>
              <text>{{ candidate.content }}</text>
              <text>{{ candidate.reason }}</text>
            </view>
          </view>
          <text v-else>本轮未生成记忆候选。</text>
        </view>
      </view>
    </view>

    <PetWidget
      v-if="petEnabled"
      :class="petClass"
      :pet-avatar="petAvatarUrl"
      :pet-name="character.pet.pet_name"
      :status="character.pet.pet_status"
      :action="petAction"
      :intimacy-level="character.intimacy_level"
    />

    <view class="composer">
      <input
        v-model="draft"
        placeholder="对他说点什么..."
        confirm-type="send"
        @confirm="sendMessage"
      />
      <button @click="sendMessage">发送</button>
    </view>
  </GradientPage>
</template>

<script setup>
import { computed, nextTick, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { api, resolveAssetUrl } from '../../api'
import GradientPage from '../../components/GradientPage.vue'
import PetWidget from '../../components/PetWidget.vue'

const character = ref(null)
const characterSettings = ref(null)
const draft = ref('')
const petAction = ref('idle')
const scrollTarget = ref('')
const messages = ref([])
const sessionId = ref('')
const showDebug = ref(false)
const promptDebug = ref(null)
const providerDebug = ref(null)
const memoryDebug = ref(null)
const safetyDebug = ref(null)
const avatarUrl = computed(() => resolveAssetUrl(character.value?.avatar))
const petAvatarUrl = computed(() =>
  resolveAssetUrl(
    character.value?.active_pet_asset?.image_url || character.value?.pet?.pet_avatar
  )
)
const petEnabled = computed(() => characterSettings.value?.pet_enabled !== false)
const petClass = computed(() => [
  'floating-pet',
  `pet-${characterSettings.value?.pet_position || 'bottom_right'}`,
])
const usesCharacterProfile = computed(
  () => promptDebug.value?.uses_character_profile ?? Boolean(character.value?.profile)
)
const providerStatusText = computed(() => {
  if (!providerDebug.value) {
    return ''
  }
  const providerMap = {
    mock: 'Mock 回复',
    openai_compatible: 'OpenAI-compatible 回复',
    custom_http: 'Custom HTTP 回复',
  }
  const label = providerMap[providerDebug.value.provider] || '模型回复'
  return providerDebug.value.fallback ? `${label} · 已回退` : label
})
const providerModeNote = computed(() => {
  if (!providerDebug.value) {
    return ''
  }
  if (providerDebug.value.fallback) {
    return '真实模型不可用，当前已回退 mock。'
  }
  if (providerDebug.value.provider === 'mock') {
    return '当前为 MockLLMProvider 测试回复，不代表真实模型理解。'
  }
  if (providerDebug.value.api_key_configured) {
    return '已配置 API Key，本轮尝试使用真实模型服务。'
  }
  return '未配置 API Key 时不会调用真实模型。'
})
const retrievalScopeText = computed(() => {
  const scope = promptDebug.value?.retrieval_scope || 'none'
  const scopeMap = {
    character_bound: '当前角色知识库',
    fallback_by_character_name: '按角色名兜底检索',
    none: '未命中知识库',
  }
  return scopeMap[scope] || scope
})
const safetyCategoriesText = computed(() => {
  const categories = safetyDebug.value?.matched_categories || []
  return categories.length ? categories.join(', ') : '本轮未触发安全分类'
})

onLoad(async ({ character_id, session_id }) => {
  character.value = await api.getCharacter(character_id)
  characterSettings.value = await api.getCharacterSettings(character_id)
  sessionId.value = session_id || ''
  if (sessionId.value) {
    await loadHistory(sessionId.value)
  } else {
    messages.value = [
      {
        id: 'msg-initial',
        role: 'assistant',
        content: character.value.last_message,
      },
    ]
  }
})

async function sendMessage() {
  const content = draft.value.trim()
  if (!content) {
    return
  }

  const userMessageId = `msg-user-${Date.now()}`
  messages.value.push({
    id: userMessageId,
    role: 'user',
    content,
  })
  draft.value = ''
  await scrollToLatest(userMessageId)

  const response = await api.chat({
    character_id: character.value.character_id,
    ...(sessionId.value ? { session_id: sessionId.value } : {}),
    message: content,
  })

  sessionId.value = response.session_id
  promptDebug.value = response.prompt_debug
  providerDebug.value = response.provider_debug
  memoryDebug.value = response.memory_debug
  safetyDebug.value = response.safety_debug
  if (response.safety_debug?.matched_categories?.length) {
    uni.showToast({
      title: '已启用安全边界提示',
      icon: 'none',
    })
  }
  if ((response.memory_debug?.created_count ?? 0) > 0) {
    uni.showToast({
      title: '角色记住了这件事',
      icon: 'none',
    })
  }
  petAction.value = response.pet_action
  character.value.pet.pet_status = response.pet_action
  const assistantMessageId = response.message_id
  messages.value.push({
    id: assistantMessageId,
    role: 'assistant',
    content: response.reply,
  })
  await scrollToLatest(assistantMessageId)
}

async function scrollToLatest(id) {
  await nextTick()
  scrollTarget.value = id
}

async function loadHistory(existingSessionId) {
  const history = await api.getChatMessages(existingSessionId)
  messages.value = history.map((message) => ({
    id: message.message_id,
    role: message.role,
    content: message.content,
  }))
  const lastMessage = messages.value[messages.value.length - 1]
  if (lastMessage) {
    await scrollToLatest(lastMessage.id)
  }
}
</script>

<style scoped lang="scss">
.chat-head {
  display: flex;
  gap: 18rpx;
  align-items: center;
  padding: 18rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
}

.avatar {
  width: 92rpx;
  height: 92rpx;
  border-radius: 8px;
}

.chat-head text {
  display: block;
}

.name {
  font-size: 32rpx;
  font-weight: 700;
}

.persona {
  margin-top: 8rpx;
  color: rgba(248, 247, 255, 0.74);
  font-size: 24rpx;
}

.message-list {
  height: calc(100vh - 500rpx);
  margin-top: 20rpx;
  padding-right: 4rpx;
}

.provider-status {
  margin-top: 14rpx;
  padding: 14rpx 18rpx;
  border: 1rpx solid rgba(126, 231, 246, 0.26);
  border-radius: 8px;
  background: rgba(126, 231, 246, 0.12);
  color: #7ee7f6;
  font-size: 24rpx;
}

.provider-status text {
  display: block;
}

.provider-note {
  margin-top: 6rpx;
  color: rgba(248, 247, 255, 0.72);
  font-size: 22rpx;
  line-height: 1.5;
}

.message {
  max-width: 78%;
  margin-bottom: 18rpx;
  padding: 18rpx 20rpx;
  border-radius: 8px;
  font-size: 28rpx;
  line-height: 1.6;
}

.assistant {
  background: rgba(255, 255, 255, 0.12);
}

.user {
  margin-left: auto;
  color: #1b1036;
  background: linear-gradient(135deg, #ffd166, #ff8db4);
}

.floating-pet {
  position: fixed;
  bottom: 150rpx;
  z-index: 5;
}

.pet-bottom_right {
  right: 28rpx;
}

.pet-bottom_left {
  left: 28rpx;
}

.pet-floating {
  right: 50%;
  transform: translateX(50%);
}

.debug-panel {
  margin-top: 18rpx;
}

.debug-toggle {
  min-height: 68rpx;
  color: #f8f7ff;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.12);
  font-size: 24rpx;
}

.debug-content {
  display: grid;
  gap: 14rpx;
  margin-top: 12rpx;
  padding: 18rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
}

.debug-row {
  display: flex;
  justify-content: space-between;
  gap: 16rpx;
  font-size: 24rpx;
}

.debug-copy text,
.debug-label {
  display: block;
}

.debug-label {
  color: rgba(248, 247, 255, 0.66);
  font-size: 22rpx;
}

.debug-copy text:last-child {
  margin-top: 8rpx;
  color: rgba(248, 247, 255, 0.82);
  font-size: 24rpx;
  line-height: 1.7;
}

.chunk-list {
  display: grid;
  gap: 10rpx;
  margin-top: 8rpx;
}

.chunk-item {
  padding: 14rpx;
  border-radius: 8px;
  background: rgba(19, 12, 47, 0.34);
}

.chunk-item text {
  display: block;
  color: rgba(248, 247, 255, 0.82);
  font-size: 22rpx;
  line-height: 1.6;
}

.chunk-item text:first-child {
  color: #7ee7f6;
}

.composer {
  position: fixed;
  right: 28rpx;
  bottom: 28rpx;
  left: 28rpx;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 130rpx;
  gap: 14rpx;
}

.composer input {
  height: 84rpx;
  padding: 0 20rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  background: rgba(19, 12, 47, 0.76);
  color: #f8f7ff;
}

.composer button {
  height: 84rpx;
  color: #1b1036;
  border-radius: 8px;
  font-weight: 700;
  background: linear-gradient(135deg, #ffd166, #7ee7f6);
}
</style>
