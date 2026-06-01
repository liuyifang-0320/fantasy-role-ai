<template>
  <GradientPage>
    <view class="page-head">
      <text class="title">记忆管理</text>
      <text class="subtitle">长期记忆会参与后续聊天 Prompt，可查看、新增、编辑或移除。</text>
    </view>

    <view class="add-panel">
      <text class="panel-title">新增记忆</text>
      <picker :range="memoryTypes" range-key="label" @change="changeMemoryType">
        <view class="picker">{{ currentMemoryType.label }}</view>
      </picker>
      <input v-model="newMemory" placeholder="添加一条长期记忆" />
      <view class="importance-row">
        <text>重要度 {{ newImportance }}</text>
        <slider
          :value="newImportance"
          min="1"
          max="5"
          step="1"
          activeColor="#7ee7f6"
          backgroundColor="rgba(255,255,255,0.18)"
          @change="changeNewImportance"
        />
      </view>
      <button @click="addMemory">添加</button>
    </view>

    <view v-for="section in sections" :key="section.key" class="memory-section">
      <view class="section-head">
        <text class="section-title">{{ section.label }}</text>
        <text class="section-count">{{ memories[section.key]?.length || 0 }} 条</text>
      </view>

      <view v-if="memories[section.key]?.length" class="memory-list">
        <view
          v-for="memory in memories[section.key]"
          :key="memory.memory_id"
          class="memory-card"
        >
          <template v-if="editingMemoryId === memory.memory_id">
            <input v-model="editingContent" class="edit-input" />
            <picker :range="memoryTypes" range-key="label" @change="changeEditingType">
              <view class="picker">{{ editingMemoryTypeLabel }}</view>
            </picker>
            <view class="importance-row">
              <text>重要度 {{ editingImportance }}</text>
              <slider
                :value="editingImportance"
                min="1"
                max="5"
                step="1"
                activeColor="#7ee7f6"
                backgroundColor="rgba(255,255,255,0.18)"
                @change="changeEditingImportance"
              />
            </view>
            <view class="card-actions">
              <button class="primary small" @click="saveEdit(memory.memory_id)">保存</button>
              <button class="ghost small" @click="cancelEdit">取消</button>
            </view>
          </template>
          <template v-else>
            <view class="memory-meta">
              <text>{{ typeLabel(memory.memory_type) }}</text>
              <text>重要度 {{ memory.importance }}</text>
            </view>
            <text class="memory-content">{{ memory.memory_content }}</text>
            <text class="memory-source">来源：{{ sourceLabel(memory.source) }}</text>
            <view class="card-actions">
              <button class="ghost small" @click="startEdit(memory)">编辑</button>
              <button class="danger small" @click="removeMemory(memory.memory_id)">移除记忆</button>
            </view>
          </template>
        </view>
      </view>
      <view v-else class="empty">暂无该类型记忆</view>
    </view>
  </GradientPage>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { api } from '../../api'
import GradientPage from '../../components/GradientPage.vue'

const characterId = ref('')
const memories = ref(emptyMemories())
const newMemory = ref('')
const newImportance = ref(3)
const memoryTypeIndex = ref(0)
const editingMemoryId = ref('')
const editingContent = ref('')
const editingMemoryType = ref('user_preference')
const editingImportance = ref(3)

const memoryTypes = [
  { label: '用户偏好', value: 'user_preference' },
  { label: '关系记忆', value: 'relationship' },
  { label: '剧情互动', value: 'story_interaction' },
  { label: '情绪状态', value: 'emotional_state' },
  { label: '自定义', value: 'custom' },
]
const sections = [
  { label: '用户偏好', key: 'user_preference_memory' },
  { label: '关系记忆', key: 'relationship_memory' },
  { label: '剧情互动', key: 'story_interaction_memory' },
  { label: '情绪状态', key: 'emotional_state_memory' },
  { label: '自定义', key: 'custom_memory' },
]
const currentMemoryType = computed(() => memoryTypes[memoryTypeIndex.value])
const editingMemoryTypeLabel = computed(() => typeLabel(editingMemoryType.value))

onLoad(async ({ character_id }) => {
  characterId.value = character_id
  await loadMemory()
})

function emptyMemories() {
  return {
    user_preference_memory: [],
    relationship_memory: [],
    story_interaction_memory: [],
    emotional_state_memory: [],
    custom_memory: [],
  }
}

async function loadMemory() {
  memories.value = {
    ...emptyMemories(),
    ...(await api.getMemory(characterId.value)),
  }
}

function changeMemoryType(event) {
  memoryTypeIndex.value = Number(event.detail.value)
}

function changeNewImportance(event) {
  newImportance.value = Number(event.detail.value)
}

function changeEditingType(event) {
  editingMemoryType.value = memoryTypes[Number(event.detail.value)].value
}

function changeEditingImportance(event) {
  editingImportance.value = Number(event.detail.value)
}

async function addMemory() {
  if (!newMemory.value.trim()) {
    return
  }
  await api.updateMemory({
    character_id: characterId.value,
    memory_content: newMemory.value.trim(),
    memory_type: currentMemoryType.value.value,
    importance: newImportance.value,
  })
  newMemory.value = ''
  newImportance.value = 3
  await loadMemory()
}

function startEdit(memory) {
  editingMemoryId.value = memory.memory_id
  editingContent.value = memory.memory_content
  editingMemoryType.value = memory.memory_type
  editingImportance.value = memory.importance
}

function cancelEdit() {
  editingMemoryId.value = ''
}

async function saveEdit(memoryId) {
  if (!editingContent.value.trim()) {
    return
  }
  const response = await api.patchMemory(memoryId, {
    memory_content: editingContent.value.trim(),
    memory_type: editingMemoryType.value,
    importance: editingImportance.value,
  })
  replaceMemory(response.memory)
  editingMemoryId.value = ''
  await loadMemory()
}

async function removeMemory(memoryId) {
  await api.deleteMemory(memoryId)
  await loadMemory()
}

function replaceMemory(updatedMemory) {
  if (!updatedMemory) {
    return
  }
  Object.keys(memories.value).forEach((key) => {
    memories.value[key] = memories.value[key].map((memory) =>
      memory.memory_id === updatedMemory.memory_id ? updatedMemory : memory,
    )
  })
}

function typeLabel(memoryType) {
  return memoryTypes.find((type) => type.value === memoryType)?.label || memoryType
}

function sourceLabel(source) {
  const sourceMap = {
    chat_auto: '聊天自动提取',
    user_manual: '用户手动添加',
    system_mock: '系统初始 mock',
  }
  return sourceMap[source] || source
}
</script>

<style scoped lang="scss">
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
  line-height: 1.6;
}

.add-panel,
.memory-card,
.empty {
  padding: 22rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
}

.add-panel {
  display: grid;
  gap: 14rpx;
  margin-top: 24rpx;
}

.panel-title,
.section-title {
  font-size: 28rpx;
  font-weight: 700;
}

.picker,
.add-panel input,
.edit-input {
  height: 76rpx;
  padding: 0 16rpx;
  border-radius: 8px;
  border: 1rpx solid rgba(255, 255, 255, 0.12);
  background: rgba(19, 12, 47, 0.52);
  line-height: 76rpx;
}

.importance-row {
  display: grid;
  gap: 6rpx;
  color: rgba(248, 247, 255, 0.8);
  font-size: 24rpx;
}

.memory-section {
  margin-top: 24rpx;
}

.section-head {
  display: flex;
  justify-content: space-between;
  gap: 16rpx;
  margin-bottom: 14rpx;
}

.section-count,
.memory-source,
.empty {
  color: rgba(248, 247, 255, 0.68);
  font-size: 24rpx;
}

.memory-list {
  display: grid;
  gap: 14rpx;
}

.memory-card {
  display: grid;
  gap: 12rpx;
}

.memory-meta {
  display: flex;
  justify-content: space-between;
  gap: 12rpx;
  color: #7ee7f6;
  font-size: 22rpx;
}

.memory-content {
  color: rgba(248, 247, 255, 0.9);
  font-size: 26rpx;
  line-height: 1.6;
}

.card-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12rpx;
}

.primary,
.ghost,
.danger,
.small {
  border-radius: 8px;
}

.primary {
  color: #1b1036;
  font-weight: 700;
  background: linear-gradient(135deg, #ffd166, #7ee7f6);
}

.ghost {
  color: #f8f7ff;
  background: rgba(255, 255, 255, 0.12);
}

.danger {
  color: #ffd4e4;
  background: rgba(255, 141, 180, 0.18);
}

.small {
  min-height: 68rpx;
  font-size: 24rpx;
}
</style>
